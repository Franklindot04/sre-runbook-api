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

## Project Roadmap

This checklist tracks the implementation status of the project. Completed work is
checked off, partially implemented work is marked as partial, and unfinished
items are listed under **NEXT — ROADMAP**.

### Completed

- [x] API security configuration
  - Protected operational endpoints require an API key.
  - API keys are compared using `secrets.compare_digest()`.
  - Missing and invalid API keys return `401 Unauthorized`.

- [x] Service management
  - Services can be created and listed.
  - Service metadata includes ownership information.

- [x] Runbook creation and retrieval
  - Runbooks can be created and retrieved.
  - Runbooks are associated with existing services.
  - Runbooks support filtering by title and slug search fields.

- [x] Alert management
  - Alerts can be created and listed.
  - Alerts support service-based filtering.
  - Alerts contain fingerprints, monitoring sources, severity, and descriptions.

- [x] Incident creation and filtering
  - Incidents can be created with optional alert associations.
  - Incidents support filtering by service and status.
  - Incident severity and open status are represented in the API.

- [x] Pagination utilities
  - Collection endpoints support `limit` and `offset`.
  - Invalid pagination values are rejected.
  - Filtered collections expose `X-Total-Count`.

- [x] Health endpoints
  - Liveness and readiness endpoints are available.

- [x] Database migrations
  - Alembic is used to manage schema migrations.

- [x] Automated quality checks
  - The test suite runs through pytest.
  - Ruff validates code quality.
  - GitHub Actions runs CI checks for pull requests.

- [x] Negative-path API tests — current scope
  - Missing API keys.
  - Invalid API keys.
  - Invalid pagination values.
  - Missing runbook services.
  - Authentication audit-log safety.

### Partially implemented

- [ ] Structured application logging
  - Authentication success and failure events are emitted as structured JSON.
  - API keys and authorization credentials are not logged.
  - **NEXT — ROADMAP:** extend structured logging consistently across request,
    database, runbook, alert, and incident operations.

- [ ] Request correlation IDs
  - Authentication audit events include a `correlation_id` field.
  - **NEXT — ROADMAP:** add middleware that creates or propagates a correlation
    ID and makes it available throughout the request lifecycle.

- [ ] Database test fixtures
  - Tests currently reset the database schema between tests.
  - **NEXT — ROADMAP:** improve fixture isolation and add PostgreSQL-backed
    integration fixtures.

- [ ] PostgreSQL integration configuration
  - PostgreSQL is identified as the production database target.
  - **NEXT — ROADMAP:** add verified PostgreSQL integration configuration and
    automated integration coverage.

- [ ] Branch protection and repository governance
  - Feature branches, pull requests, and CI checks are in use.
  - **NEXT — ROADMAP:** verify protected branches, required reviews, required
    status checks, and merge policy in repository settings.

### NEXT — ROADMAP

- [ ] Authentication models.
- [ ] Authentication endpoints.
- [ ] Password hashing and token handling.
- [ ] User/service ownership authorization.
- [ ] Runbook update endpoint.
- [ ] Runbook lifecycle status.
- [ ] Alert deduplication improvements.
- [ ] Incident status transitions.
- [ ] Incident resolution endpoint.
- [ ] Incident timeline events.
- [ ] Remediation references.
- [ ] Consistent API error responses.
- [ ] Metrics endpoint.
- [ ] Expanded readiness checks.
- [ ] Container non-root hardening.
- [ ] Docker health check.
- [ ] Dependency and security scanning.
- [ ] Release metadata and versioning.
- [ ] Deployment documentation.
- [ ] Final integration and release validation.

## Current Status

The project is an early production-oriented MVP with service, runbook, alert,
and incident workflows; API-key protection; filtering and pagination; database
migrations; health checks; automated tests; and CI validation.

The next implementation focus is the authentication foundation: authentication
models, password hashing, token handling, authentication endpoints, and
ownership-based authorization.
