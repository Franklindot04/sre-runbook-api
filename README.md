# SRE Runbook API

`sre-runbook-api` is a production-minded FastAPI backend for structured
operational runbooks, incidents, alerts, service ownership, and reliability
workflows. It gives SRE and platform teams a database-backed API for collecting
the operational context responders need during on-call work: what service is
affected, who owns it, what runbook applies, which alerts are involved, and how
incident records are organized.

The repository is intentionally focused on the API layer and its operating
boundaries. It does not claim a hosted SaaS product, cloud infrastructure, or
deployment platform; those decisions remain outside the repository.
The design emphasizes predictable operational behavior so responders can rely 
on consistent patterns during incident triage and service recovery.

## Project Status

The planned implementation and review roadmap for this repository has been
completed. The project is in a stable, validated state with application code,
migrations, tests, CI, Docker startup behavior, deployment guidance, release
readiness guidance, and contribution workflow documentation in place.

Current non-code follow-up is administrative rather than functional: repository
operators may still choose to configure stricter GitHub branch protection,
release tagging, vulnerability scanning, or platform-specific deployment
controls outside this codebase.

## Project Leadership

- **Franklin Ajero (`@Franklindot04`)** - Project Owner and Maintainer
- **Ellesmaris (`@ellesmaris`)** - Co-Author and Reviewer

The repository was developed through focused pull requests, independent review,
and GitHub-recognized co-authorship where both contributors materially
contributed. Material joint contributions are credited with standard
`Co-authored-by` trailers so GitHub can recognize the work without publishing
collaborator contact details in project documentation.

## Core Capabilities

The API currently supports:

- Public user registration and login.
- Password hashing and signed bearer access tokens.
- API-key protection for operational endpoints.
- User-owned services with list and search behavior scoped to the current user.
- Runbook creation, listing, searching, filtering, and detail retrieval.
- Alert creation, listing, service filtering, severity filtering, and fingerprint
  uniqueness.
- Incident creation with optional alert association and filtering by service or
  status.
- Ownership-aware authorization boundaries for service, runbook, alert, and
  incident operations.
- Pagination with `limit`, `offset`, and `X-Total-Count` on collection routes.
- Liveness and readiness endpoints, including database readiness checks.
- Request correlation IDs, structured request logging, authentication audit
  logging, security response headers, and standardized API error envelopes.
- SQLite-backed local development and PostgreSQL migration coverage in CI.

This README is a high-level project guide rather than a complete endpoint
reference. FastAPI exposes interactive OpenAPI documentation at `/docs` when
the application is running.

## Architecture

The project uses a compact `src` layout:

```text
src/sre_runbook_api/
```

The main application entry point is:

```text
sre_runbook_api.main:app
```

The stack is:

- Python 3.12 or newer.
- FastAPI for the HTTP API.
- Pydantic and Pydantic Settings for request validation and runtime
  configuration.
- SQLAlchemy for persistence models and sessions.
- Alembic for schema migrations.
- SQLite as the default local development database.
- PostgreSQL through the psycopg SQLAlchemy driver for production-style
  integration and CI migration coverage.
- pytest for automated tests.
- Ruff for linting.
- Docker for reproducible container startup.
- GitHub Actions for pull-request validation.

Alembic migration history creates the operational tables, authentication users,
and service ownership relationship. The Dockerfile installs the package, applies
`alembic upgrade head`, and starts Uvicorn on port `8000`.

## Reliability and Security

Implemented reliability and security practices include:

- API-key authentication for protected operational routes.
- Bearer-token authentication for active users.
- Password hashing for registered users.
- Ownership filtering so users see and operate on their own services and
  related runbooks, alerts, and incidents.
- Safe not-found style responses for cross-user resource references.
- Protected-mode validation for staging and production authentication secrets.
- Secret-safe configuration examples in `.env.example`.
- Request correlation IDs in responses, logs, and error payloads.
- Structured JSON access logs and API-key authentication audit logs without
  logging submitted credentials.
- Standardized HTTP and validation error responses with `detail`, `error_code`,
  and `correlation_id`.
- Security response headers on success and error responses.
- Database readiness checks and PostgreSQL migration lifecycle coverage.
- Isolated test database behavior for the ordinary test suite.

The repository does not include Kubernetes manifests, automated release
management, hosted infrastructure, or a vulnerability scanning workflow.

## Getting Started

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project with development dependencies:

```bash
pip install -e ".[dev]"
```

Prepare local configuration:

```bash
cp .env.example .env
```

Apply migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn sre_runbook_api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

For deployment configuration, protected-environment secret validation,
PostgreSQL behavior, migration ordering, and post-start verification, see the
[Deployment Environment Guide](docs/deployment-environment-guide.md).

## Validation

Run the primary local checks before opening a pull request:

```bash
.venv/bin/ruff check .

PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -p no:cacheprovider

git diff --check
```

Local PostgreSQL migration lifecycle coverage may skip when
`CI_POSTGRES_DATABASE_URL` is not available. CI supplies PostgreSQL integration
configuration and runs the migration lifecycle coverage without skipping.

Do not treat a historical test total as a permanent project guarantee. Review
the current Ruff, pytest, warning, skip, and CI results for the exact commit
under review.

## Documentation

- [Contribution and Review Process](CONTRIBUTING.md)
- [Maintainer Guide](MAINTAINERS.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Project Roadmap](ROADMAP.md)
- [Deployment Environment Guide](docs/deployment-environment-guide.md)
- [Release Readiness Checklist](docs/release-readiness-checklist.md)
- [Project Completion Review](docs/project-completion-review.md)
- [Migration Notes](migrations/README)
- [Project Notice](NOTICE)
- [License](LICENSE)

## Repository Workflow

Project work uses focused topic branches and pull requests into `main`.
Contributors validate locally before review, CI provides shared PostgreSQL,
Alembic, Ruff, and pytest evidence, and an independent collaborator reviews the
current PR head before merge.

Recent project work has used normal merge commits. Material joint contributions
are credited with GitHub-recognized `Co-authored-by` trailers, and merged topic
branches are cleaned up after completion. See the
[Contribution and Review Process](CONTRIBUTING.md) for the full workflow.

## License

This project is licensed under the
[Apache License 2.0](LICENSE).
