from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(
        min_length=2,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = None
    owner_team: str | None = Field(default=None, max_length=120)


class ServiceRead(ServiceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class RunbookCreate(BaseModel):
    service_id: int
    title: str = Field(min_length=3, max_length=200)
    slug: str = Field(
        min_length=3,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    summary: str = Field(min_length=10, max_length=500)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    content: str = Field(min_length=20)


class RunbookRead(RunbookCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime


class AlertCreate(BaseModel):
    service_id: int
    fingerprint: str = Field(min_length=3, max_length=200)
    name: str = Field(min_length=3, max_length=200)
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    source: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=10)


class AlertRead(AlertCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class IncidentCreate(BaseModel):
    service_id: int
    alert_id: int | None = None
    title: str = Field(min_length=3, max_length=200)
    summary: str = Field(min_length=10, max_length=500)
    severity: str = Field(pattern="^(low|medium|high|critical)$")


class IncidentRead(IncidentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: datetime
    resolved_at: datetime | None
