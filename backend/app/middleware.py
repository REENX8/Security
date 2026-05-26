"""Cross-cutting HTTP middleware.

Adds three things on top of the default Starlette pipeline:

1. **Request-ID propagation**: every request gets an ``X-Request-ID``
   header on the way out (preserved if the client already set one). The
   id is also bound to the access log line so support requests can quote
   it instead of trying to describe what happened.
2. **Security response headers**: the small set every public API should
   send anyway. They cost nothing and remove easy attack surfaces (MIME
   sniff, click-jack, referrer leaks).
3. **Structured JSON access log** option: ``LOG_FORMAT=json`` emits one
   line per request as compact JSON instead of the human-readable text
   format. Easier to scrape with Loki / Cloud Logging / Datadog.
"""

from __future__ import annotations

import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "interest-cohort=()",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Stamp every request with a stable id + security headers + access log."""

    def __init__(self, app, *, log_format: str = "text") -> None:
        super().__init__(app)
        self._json_logs = log_format.lower() == "json"
        self._log = logging.getLogger("phish-detector.access")

    async def dispatch(self, request: Request, call_next):
        req_id = (
            request.headers.get(REQUEST_ID_HEADER)
            or uuid.uuid4().hex[:16]
        )
        # Make the id reachable to handlers via ``request.state``.
        request.state.request_id = req_id

        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:  # noqa: BLE001 -- re-raised after logging
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._emit(request, status=500, elapsed_ms=elapsed_ms,
                       req_id=req_id, exc=True)
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers[REQUEST_ID_HEADER] = req_id
        for k, v in _SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        self._emit(request, status=response.status_code,
                   elapsed_ms=elapsed_ms, req_id=req_id)
        return response

    def _emit(
        self,
        request: Request,
        *,
        status: int,
        elapsed_ms: float,
        req_id: str,
        exc: bool = False,
    ) -> None:
        if self._json_logs:
            line = json.dumps(
                {
                    "ts": time.time(),
                    "level": "ERROR" if exc else "INFO",
                    "request_id": req_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "client": request.client.host if request.client else None,
                },
                separators=(",", ":"),
            )
            (self._log.error if exc else self._log.info)(line)
        else:
            self._log.log(
                logging.ERROR if exc else logging.INFO,
                "%s %s -> %s (%.1f ms) [%s]",
                request.method, request.url.path, status, elapsed_ms, req_id,
            )
