"""FastAPI application entry point."""

from __future__ import annotations

import datetime as _dt
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import func, select

from app import __version__
from app.cache import TTLCache
from app.config import settings
from app.database import SessionLocal, init_db
from app.errors import register_error_handlers
from app.metrics import CACHE_SIZE, MODEL_READY, render_metrics
from app.ml.loader import ModelLoadError, load_scorer
from app.models import UrlCheck
from app.rate_limit import limiter
from app.routers import check, history, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("phish-detector")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = _dt.datetime.now(_dt.timezone.utc)
    app.state.cache = (
        TTLCache(ttl=settings.cache_ttl, maxsize=settings.cache_maxsize)
        if settings.enable_cache else None
    )

    await init_db()
    logger.info("database schema ready")
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
    yield
    logger.info("shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Real-time phishing URL detection for Thai government "
                "and educational websites.",
    version=__version__,
    lifespan=lifespan,
)

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
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method, request.url.path, response.status_code, elapsed,
    )
    return response


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


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "endpoints": [
            "POST /api/v1/check",
            "POST /api/v1/check/batch",
            "GET /api/v1/stats",
            "GET /api/v1/history",
            "GET /health",
            "GET /metrics",
        ],
    }
