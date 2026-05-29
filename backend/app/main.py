"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import datetime as _dt
import logging
import time
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import func, select

from phish_features import FEATURE_SCHEMA_VERSION
from phish_features import __version__ as features_version

from app import __version__
from app.cache import build_cache
from app.config import settings
from app.database import SessionLocal, init_db
from app.errors import register_error_handlers
from app.metrics import CACHE_SIZE, MODEL_READY, render_metrics
from app.middleware import RequestContextMiddleware
from app.ml.loader import ModelLoadError, load_scorer
from app.feed_ingestion import FeedPoller
from app.models import DbWhitelistEntry, ExternalFeedSource, ExternalFeedSourceType, UrlCheck
from app.rate_limit import limiter
from app.routers import campaigns as campaigns_router
from app.routers import check, history, stats
from app.routers import admin as admin_router
from app.routers import domain as domain_router
from app.routers import feed as feed_router
from app.routers import feedback as feedback_router
from app.routers import impact as impact_router
from app.routers import learn as learn_router
from app.routers import line_bot as line_bot_router
from app.routers import watchlist as watchlist_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("phish-detector")


async def _seed_whitelist_from_json() -> None:
    """Migrate whitelist.json → DB on first startup (idempotent)."""
    import json, os
    path = settings.whitelist_path
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    entries = payload.get("entries", [])
    if not entries:
        return

    from sqlalchemy import select as _select
    async with SessionLocal() as session:
        existing = (
            await session.execute(_select(DbWhitelistEntry.domain))
        ).scalars().all()
        existing_set = set(existing)
        new_rows = [
            DbWhitelistEntry(
                domain=e["domain"],
                agency_name=e.get("agency_name", ""),
                category=e.get("category", "other"),
                added_by="seed",
                is_seeded=True,
            )
            for e in entries
            if e.get("domain") and e["domain"] not in existing_set
        ]
        if new_rows:
            session.add_all(new_rows)
            await session.commit()
            logger.info("whitelist seeded %d entries from JSON", len(new_rows))


async def _seed_external_feed_sources() -> None:
    """Insert default OpenPhish and PhishTank source rows if not present (idempotent)."""
    defaults = [
        {
            "name": "openphish",
            "source_type": ExternalFeedSourceType.openphish,
            "feed_url": settings.openphish_feed_url,
            "poll_interval_minutes": settings.external_feed_poll_interval,
        },
        {
            "name": "phishtank",
            "source_type": ExternalFeedSourceType.phishtank,
            "feed_url": "https://data.phishtank.com/data/{api_key}/online-valid.json",
            "api_key": settings.phishtank_api_key or None,
            "poll_interval_minutes": settings.external_feed_poll_interval,
        },
    ]
    async with SessionLocal() as session:
        for d in defaults:
            existing = (
                await session.execute(
                    select(ExternalFeedSource).where(ExternalFeedSource.name == d["name"])
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(ExternalFeedSource(**d))
        await session.commit()
    logger.info("external feed sources seeded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = _dt.datetime.now(_dt.timezone.utc)
    app.state.cache = build_cache(settings)

    # The core URL scorer does not need the database -- history, stats and
    # admin endpoints do. Tolerate a missing/unreachable DB at startup so
    # the app still serves /health and /check; DB-backed routes will fail
    # at request time with a clear error. This makes the service resilient
    # to managed-DB DNS hiccups (e.g. cross-region Render Postgres) and
    # lets users run the detector even before provisioning a DB.
    app.state.db_ready = False
    try:
        await init_db()
        await _seed_whitelist_from_json()
        app.state.db_ready = True
        logger.info("database schema ready")
    except Exception as exc:  # broad: any DB driver / network error
        logger.warning(
            "database NOT ready (%s) -- /check and /health still work, "
            "but /history /stats /admin will return 503",
            exc,
        )

    try:
        app.state.scorer = load_scorer()
        MODEL_READY.set(1)
        meta = app.state.scorer.features_meta
        logger.info(
            "model loaded (schema=%s, trained=%s, test_f1=%s)",
            meta.get("schema_version"),
            meta.get("trained_at"),
            meta.get("metrics", {}).get("test_f1"),
        )
    except ModelLoadError as exc:
        app.state.scorer = None
        MODEL_READY.set(0)
        logger.warning("model NOT loaded: %s -- /check will return 503", exc)

    app.state.feed_task = None
    if settings.external_feeds_enabled and app.state.db_ready:
        try:
            await _seed_external_feed_sources()
            poller = FeedPoller(app.state)
            app.state.feed_task = asyncio.create_task(poller.run_forever())
        except Exception as exc:  # noqa: BLE001
            logger.warning("feed poller failed to start: %s", exc)

    app.state.feedback_task = None
    if settings.feedback_retrain_enabled and app.state.db_ready:
        async def _feedback_retrain_loop() -> None:
            from functools import partial

            from ml_pipeline.feedback_retrain import run as _run_retrain
            while True:
                await asyncio.sleep(settings.feedback_retrain_interval_hours * 3600)
                try:
                    ok = await asyncio.get_event_loop().run_in_executor(
                        None,
                        partial(
                            _run_retrain,
                            min_rows=settings.feedback_accumulation_threshold,
                            enforce_gate=settings.feedback_promote_requires_gate,
                        ),
                    )
                    # Hot-swap the freshly promoted model without a restart.
                    if ok:
                        try:
                            app.state.scorer = load_scorer()
                            logger.info("scorer hot-reloaded after retrain")
                        except Exception as exc:  # noqa: BLE001 - keep old model
                            logger.error(
                                "scorer reload failed (%s) -- keeping previous "
                                "model", exc,
                            )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("feedback retrain failed: %s", exc)
        app.state.feedback_task = asyncio.create_task(_feedback_retrain_loop())

    yield
    if app.state.feed_task:
        app.state.feed_task.cancel()
        with suppress(asyncio.CancelledError):
            await app.state.feed_task
    if app.state.feedback_task:
        app.state.feedback_task.cancel()
        with suppress(asyncio.CancelledError):
            await app.state.feedback_task
    logger.info("shutting down")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Real-time phishing URL detection for Thai government and "
        "educational websites.\n\n"
        "**Disclaimer / ข้อตกลงในการใช้ซอฟต์แวร์:** ซอฟต์แวร์นี้พัฒนาขึ้นภายใต้ "
        "การแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์แห่งประเทศไทย (NSC) สนับสนุนโดย "
        "สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ (สวทช.) "
        "เพื่อการศึกษาและการเรียนรู้ ไม่ใช่เพื่อวัตถุประสงค์เชิงพาณิชย์ "
        "สวทช. ไม่รับรองความถูกต้องและไม่รับผิดชอบต่อความเสียหายที่เกิด "
        "จากการใช้งาน  เผยแพร่ภายใต้ Apache License 2.0 — ดูฉบับเต็มได้ที่ "
        "endpoint `/api/v1/disclaimer`."
    ),
    version=__version__,
    lifespan=lifespan,
)


@app.get("/api/v1/disclaimer", tags=["meta"], include_in_schema=True)
async def disclaimer() -> dict:
    """ข้อตกลงในการใช้ซอฟต์แวร์ตามข้อกำหนด NSC (booklet หน้า 44)."""
    return {
        "thai": (
            "ซอฟต์แวร์นี้เป็นผลงานที่พัฒนาขึ้นภายใต้โครงการ \"ระบบตรวจจับเว็บไซต์"
            "ฟิชชิงสำหรับหน่วยงานราชการและสถาบันการศึกษาไทย ด้วยการเรียนรู้ของ"
            "เครื่องและกฎอ้างอิงที่โปร่งใส\" ซึ่งสนับสนุนโดยสำนักงานพัฒนา"
            "วิทยาศาสตร์และเทคโนโลยีแห่งชาติ (สวทช.) ในการแข่งขันพัฒนาโปรแกรม"
            "คอมพิวเตอร์แห่งประเทศไทย ครั้งที่ 28 (NSC 2026) โดยมีวัตถุประสงค์"
            "เพื่อส่งเสริมให้นักเรียนและนักศึกษาได้เรียนรู้และฝึกทักษะในการ"
            "พัฒนาซอฟต์แวร์ สวทช. ไม่มีหน้าที่ในการดูแล บำรุงรักษา อบรมการ"
            "ใช้งาน หรือพัฒนาประสิทธิภาพซอฟต์แวร์ ตลอดจนไม่รับประกันความ"
            "เสียหายต่าง ๆ อันเกิดจากการใช้งาน เผยแพร่ภายใต้ Apache License 2.0"
        ),
        "english": (
            "This software is a work developed under the project "
            "\"Thai Public-Sector Phishing URL Detection System using "
            "Machine Learning with a Transparent Rules Engine\", supported "
            "by the National Science and Technology Development Agency "
            "(NSTDA) in the 28th National Software Contest (NSC 2026), "
            "in order to encourage pupils and students to learn and "
            "practice their skills in developing software. NSTDA shall "
            "not be responsible for taking care, maintaining, training, "
            "or developing the efficiency of this software, and shall "
            "not be liable for any damages arising out of its use. "
            "Distributed under the Apache License 2.0."
        ),
        "license": "Apache-2.0",
        "license_url": (
            "https://github.com/reenx8/security/blob/main/LICENSE"
        ),
        "contest": "NSC 2026 (The 28th National Software Contest)",
    }

# --- middleware (added last = outermost) ---
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware, log_format=settings.log_format)


# --- error handlers ---
register_error_handlers(app)


@app.exception_handler(RateLimitExceeded)
async def _rate_limited(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": f"Rate limit exceeded ({exc.detail}).",
            "code": "RATE_LIMITED",
        },
    )


# --- routes ---
app.include_router(check.router, prefix="/api/v1", tags=["check"])
app.include_router(stats.router, prefix="/api/v1", tags=["stats"])
app.include_router(history.router, prefix="/api/v1", tags=["history"])
app.include_router(admin_router.router, prefix="/api/v1", tags=["admin"])
app.include_router(feedback_router.router, prefix="/api/v1", tags=["feedback"])
app.include_router(watchlist_router.router, prefix="/api/v1", tags=["watchlist"])
app.include_router(campaigns_router.router, prefix="/api/v1", tags=["campaigns"])
app.include_router(domain_router.router, prefix="/api/v1", tags=["domain"])
app.include_router(impact_router.router, prefix="/api/v1", tags=["impact"])
app.include_router(learn_router.router, prefix="/api/v1", tags=["learn"])
if settings.enable_public_feed:
    app.include_router(feed_router.router, prefix="/api/v1", tags=["feed"])
if settings.line_channel_token or settings.line_channel_secret:
    app.include_router(line_bot_router.router, prefix="/api/v1", tags=["line"])


@app.get("/health", tags=["meta"])
async def health(request: Request) -> dict:
    scorer = getattr(request.app.state, "scorer", None)
    started = getattr(request.app.state, "started_at", None)
    uptime = (
        (_dt.datetime.now(_dt.timezone.utc) - started).total_seconds()
        if started else None
    )
    cache = getattr(request.app.state, "cache", None)

    # Lightweight DB check (counts rows).
    db_ok, db_rows = True, None
    try:
        async with SessionLocal() as session:
            db_rows = (
                await session.execute(select(func.count()).select_from(UrlCheck))
            ).scalar_one()
    except Exception as exc:  # noqa: BLE001
        db_ok = False
        logger.warning("health: DB check failed: %s", exc)

    meta = scorer.features_meta if scorer else {}
    return {
        "status": "ok" if (scorer and db_ok) else "degraded",
        "model_ready": scorer is not None,
        "db_ok": db_ok,
        "version": __version__,
        "schema_version": meta.get("schema_version"),
        "model_trained_at": meta.get("trained_at"),
        "model_metrics": meta.get("metrics", {}),
        "checks_in_db": db_rows,
        "cache_size": len(cache) if cache is not None else None,
        "uptime_seconds": round(uptime, 1) if uptime is not None else None,
    }


@app.get("/metrics", tags=["meta"], include_in_schema=False)
async def metrics_endpoint() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


@app.get("/version", tags=["meta"])
async def version() -> dict:
    """Triple of versions that together identify the running build."""
    return {
        "backend": __version__,
        "phish_features": features_version,
        "schema": FEATURE_SCHEMA_VERSION,
    }


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "schema_version": FEATURE_SCHEMA_VERSION,
        "docs": "/docs",
        "endpoints": [
            "POST /api/v1/check",
            "POST /api/v1/check/batch",
            "GET  /api/v1/stats",
            "GET  /api/v1/history",
            "GET  /api/v1/admin/whitelist",
            "POST /api/v1/admin/whitelist",
            "DELETE /api/v1/admin/whitelist/{domain}",
            "POST /api/v1/feedback",
            "GET  /api/v1/feedback",
            "GET  /api/v1/feedback/export",
            "GET  /api/v1/watchlist",
            "POST /api/v1/watchlist",
            "DELETE /api/v1/watchlist/{brand}",
            "GET  /api/v1/watchlist/deliveries",
            "GET  /api/v1/campaigns",
            "GET  /api/v1/domain/{host}/history",
            "GET  /api/v1/feed.json",
            "GET  /api/v1/feed.csv",
            "GET  /api/v1/feed.stix",
            "GET  /api/v1/impact",
            "GET  /api/v1/learn",
            "GET  /api/v1/learn/{card_id}",
            "GET  /health",
            "GET  /version",
            "GET  /metrics",
        ],
    }
