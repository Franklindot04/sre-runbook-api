import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from sre_runbook_api import models  # noqa: F401
from sre_runbook_api.api.routes import router
from sre_runbook_api.config import get_settings
from sre_runbook_api.database import engine
from sre_runbook_api.errors import (
    http_exception_handler,
    validation_exception_handler,
)
from sre_runbook_api.logging_middleware import RequestLoggingMiddleware
from sre_runbook_api.middleware import CorrelationIdMiddleware

settings = get_settings()
access_logger = logging.getLogger("sre_runbook_api.access")
access_logger.setLevel(getattr(logging, settings.log_level))


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API for centralized SRE runbooks, service alerts, "
        "operational metadata, remediation references, and incident context."
    ),
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.include_router(router)


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logging.getLogger("sre_runbook_api.health").warning(
            "database readiness check failed"
        )
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from None

    return {
        "status": "ready",
        "environment": settings.environment,
    }
