"""FastAPI application entry point."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import __version__
from app.config import settings
from app.database import init_db
from app.errors import register_error_handlers
from app.ml.loader import ModelLoadError, load_scorer
from app.rate_limit import limiter
from app.routers import check, history, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("phish-detector")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("database schema ready")
    try:
        app.state.scorer = load_scorer()
        meta = app.state.scorer.features_meta
        logger.info(
            "model loaded (schema=%s, trained=%s, test_f1=%s)",
            meta.get("schema_version"),
            meta.get("trained_at"),
            meta.get("metrics", {}).get("test_f1"),
        )
    except ModelLoadError as exc:
        app.state.scorer = None
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
    return {
        "status": "ok",
        "model_ready": scorer is not None,
        "version": __version__,
        "schema_version": (
            scorer.features_meta.get("schema_version") if scorer else None
        ),
    }


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "endpoints": [
            "POST /api/v1/check",
            "GET /api/v1/stats",
            "GET /api/v1/history",
        ],
    }
