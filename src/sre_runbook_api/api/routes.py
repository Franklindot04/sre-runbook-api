from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from sre_runbook_api.api.pagination import Pagination
from sre_runbook_api.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from sre_runbook_api.database import get_db
from sre_runbook_api.models import Alert, Incident, Runbook, Service, User
from sre_runbook_api.schemas import (
    AlertCreate,
    AlertRead,
    IncidentCreate,
    IncidentRead,
    LoginRequest,
    RunbookCreate,
    RunbookRead,
    ServiceCreate,
    ServiceRead,
    TokenRead,
    UserRead,
    UserRegister,
)
from sre_runbook_api.security import require_api_key

router = APIRouter(prefix="/api/v1")

protected_router = APIRouter(
    dependencies=[
        Depends(require_api_key),
        Depends(get_current_user),
    ],
)


def get_owned_service(
    service_id: int,
    current_user: User,
    db: Session,
) -> Service:
    service = db.scalar(
        select(Service).where(
            Service.id == service_id,
            Service.owner_id == current_user.id,
        )
    )

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )

    return service


@protected_router.post(
    "/services",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
    tags=["services"],
)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    service = Service(
        **payload.model_dump(),
        owner_id=current_user.id,
    )
    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@protected_router.get(
    "/services",
    response_model=list[ServiceRead],
    tags=["services"],
)
def list_services(
    response: Response,
    search: str | None = Query(default=None, max_length=100),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Service]:
    statement = (
        select(Service)
        .where(Service.owner_id == current_user.id)
        .order_by(Service.name, Service.id)
    )

    if search:
        pattern = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(Service.name).like(pattern),
                func.lower(Service.slug).like(pattern),
            )
        )

    total = db.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    response.headers["X-Total-Count"] = str(total)

    statement = statement.offset(pagination.offset).limit(pagination.limit)

    return list(db.scalars(statement).all())


@protected_router.post(
    "/runbooks",
    response_model=RunbookRead,
    status_code=status.HTTP_201_CREATED,
    tags=["runbooks"],
)
def create_runbook(
    payload: RunbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Runbook:
    get_owned_service(payload.service_id, current_user, db)

    runbook = Runbook(**payload.model_dump())
    db.add(runbook)
    db.commit()
    db.refresh(runbook)

    return runbook


@protected_router.get(
    "/runbooks",
    response_model=list[RunbookRead],
    tags=["runbooks"],
)
def list_runbooks(
    response: Response,
    service_id: int | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Runbook]:
    statement = (
        select(Runbook)
        .join(Service, Runbook.service_id == Service.id)
        .where(Service.owner_id == current_user.id)
        .order_by(Runbook.created_at.desc(), Runbook.id.desc())
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

    total = db.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    response.headers["X-Total-Count"] = str(total)

    statement = statement.offset(pagination.offset).limit(pagination.limit)

    return list(db.scalars(statement).all())


@protected_router.get(
    "/runbooks/{runbook_id}",
    response_model=RunbookRead,
    tags=["runbooks"],
)
def get_runbook(
    runbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Runbook:
    runbook = db.scalar(
        select(Runbook)
        .join(Service, Runbook.service_id == Service.id)
        .where(
            Runbook.id == runbook_id,
            Service.owner_id == current_user.id,
        )
    )

    if runbook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Runbook not found.",
        )

    return runbook


@protected_router.post(
    "/alerts",
    response_model=AlertRead,
    status_code=status.HTTP_201_CREATED,
    tags=["alerts"],
)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Alert:
    get_owned_service(payload.service_id, current_user, db)

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


@protected_router.get(
    "/alerts",
    response_model=list[AlertRead],
    tags=["alerts"],
)
def list_alerts(
    response: Response,
    service_id: int | None = Query(default=None),
    severity: str | None = Query(default=None, max_length=20),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Alert]:
    statement = (
        select(Alert)
        .join(Service, Alert.service_id == Service.id)
        .where(Service.owner_id == current_user.id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
    )

    if service_id is not None:
        statement = statement.where(Alert.service_id == service_id)

    if severity is not None:
        statement = statement.where(Alert.severity == severity)

    total = db.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    response.headers["X-Total-Count"] = str(total)

    statement = statement.offset(pagination.offset).limit(pagination.limit)

    return list(db.scalars(statement).all())


@protected_router.post(
    "/incidents",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["incidents"],
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Incident:
    get_owned_service(payload.service_id, current_user, db)

    if payload.alert_id is not None:
        alert = db.scalar(
            select(Alert)
            .join(Service, Alert.service_id == Service.id)
            .where(
                Alert.id == payload.alert_id,
                Alert.service_id == payload.service_id,
                Service.owner_id == current_user.id,
            )
        )

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


@protected_router.get(
    "/incidents",
    response_model=list[IncidentRead],
    tags=["incidents"],
)
def list_incidents(
    response: Response,
    service_id: int | None = Query(default=None),
    incident_status: str | None = Query(default=None, alias="status"),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Incident]:
    statement = (
        select(Incident)
        .join(Service, Incident.service_id == Service.id)
        .where(Service.owner_id == current_user.id)
        .order_by(Incident.started_at.desc(), Incident.id.desc())
    )

    if service_id is not None:
        statement = statement.where(Incident.service_id == service_id)

    if incident_status is not None:
        statement = statement.where(Incident.status == incident_status)

    total = db.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    response.headers["X-Total-Count"] = str(total)

    statement = statement.offset(pagination.offset).limit(pagination.limit)

    return list(db.scalars(statement).all())


@router.post(
    "/auth/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    tags=["authentication"],
)
def register_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
) -> User:
    email = payload.email.strip().lower()

    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = User(
        email=email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/auth/login",
    response_model=TokenRead,
    tags=["authentication"],
)
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenRead:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login_at = func.now()
    db.commit()

    return TokenRead(access_token=create_access_token(str(user.id)))


router.include_router(protected_router)