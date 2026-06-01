"""TAXII 2.1 server (read-only) for the public phishing feed.

Implements the subset of the OASIS TAXII 2.1 spec needed for one-way ingest by
standard clients (e.g. the `taxii2-client` library, OpenCTI, MISP TAXII):

  GET /taxii2/                                          discovery
  GET /taxii2/{api_root}/                               api-root info
  GET /taxii2/{api_root}/collections/                   collection list
  GET /taxii2/{api_root}/collections/{id}/              collection metadata
  GET /taxii2/{api_root}/collections/{id}/objects/      STIX objects (envelope)
  GET /taxii2/{api_root}/collections/{id}/manifest/     object manifest

There is a single api-root (``feed``) exposing one read-only collection of
phishing-URL indicators. Writes (POST objects) are intentionally unsupported.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Label, UrlCheck
from app.stix import build_indicator, indicator_id_for

router = APIRouter(prefix="/taxii2")

# TAXII 2.1 media types.
TAXII_MEDIA_TYPE = "application/taxii+json;version=2.1"
STIX_MEDIA_TYPE = "application/stix+json;version=2.1"

API_ROOT = "feed"
COLLECTION_ID = "a1f5c0de-0000-4000-8000-000000000001"
COLLECTION_TITLE = "Thai phishing indicators"

DEFAULT_HOURS = 24
MAX_HOURS = 24 * 14
MAX_LIMIT = 2000


def _taxii_response(content: dict, status_code: int = 200) -> Response:
    """A JSON response carrying the required TAXII 2.1 media type."""
    import json

    return Response(
        content=json.dumps(content, default=str),
        media_type=TAXII_MEDIA_TYPE,
        status_code=status_code,
        headers={"Cache-Control": "public, max-age=60"},
    )


def _require_api_root(api_root: str) -> None:
    if api_root != API_ROOT:
        raise HTTPException(status_code=404, detail="unknown API root")


def _require_collection(api_root: str, collection_id: str) -> None:
    _require_api_root(api_root)
    if collection_id != COLLECTION_ID:
        raise HTTPException(status_code=404, detail="unknown collection")


async def _recent_rows(
    session: AsyncSession,
    hours: int,
    limit: int,
    added_after: dt.datetime | None,
) -> list[UrlCheck]:
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    if added_after is not None and added_after > since:
        since = added_after
    rows = (
        await session.execute(
            select(UrlCheck)
            .where(UrlCheck.label == Label.phishing)
            .where(UrlCheck.checked_at >= since)
            .order_by(UrlCheck.checked_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)


def _parse_added_after(value: str) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid added_after timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


@router.get("/", summary="TAXII 2.1 discovery")
async def discovery(request: Request) -> Response:
    base = str(request.base_url).rstrip("/")
    api_root_url = f"{base}/api/v1/taxii2/{API_ROOT}/"
    return _taxii_response({
        "title": "Thai Phishing Detector TAXII Server",
        "description": "Read-only TAXII 2.1 feed of high-confidence Thai phishing URLs.",
        "contact": "https://github.com/reenx8/security",
        "default": api_root_url,
        "api_roots": [api_root_url],
    })


@router.get("/{api_root}/", summary="TAXII 2.1 API root information")
async def api_root_info(api_root: str) -> Response:
    _require_api_root(api_root)
    return _taxii_response({
        "title": "Phishing feed API root",
        "description": "Single read-only collection of phishing-URL indicators.",
        "versions": [TAXII_MEDIA_TYPE],
        "max_content_length": 104857600,
    })


@router.get("/{api_root}/collections/", summary="List collections")
async def list_collections(api_root: str) -> Response:
    _require_api_root(api_root)
    return _taxii_response({"collections": [_collection_dict()]})


@router.get("/{api_root}/collections/{collection_id}/", summary="Collection metadata")
async def collection_info(api_root: str, collection_id: str) -> Response:
    _require_collection(api_root, collection_id)
    return _taxii_response(_collection_dict())


def _collection_dict() -> dict:
    return {
        "id": COLLECTION_ID,
        "title": COLLECTION_TITLE,
        "description": "Phishing URLs flagged with high confidence in the last 14 days.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_MEDIA_TYPE],
    }


@router.get(
    "/{api_root}/collections/{collection_id}/objects/",
    summary="Get STIX objects (TAXII envelope)",
)
async def get_objects(
    api_root: str,
    collection_id: str,
    hours: int = Query(default=DEFAULT_HOURS, ge=1, le=MAX_HOURS),
    limit: int = Query(default=500, ge=1, le=MAX_LIMIT),
    added_after: str = Query(default=""),
    session: AsyncSession = Depends(get_session),
) -> Response:
    _require_collection(api_root, collection_id)
    rows = await _recent_rows(session, hours, limit, _parse_added_after(added_after))
    return _taxii_response({
        "more": False,
        "objects": [build_indicator(r) for r in rows],
    })


@router.get(
    "/{api_root}/collections/{collection_id}/manifest/",
    summary="Object manifest",
)
async def get_manifest(
    api_root: str,
    collection_id: str,
    hours: int = Query(default=DEFAULT_HOURS, ge=1, le=MAX_HOURS),
    limit: int = Query(default=500, ge=1, le=MAX_LIMIT),
    added_after: str = Query(default=""),
    session: AsyncSession = Depends(get_session),
) -> Response:
    _require_collection(api_root, collection_id)
    rows = await _recent_rows(session, hours, limit, _parse_added_after(added_after))
    manifest = [
        {
            "id": indicator_id_for(r),
            "date_added": r.checked_at.isoformat().replace("+00:00", "Z"),
            "version": r.checked_at.isoformat().replace("+00:00", "Z"),
            "media_type": STIX_MEDIA_TYPE,
        }
        for r in rows
    ]
    return _taxii_response({"more": False, "objects": manifest})
