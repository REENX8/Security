"""Structured error handling.

Every error response has the shape ``{"error": "...", "code": "..."}``.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Application-level error carrying an HTTP status + machine code."""

    def __init__(self, message: str, code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ModelNotLoadedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Detection model is not loaded. Run the ML pipeline first.",
            code="MODEL_NOT_LOADED",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def _json(status_code: int, message: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": message, "code": code}
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return _json(exc.status_code, exc.message, exc.code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        detail = exc.errors()[0].get("msg", "Invalid request") if exc.errors() \
            else "Invalid request"
        return _json(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail, "VALIDATION_ERROR"
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            429: "RATE_LIMITED",
        }.get(exc.status_code, "HTTP_ERROR")
        return _json(exc.status_code, str(exc.detail), code)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        return _json(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred.",
            "INTERNAL_ERROR",
        )
