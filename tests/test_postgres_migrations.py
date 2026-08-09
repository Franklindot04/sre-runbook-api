import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.sql.compiler import IdentifierPreparer

from sre_runbook_api.config import get_settings

POSTGRES_DATABASE_URL_ENV = "CI_POSTGRES_DATABASE_URL"
EXPECTED_TABLES = {
    "alembic_version",
    "alerts",
    "incidents",
    "runbooks",
    "services",
    "users",
}
APPLICATION_TABLES = EXPECTED_TABLES - {"alembic_version"}


def _alembic_config() -> Config:
    return Config("alembic.ini")


def _migration_script() -> ScriptDirectory:
    return ScriptDirectory.from_config(_alembic_config())


def _quote_database_name(engine: Engine, database_name: str) -> str:
    preparer = IdentifierPreparer(engine.dialect)
    return preparer.quote(database_name)


@pytest.fixture
def postgres_database_url() -> Iterator[str]:
    if not os.environ.get(POSTGRES_DATABASE_URL_ENV):
        pytest.skip(
            f"{POSTGRES_DATABASE_URL_ENV} is required for PostgreSQL "
            "migration lifecycle coverage."
        )

    base_url = make_url(os.environ[POSTGRES_DATABASE_URL_ENV])
    database_name = f"test_migrations_{uuid4().hex}"
    admin_engine = create_engine(
        _admin_database_url(base_url),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    quoted_database_name = _quote_database_name(admin_engine, database_name)

    with admin_engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE {quoted_database_name}"))

    test_url = base_url.set(database=database_name)

    try:
        yield test_url.render_as_string(hide_password=False)
    finally:
        _drop_database(admin_engine, database_name, quoted_database_name)
        admin_engine.dispose()


def _admin_database_url(base_url: URL) -> str:
    admin_database = "postgres"
    if base_url.database == admin_database:
        admin_database = "template1"

    return base_url.set(database=admin_database).render_as_string(
        hide_password=False,
    )


def _drop_database(
    admin_engine: Engine,
    database_name: str,
    quoted_database_name: str,
) -> None:
    with admin_engine.connect() as connection:
        connection.execute(
            text(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = :database_name AND pid <> pg_backend_pid()"
            ),
            {"database_name": database_name},
        )
        connection.execute(text(f"DROP DATABASE IF EXISTS {quoted_database_name}"))


def _run_alembic_command(
    monkeypatch: pytest.MonkeyPatch,
    database_url: str,
    revision: str,
) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    try:
        if revision == "base":
            command.downgrade(_alembic_config(), revision)
        else:
            command.upgrade(_alembic_config(), revision)
    finally:
        get_settings.cache_clear()


def _current_database_revision(database_url: str) -> str:
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT version_num FROM alembic_version")
            )
            return result.scalar_one()
    finally:
        engine.dispose()


def _table_names(database_url: str) -> set[str]:
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_migration_history_has_one_downgradeable_head() -> None:
    script = _migration_script()
    heads = script.get_heads()

    assert heads == ["4b309be83536"]
    assert all(
        revision.module.downgrade is not None
        for revision in script.walk_revisions()
    )


def test_postgres_migrations_upgrade_downgrade_and_reupgrade(
    monkeypatch: pytest.MonkeyPatch,
    postgres_database_url: str,
) -> None:
    head_revision = _migration_script().get_current_head()

    _run_alembic_command(monkeypatch, postgres_database_url, "head")

    assert _current_database_revision(postgres_database_url) == head_revision
    assert _table_names(postgres_database_url) == EXPECTED_TABLES

    _run_alembic_command(monkeypatch, postgres_database_url, "base")

    assert not (_table_names(postgres_database_url) & APPLICATION_TABLES)

    _run_alembic_command(monkeypatch, postgres_database_url, "head")

    assert _current_database_revision(postgres_database_url) == head_revision
    assert _table_names(postgres_database_url) == EXPECTED_TABLES
