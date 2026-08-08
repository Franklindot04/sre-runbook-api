from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _error_response(
    request: Request,
    *,
    status_code: int,
    error_code: str,
    detail: Any,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    content = {
        "detail": detail,
        "error_code": error_code,
        "correlation_id": _correlation_id(request),
    }

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return _error_response(
        request,
        status_code=exc.status_code,
        error_code="http_error",
        detail=exc.detail,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _error_response(
        request,
        status_code=422,
        error_code="validation_error",
        detail=exc.errors(),
    )
