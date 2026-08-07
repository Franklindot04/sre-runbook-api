from contextlib import asynccontextmanager

from fastapi import FastAPI

from sre_runbook_api import models  # noqa: F401
from sre_runbook_api.api.routes import router
from sre_runbook_api.config import get_settings

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
