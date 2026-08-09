# Deployment Environment Guide

This guide describes how to configure and start `sre-runbook-api` in
development, staging, and production using behavior already present in the
repository. It covers runtime settings, database connectivity, authentication
secrets, migration execution, startup, and basic post-start verification.

It does not define cloud-provider infrastructure, reverse proxies, process
managers, autoscaling, secret-manager products, or release approval policy.

## Supported Environments

The settings model accepts any `ENVIRONMENT` string, with `development` as the
default. Current tests cover `development`, `test`, `staging`, and
`production`.

Only `staging` and `production` receive protected-mode validation for
authentication secrets. In those modes, application settings reject missing or
unsafe API-key and JWT-secret configuration during settings construction. Other
modes allow deterministic local defaults so development and tests can run
without deployment secrets.

## Configuration Loading

Runtime configuration is read through the Pydantic settings model in
`src/sre_runbook_api/config.py`.

The model supports environment variables and a root-level `.env` file. The
configuration declares `env_file=".env"`, uses UTF-8 encoding, treats variable
names case-insensitively, and ignores extra variables. Environment variables
provided by the shell or deployment platform override values loaded from `.env`.

Use `.env` only for local development. Deployed staging and production secrets
should come from the deployment platform or its secret store, not from committed
files. Do not commit real credentials, API keys, JWT secrets, tokens, passwords,
or credential-bearing database URLs.

## Environment Variables

| Variable | Purpose | Sensitive | Development behavior | Staging and production requirement | Safe example format |
| --- | --- | --- | --- | --- | --- |
| `APP_NAME` | FastAPI application title | No | Defaults to the repository application name | Optional | `SRE Runbook API` |
| `APP_VERSION` | FastAPI application version | No | Defaults to the package version | Optional | `0.1.0` |
| `ENVIRONMENT` | Runtime environment selector | No | Defaults to `development` | Set to `staging` or `production` to enable protected-mode validation | `production` |
| `DEBUG` | Boolean debug flag in settings | No | Defaults to `false` | Optional; no startup behavior currently depends on it | `false` |
| `LOG_LEVEL` | Access logger level | No | Defaults to `INFO`; normalized to uppercase | Optional, but must be one of the supported Python logging levels | `INFO` |
| `DATABASE_URL` | SQLAlchemy and Alembic database URL | Yes when it contains credentials | Defaults to a local SQLite file | Required for PostgreSQL-backed deployments | `<database-url>` |
| `API_KEY` | API key required by protected operational endpoints | Yes | A repository-known development default is available outside protected modes | Required; must be nonblank, at least 32 characters, and not a repository default or documented placeholder | `<generated-api-key>` |
| `API_KEY_HEADER` | Header name used for API-key authentication | No | Defaults to `X-API-Key` | Optional unless the deployment standard requires a different header | `X-API-Key` |
| `JWT_SECRET_KEY` | HMAC signing key for bearer access tokens | Yes | A repository-known development default is available outside protected modes | Required; must be nonblank, at least 32 characters, and not a repository default or documented placeholder | `<generated-jwt-secret>` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime in minutes | No | Defaults to `30` | Optional | `30` |

## Protected-Mode Secret Validation

When `ENVIRONMENT` is `staging` or `production`, settings construction validates
`API_KEY` and `JWT_SECRET_KEY` before migrations or application startup can use
the configuration.

Both secrets are rejected when they are blank or whitespace-only, when they
match repository-known development defaults, or when they match documented
placeholder values. Both secrets must also contain at least 32 characters
outside development.

The implementation does not currently enforce entropy scoring, character-class
rules, rotation schedules, or a rule that the API key and JWT secret must differ.
Apply those controls through deployment policy if they are required by the
operating environment.

## Database Configuration

`DATABASE_URL` is consumed by both the application engine in
`src/sre_runbook_api/database.py` and Alembic in `migrations/env.py`. Alembic
sets its SQLAlchemy URL from the same settings value, so migration commands and
the running API must point at the same database revision target.

Local development defaults to SQLite:

```text
sqlite:///./sre_runbook.db
```

The application enables SQLite `check_same_thread=False` only when the database
URL starts with `sqlite`. All engines use SQLAlchemy `pool_pre_ping=True`.

Production deployments are expected to provide a PostgreSQL `DATABASE_URL`.
The installed dependency stack includes the psycopg SQLAlchemy driver, and CI
validates PostgreSQL connectivity and migrations with this URL form:

```text
postgresql+psycopg://<host>:<port>/<database>
```

Keep database credentials least-privileged for the deployment role. Do not put a
complete credential-bearing URL in repository files, documentation, logs, pull
request text, or shell transcripts.

## Migration Procedure

Run migrations before serving staging or production traffic:

```bash
alembic upgrade head
```

Inspect the current migration state with:

```bash
alembic current
```

To fail when the database is not at the current head, use:

```bash
alembic current --check-heads
```

The current migration history has one head and creates the operational tables,
authentication users, and service ownership columns. CI validates direct
`alembic upgrade head` execution against PostgreSQL, then checks the database is
at the migration head. The PostgreSQL migration lifecycle test also exercises
upgrade, downgrade to base, and re-upgrade coverage; that downgrade coverage is
a test safety check, not a recommendation to use downgrades casually as a
production rollback strategy.

## Application Startup

The repository-supported application module is:

```text
sre_runbook_api.main:app
```

For local development, the README-supported command is:

```bash
uvicorn sre_runbook_api.main:app --reload
```

For a deployed process, provide configuration first, run migrations, and then
start Uvicorn with explicit host and port values:

```bash
alembic upgrade head
uvicorn sre_runbook_api.main:app --host <host> --port <port>
```

The Dockerfile installs the package, exposes port `8000`, applies migrations,
and starts the API with:

```text
alembic upgrade head && uvicorn sre_runbook_api.main:app --host 0.0.0.0 --port 8000
```

Because settings are constructed during import of the main application and
database modules, invalid protected-mode secrets, invalid log levels, or an
unsupported database URL can prevent both migration and application startup.

## Post-Start Verification

Liveness does not require authentication:

```bash
curl -fsS http://<host>:<port>/health/live
```

Readiness verifies database connectivity and returns the active environment in
the response body:

```bash
curl -fsS http://<host>:<port>/health/ready
```

FastAPI interactive documentation is available at:

```text
http://<host>:<port>/docs
```

The public authentication endpoints are under `/api/v1/auth/register` and
`/api/v1/auth/login`. Operational endpoints under `/api/v1/services`,
`/api/v1/runbooks`, `/api/v1/alerts`, and `/api/v1/incidents` require both the
configured API-key header and a bearer token for an active user. Use placeholders
or deployment-platform secret references in runbooks and smoke checks rather
than writing raw secrets into commands.

## Failure Guidance

Protected-mode secret validation failure:
Check `ENVIRONMENT`, `API_KEY`, and `JWT_SECRET_KEY`. In `staging` and
`production`, both secrets must be nonblank, at least 32 characters, and must
not be repository-known development defaults or documented placeholders.

Database connectivity failure:
Check `DATABASE_URL`, network reachability, database credentials, and whether
the database server is accepting connections. `/health/ready` returns `503`
with `Database unavailable` when the application cannot execute a simple
database query.

Migration failure:
Confirm that `DATABASE_URL` points to the intended database and run
`alembic current` or `alembic current --check-heads` to inspect revision state.
Keep migrations and application revisions aligned before directing traffic.

Invalid environment selection:
The settings model accepts arbitrary environment strings, but protected-mode
secret validation applies only to `staging` and `production`. Use one of the
documented environment names for predictable operator behavior.

Authentication configuration failure:
Confirm clients send the configured `API_KEY_HEADER` and a bearer token from
`/api/v1/auth/login` for protected operational endpoints. Do not log or echo the
actual API key, JWT secret, or bearer token while troubleshooting.

## Deployment Safety Notes

Keep real secrets out of committed files, examples, documentation, pull request
text, and command output. Use synthetic values in CI and local tests. Provide
staging and production credentials through the deployment environment, apply
least privilege to database credentials, rotate credentials through the
deployment platform when needed, run migrations before startup, and verify
health endpoints before directing traffic.

For local startup, testing, and endpoint details, see the repository
[README](../README.md).
