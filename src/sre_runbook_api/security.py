import json
import logging
import secrets

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from sre_runbook_api.config import get_settings

settings = get_settings()
logger = logging.getLogger("sre_runbook_api.auth")

api_key_header = APIKeyHeader(
    name=settings.api_key_header,
    scheme_name="ApiKeyAuth",
    description="API key required for protected operational endpoints.",
    auto_error=False,
)


def _log_auth_event(
    request: Request,
    *,
    event: str,
    reason: str,
) -> None:
    record = {
        "event": event,
        "method": request.method,
        "path": request.url.path,
        "reason": reason,
        "correlation_id": getattr(request.state, "correlation_id", None),
    }

    logger.info(json.dumps(record, separators=(",", ":")))


def require_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> str:
    if api_key is None:
        _log_auth_event(
            request,
            event="auth_failure",
            reason="missing_api_key",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    expected_key = settings.api_key.get_secret_value()

    if not secrets.compare_digest(api_key, expected_key):
        _log_auth_event(
            request,
            event="auth_failure",
            reason="invalid_api_key",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    _log_auth_event(
        request,
        event="auth_success",
        reason="valid_api_key",
    )

    return api_key