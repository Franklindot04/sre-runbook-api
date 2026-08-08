from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from sre_runbook_api.api.pagination import Pagination
from sre_runbook_api.database import get_db
from sre_runbook_api.models import Alert, Incident, Runbook, Service
from sre_runbook_api.schemas import (
    AlertCreate,
    AlertRead,
    IncidentCreate,
    IncidentRead,
    RunbookCreate,
    RunbookRead,
    ServiceCreate,
    ServiceRead,
)
from sre_runbook_api.security import require_api_key

router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(require_api_key)],
)


@router.post(
    "/services",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
    tags=["services"],
)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
) -> Service:
    existing = db.scalar(
        select(Service).where(
            (Service.name == payload.name) | (Service.slug == payload.slug)
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A service with this name or slug already exists.",
        )

    service = Service(**payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get(
    "/services",
    response_model=list[ServiceRead],
    tags=["services"],
)
def list_services(
    search: str | None = Query(default=None, max_length=100),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
) -> list[Service]:
    statement = select(Service).order_by(Service.name, Service.id)

    if search:
        pattern = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(Service.name).like(pattern),
                func.lower(Service.slug).like(pattern),
            )
        )

    statement = statement.offset(pagination.offset).limit(pagination.limit)
    return list(db.scalars(statement).all())


@router.post(
    "/runbooks",
    response_model=RunbookRead,
    status_code=status.HTTP_201_CREATED,
    tags=["runbooks"],
)
def create_runbook(
    payload: RunbookCreate,
    db: Session = Depends(get_db),
) -> Runbook:
    service = db.get(Service, payload.service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )

    runbook = Runbook(**payload.model_dump())
    db.add(runbook)
    db.commit()
    db.refresh(runbook)
    return runbook


@router.get(
    "/runbooks",
    response_model=list[RunbookRead],
    tags=["runbooks"],
)
def list_runbooks(
    service_id: int | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
) -> list[Runbook]:
    statement = select(Runbook).order_by(
        Runbook.created_at.desc(),
        Runbook.id.desc(),
    )

    if service_id is not None:
        statement = statement.where(Runbook.service_id == service_id)

    if search:
        pattern = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(Runbook.title).like(pattern),
                func.lower(Runbook.slug).like(pattern),
            )
        )

    statement = statement.offset(pagination.offset).limit(pagination.limit)
    return list(db.scalars(statement).all())


@router.get(
    "/runbooks/{runbook_id}",
    response_model=RunbookRead,
    tags=["runbooks"],
)
def get_runbook(
    runbook_id: int,
    db: Session = Depends(get_db),
) -> Runbook:
    runbook = db.get(Runbook, runbook_id)

    if runbook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Runbook not found.",
        )

    return runbook


@router.post(
    "/alerts",
    response_model=AlertRead,
    status_code=status.HTTP_201_CREATED,
    tags=["alerts"],
)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
) -> Alert:
    service = db.get(Service, payload.service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )

    existing = db.scalar(
        select(Alert).where(Alert.fingerprint == payload.fingerprint)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An alert with this fingerprint already exists.",
        )

    alert = Alert(**payload.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get(
    "/alerts",
    response_model=list[AlertRead],
    tags=["alerts"],
)
def list_alerts(
    service_id: int | None = Query(default=None),
    severity: str | None = Query(default=None, max_length=20),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
) -> list[Alert]:
    statement = select(Alert).order_by(
        Alert.created_at.desc(),
        Alert.id.desc(),
    )

    if service_id is not None:
        statement = statement.where(Alert.service_id == service_id)

    if severity is not None:
        statement = statement.where(Alert.severity == severity)

    statement = statement.offset(pagination.offset).limit(pagination.limit)
    return list(db.scalars(statement).all())


@router.post(
    "/incidents",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["incidents"],
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
) -> Incident:
    service = db.get(Service, payload.service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )

    if payload.alert_id is not None:
        alert = db.get(Alert, payload.alert_id)
        if alert is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found.",
            )

    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.get(
    "/incidents",
    response_model=list[IncidentRead],
    tags=["incidents"],
)
def list_incidents(
    service_id: int | None = Query(default=None),
    incident_status: str | None = Query(default=None, alias="status"),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
) -> list[Incident]:
    statement = select(Incident).order_by(
        Incident.started_at.desc(),
        Incident.id.desc(),
    )

    if service_id is not None:
        statement = statement.where(Incident.service_id == service_id)

    if incident_status is not None:
        statement = statement.where(Incident.status == incident_status)

    statement = statement.offset(pagination.offset).limit(pagination.limit)
    return list(db.scalars(statement).all())
