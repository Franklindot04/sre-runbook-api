from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from sre_runbook_api import models  # noqa: F401
from sre_runbook_api.api.routes import router
from sre_runbook_api.config import get_settings
from sre_runbook_api.errors import (
    http_exception_handler,
    validation_exception_handler,
)
from sre_runbook_api.logging_middleware import RequestLoggingMiddleware
from sre_runbook_api.middleware import CorrelationIdMiddleware

settings = get_settings()


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
    return {
        "status": "ready",
        "environment": settings.environment,
    }
