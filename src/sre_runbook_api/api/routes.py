from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from sre_runbook_api.database import get_db
from sre_runbook_api.models import Runbook, Service
from sre_runbook_api.schemas import (
    RunbookCreate,
    RunbookRead,
    ServiceCreate,
    ServiceRead,
)

router = APIRouter(prefix="/api/v1")


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
    db: Session = Depends(get_db),
) -> list[Service]:
    return list(db.scalars(select(Service).order_by(Service.name)).all())


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
    db: Session = Depends(get_db),
) -> list[Runbook]:
    statement = select(Runbook).order_by(Runbook.created_at.desc())

    if service_id is not None:
        statement = statement.where(Runbook.service_id == service_id)

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
