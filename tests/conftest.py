from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sre_runbook_api.auth import create_access_token, hash_password
from sre_runbook_api.config import DEVELOPMENT_API_KEY
from sre_runbook_api.database import Base, SessionLocal, engine
from sre_runbook_api.main import app
from sre_runbook_api.models import User


@pytest.fixture
def empty_database() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(empty_database: None) -> Iterator[Session]:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def authenticated_user(db_session: Session) -> User:
    user = User(
        email="fixture@example.com",
        display_name="Fixture User",
        password_hash=hash_password("fixture-password-123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def authenticated_access_token(authenticated_user: User) -> str:
    return create_access_token(str(authenticated_user.id))


@pytest.fixture
def client(authenticated_access_token: str) -> Iterator[TestClient]:
    with TestClient(
        app,
        headers={
            "X-API-Key": DEVELOPMENT_API_KEY,
            "Authorization": f"Bearer {authenticated_access_token}",
        },
    ) as test_client:
        yield test_client
