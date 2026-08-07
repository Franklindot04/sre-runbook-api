from fastapi import FastAPI

from sre_runbook_api.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API for centralized SRE runbooks, service alerts, "
        "operational metadata, remediation references, and incident context."
    ),
)


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
def readiness() -> dict[str, str]:
    return {
        "status": "ready",
        "environment": settings.environment,
    }
