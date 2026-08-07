# sre-runbook-api

Centralized SRE runbook API for service alerts, operational metadata, remediation references, and incident context.

## Overview

`sre-runbook-api` is a production-oriented backend service for centralizing operational knowledge used during incident response and on-call workflows.

The API provides a structured foundation for managing:

- Production services.
- Operational runbooks.
- Monitoring alerts.
- Incident context.
- Severity and ownership metadata.
- Database-backed remediation references.

## API Capabilities

The API currently provides:

- Service creation and listing.
- Runbook creation, listing, filtering, and retrieval.
- Alert creation and service-based filtering.
- Incident creation with optional alert association.
- Incident filtering by service and status.
- Liveness and readiness health checks.
- OpenAPI documentation through FastAPI.

## Core Domains

### Services

Represents a production service and its operational ownership.

### Runbooks

Contains structured response procedures, remediation guidance, severity, and service association.

### Alerts

Stores alert fingerprints, monitoring sources, severity, descriptions, and associated services.

### Incidents

Captures active operational incidents, their alert context, severity, status, and affected service.

## Architecture

The project uses a layered backend structure:

- FastAPI provides the HTTP API layer.
- Pydantic provides request and response validation.
- SQLAlchemy provides database access and domain models.
- Alembic manages database schema migrations.
- SQLite supports local development.
- PostgreSQL is supported for production deployments.
- Docker provides a reproducible runtime environment.
- GitHub Actions validates tests and code quality.

## Local Development

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project and development dependencies:

```bash
pip install -e ".[dev]"
cp .env.example .env
```

Create the local database schema:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn sre_runbook_api.main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health/live` | Liveness check |
| GET | `/health/ready` | Readiness check |
| POST | `/api/v1/services` | Create a service |
| GET | `/api/v1/services` | List services |
| POST | `/api/v1/runbooks` | Create a runbook |
| GET | `/api/v1/runbooks` | List and filter runbooks |
| GET | `/api/v1/runbooks/{runbook_id}` | Retrieve a runbook |
| POST | `/api/v1/alerts` | Create an alert |
| GET | `/api/v1/alerts` | List and filter alerts |
| POST | `/api/v1/incidents` | Create an incident |
| GET | `/api/v1/incidents` | List and filter incidents |

## Testing and Quality

Run the test suite:

```bash
pytest
```

Run static analysis:

```bash
ruff check .
```

Run both checks before committing:

```bash
pytest && ruff check .
```

## Database Migrations

Create a new migration after changing models:

```bash
alembic revision --autogenerate -m "describe schema change"
```

Apply migrations:

```bash
alembic upgrade head
```

Check the current migration:

```bash
alembic current
```

## Docker

Build the container:

```bash
docker build -t sre-runbook-api .
```

Run the API:

```bash
docker run --rm -p 8000:8000 sre-runbook-api
```

The container applies database migrations before starting the API server.

## Deployment

Production deployments should provide:

- A PostgreSQL `DATABASE_URL`.
- Environment-specific configuration.
- Automated database migrations.
- Containerized application execution.
- CI validation before merging.
- Secure handling of environment variables and credentials.

## Project Status

Early production-oriented MVP in active development.
