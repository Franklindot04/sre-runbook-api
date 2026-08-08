import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from sre_runbook_api.config import get_settings

settings = get_settings()

api_key_header = APIKeyHeader(
    name=settings.api_key_header,
    scheme_name="ApiKeyAuth",
    description="API key required for protected operational endpoints.",
)


def require_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    return api_key
