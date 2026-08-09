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

- Public user registration and login.
- Service creation and listing.
- Runbook creation, listing, filtering, and retrieval.
- Alert creation and service-based filtering.
- Incident creation with optional alert association.
- Incident filtering by service and status.
- Liveness and readiness health checks.
- Correlation IDs, structured request logs, standardized error responses, and
  security response headers.
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
| POST | `/api/v1/auth/register` | Register a user and return the created user record |
| POST | `/api/v1/auth/login` | Validate credentials and return a bearer access token |
| POST | `/api/v1/services` | Create a service |
| GET | `/api/v1/services` | List services |
| POST | `/api/v1/runbooks` | Create a runbook |
| GET | `/api/v1/runbooks` | List and filter runbooks |
| GET | `/api/v1/runbooks/{runbook_id}` | Retrieve a runbook |
| POST | `/api/v1/alerts` | Create an alert |
| GET | `/api/v1/alerts` | List and filter alerts |
| POST | `/api/v1/incidents` | Create an incident |
| GET | `/api/v1/incidents` | List and filter incidents |

The two authentication endpoints are public. The operational endpoints under
`/api/v1/services`, `/api/v1/runbooks`, `/api/v1/alerts`, and
`/api/v1/incidents` require both the configured API key header and a bearer
token for an active user. The API key protects the operational API surface; the
bearer token resolves the current user for ownership checks.

Registration stores a normalized email address and a hashed password. Login
verifies the submitted password and returns a signed JWT bearer token. The API
does not return password hashes in registration or login responses.

Services are owned by users. Service listing returns only the current user's
services, and runbook, alert, and incident operations are restricted through
the owned service relationship where those routes exist. Cross-user service,
runbook, alert, and incident references are rejected with the same not-found
style responses used for missing resources.

Every request receives an `X-Correlation-ID` response header. A valid incoming
`X-Correlation-ID` is preserved; invalid or missing values are replaced. Access
logs are emitted as JSON records with request method, path, status code,
duration, and correlation ID. API-key authentication success and failure events
are also logged as structured JSON without logging submitted API keys or bearer
credentials. HTTP and validation errors use the repository error envelope with
`detail`, `error_code`, and `correlation_id`. Responses include the configured
security headers.

## Testing and Quality

Run the test suite:

```bash
.venv/bin/python -m pytest
```

Run static analysis:

```bash
.venv/bin/ruff check .
```

Run both checks before committing:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
```

CI installs the project with development dependencies on Python 3.12, then runs
`ruff check .` and `pytest` for pull requests targeting `main`.

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

For repository-specific deployment configuration, migration ordering, startup,
and verification guidance, see the
[Deployment Environment Guide](docs/deployment-environment-guide.md).

## Project Roadmap

This checklist tracks the implementation status of the project. Completed work is
checked off, partially implemented work is marked as partial, and unfinished
items are listed under **NEXT — ROADMAP**.

### Completed

- [x] API security configuration
  - Protected operational endpoints require an API key.
  - API keys are compared using `secrets.compare_digest()`.
  - Missing and invalid API keys return `401 Unauthorized`.

- [x] Authentication foundation
  - Users can register through `POST /api/v1/auth/register`.
  - Users can log in through `POST /api/v1/auth/login`.
  - Passwords are hashed with `pwdlib`.
  - Login returns a signed bearer JWT.
  - Invalid, expired, malformed, inactive-user, and missing-user tokens are
    rejected.

- [x] Service management
  - Services can be created and listed.
  - Service metadata includes owner-team information.
  - Created services are assigned to the authenticated user.
  - Service listing is scoped to the authenticated user.

- [x] Runbook creation and retrieval
  - Runbooks can be created and retrieved.
  - Runbooks are associated with existing services owned by the current user.
  - Runbooks support filtering by title and slug search fields.
  - Runbook detail lookup hides another user's runbooks with a not-found
    response.

- [x] Alert management
  - Alerts can be created and listed.
  - Alerts support service-based filtering.
  - Alerts contain fingerprints, monitoring sources, severity, and descriptions.
  - Alert creation and listing are scoped through owned services.

- [x] Incident creation and filtering
  - Incidents can be created with optional alert associations.
  - Incidents support filtering by service and status.
  - Incident severity and open status are represented in the API.
  - Incident creation rejects cross-user service and alert references with safe
    not-found responses.

- [x] Pagination utilities
  - Collection endpoints support `limit` and `offset`.
  - Invalid pagination values are rejected.
  - Filtered collections expose `X-Total-Count`.

- [x] Request correlation IDs
  - Requests receive an `X-Correlation-ID` response header.
  - Valid incoming correlation IDs are preserved.
  - Invalid or missing correlation IDs are replaced.
  - Error responses and structured logs include the active correlation ID.

- [x] Structured request logging
  - Completed requests are logged as JSON access events.
  - Failed requests are logged as JSON failure events.
  - Access log records include method, path, status code, duration, and
    correlation ID.

- [x] Authentication audit logging
  - API-key success and failure events are emitted as structured JSON.
  - API keys and authorization credentials are not logged.

- [x] Standardized error responses
  - HTTP errors include `detail`, `error_code`, and `correlation_id`.
  - Validation errors use the same response envelope.

- [x] Security response headers
  - Responses include content-type, frame, frame-ancestor, referrer, and
    cache-control headers.
  - Header coverage is tested for success and error responses.

- [x] Health endpoints
  - Liveness and readiness endpoints are available.
  - Readiness checks the database connection and returns `503` when unavailable.

- [x] Database migrations
  - Alembic is used to manage schema migrations.
  - Current migrations create operational tables, users, and service ownership.

- [x] Automated quality checks
  - The test suite runs through pytest.
  - Ruff validates code quality.
  - GitHub Actions runs CI checks for pull requests.

- [x] Negative-path API tests — current scope
  - Missing API keys.
  - Invalid API keys.
  - Missing and invalid bearer tokens.
  - Invalid pagination values.
  - Missing runbook services.
  - Cross-user ownership references.
  - Authentication audit-log safety.

### Partially implemented

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

- [ ] Broaden authorization coverage for future update and delete routes when
  those routes are added.
- [ ] Runbook update endpoint.
- [ ] Runbook lifecycle status.
- [ ] Alert deduplication improvements.
- [ ] Incident status transitions.
- [ ] Incident resolution endpoint.
- [ ] Incident timeline events.
- [ ] Remediation references.
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
and incident workflows; public registration and login; API-key and bearer-token
requirements for operational routes; ownership-scoped service, runbook, alert,
and incident access; filtering and pagination; database migrations; health
checks; correlation IDs; structured request and authentication logs; standard
error envelopes; security headers; automated tests; and CI validation.

Remaining work is focused on product endpoints that do not exist yet, broader
integration coverage, PostgreSQL validation, deployment documentation, container
hardening, repository governance verification, and final release validation.
