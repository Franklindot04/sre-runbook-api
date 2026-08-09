# Release Readiness Checklist

Use this checklist as the final gate before deploying or publishing a release of
`sre-runbook-api`. It is intentionally provider-neutral: the repository defines
validation commands, migration behavior, startup behavior, and health checks,
while the operator remains responsible for the target deployment platform,
secrets, backups, traffic routing, and recovery decisions.

For environment-specific configuration details, review the
[Deployment Environment Guide](deployment-environment-guide.md) before using
this checklist.

## Pre-Release

### Release Identification and Scope

- [ ] Release purpose and intended change set are written down.
- [ ] Exact commit or merge commit intended for release is recorded.
- [ ] Release source is `main`.
- [ ] Commits and pull requests included in the release are reviewed.
- [ ] Database, configuration, security, and operational impact are identified.
- [ ] Release owner or operator is recorded outside repository secrets.
- [ ] Any version label or release name is an operator decision; the repository
      does not currently define automated semantic versioning, generated
      changelogs, signed releases, or release artifacts.

### Git and Pull-Request State

- [ ] Working tree is clean.
- [ ] Local `main` is synchronized with `origin/main`.
- [ ] Feature changes were merged through reviewed pull requests.
- [ ] Required reviews are complete.
- [ ] Required conversations are resolved where applicable.
- [ ] Required GitHub Actions checks for the release commit are successful.
- [ ] No unmerged release-critical branch is outstanding.
- [ ] No force-push or branch-protection bypass was used for the release.

### Quality Validation

- [ ] Ruff passes with zero failures:

  ```bash
  .venv/bin/ruff check .
  ```

- [ ] The full pytest suite passes with zero failures:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 \
    .venv/bin/python -m pytest -p no:cacheprovider
  ```

- [ ] Test totals are reviewed from the current run instead of treated as a
      timeless contract.
- [ ] Local PostgreSQL migration coverage is reviewed: it may skip when
      `CI_POSTGRES_DATABASE_URL` is absent.
- [ ] The authoritative CI run executes PostgreSQL migration coverage without
      skips.
- [ ] The known third-party warning count is reviewed for unexpected changes.
- [ ] CI validation passed for PostgreSQL container readiness, PostgreSQL
      connectivity, direct Alembic validation, Ruff, the full pytest suite, and
      the PostgreSQL migration lifecycle.

### Configuration Readiness

- [ ] Intended `ENVIRONMENT` is selected and reviewed.
- [ ] `DATABASE_URL` is supplied for the target database by the deployment
      environment.
- [ ] `API_KEY` is supplied through protected deployment configuration.
- [ ] `API_KEY_HEADER` matches client and operational expectations.
- [ ] `JWT_SECRET_KEY` is supplied through protected deployment configuration.
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES`, `LOG_LEVEL`, `APP_NAME`, `APP_VERSION`, and
      `DEBUG` are reviewed for the target environment.
- [ ] Staging and production protected-mode validation rejects blank secrets,
      repository defaults, documented placeholders, and secrets shorter than 32
      characters.
- [ ] Secret values are not committed to repository files, copied into logs, or
      pasted into pull requests.
- [ ] Configuration is reviewed against the
      [Deployment Environment Guide](deployment-environment-guide.md).

### Database and Migration Readiness

- [ ] Target PostgreSQL database is reachable from the deployment environment.
- [ ] Database credentials are scoped with least privilege for the deployment
      role.
- [ ] Backup, restore, or recovery decision is made before any release that
      carries migration risk.
- [ ] Current Alembic head is understood from repository migration history.
- [ ] Direct migration execution is validated:

  ```bash
  alembic upgrade head
  ```

- [ ] Current revision state is inspected:

  ```bash
  alembic current
  ```

- [ ] Head alignment is checked where available:

  ```bash
  alembic current --check-heads
  ```

- [ ] Migration compatibility is reviewed with the application revision being
      released.
- [ ] Application code and migration revisions are kept aligned before traffic
      is directed.
- [ ] Migration failure handling is decided before deployment begins.
- [ ] CI validation against synthetic PostgreSQL is treated as repository
      evidence, not as proof that the actual deployment database is reachable or
      recoverable.
- [ ] Downgrade coverage in tests is not treated as a guaranteed safe production
      rollback path; backup and recovery planning remain required.

### Container and Startup Readiness

- [ ] Container build or runtime configuration is reviewed.
- [ ] Migration-before-startup ordering is understood.
- [ ] Application module is confirmed as `sre_runbook_api.main:app`.
- [ ] Deployed process starts with explicit host and port values, or uses the
      container entry point.
- [ ] The Docker entry point behavior is understood: migrations run before
      Uvicorn starts on port `8000`.
- [ ] Deployment environment supplies all required settings before migration or
      startup imports configuration.
- [ ] No image registry, hosting platform, Kubernetes rollout, canary, blue-green
      deployment, or automated rollback capability is assumed from the
      repository.

### Security Readiness

- [ ] Protected-mode secrets are non-default, non-placeholder, nonblank, and at
      least 32 characters in staging and production.
- [ ] Secret material is absent from commits, pull requests, logs, and release
      notes.
- [ ] Database permissions follow least privilege.
- [ ] Authentication smoke tests use placeholders or deployment-platform secret
      references instead of raw secret values.
- [ ] Release does not weaken API-key, bearer-token, ownership, authentication,
      or authorization boundaries.
- [ ] Security-related changes received focused review.
- [ ] Exposed FastAPI documentation behavior at `/docs` is understood for the
      target environment.
- [ ] Security response headers and standardized error behavior are expected to
      remain in place.
- [ ] Any vulnerability scanning, release approval system, or credential
      rotation policy is handled outside the repository unless implemented in a
      future change.

## Deployment

### Deployment Execution

- [ ] Exact release commit is recorded before deployment starts.
- [ ] Target configuration is applied before migration and startup.
- [ ] Migrations complete before the application serves traffic.
- [ ] Application starts through the supported command or container entry point.
- [ ] Operator observes startup output for non-sensitive configuration,
      migration, import, or database failures.
- [ ] Traffic is not directed to the release until verification succeeds.
- [ ] Provider-specific orchestration commands are recorded in external runbooks,
      not inferred from this repository.

## Post-Deployment

### Post-Deployment Verification

- [ ] Liveness endpoint returns a successful response:

  ```bash
  curl -fsS http://<host>:<port>/health/live
  ```

- [ ] Readiness endpoint returns a successful response and the expected
      environment:

  ```bash
  curl -fsS http://<host>:<port>/health/ready
  ```

- [ ] FastAPI documentation behavior at `/docs` is verified according to the
      target environment decision.
- [ ] Public authentication flow is smoke-tested through `/api/v1/auth/register`
      and `/api/v1/auth/login` using safe secret handling.
- [ ] At least one protected database-backed read path is verified with the
      configured API-key header and a bearer token.
- [ ] `X-Correlation-ID` behavior is present on representative success and error
      responses.
- [ ] No unexpected standardized error-contract or security-header regression is
      observed.
- [ ] Logs are reviewed for startup, readiness, authentication, and request
      errors without exposing secret values.

### Rollback and Recovery Decision

- [ ] Rollback owner is identified.
- [ ] Previous application revision is known.
- [ ] Database compatibility with the previous revision is assessed.
- [ ] Backup, restore, or recovery route is understood for migration-bearing
      releases.
- [ ] Criteria for stopping traffic, rolling back application code, or starting
      recovery are defined.
- [ ] Rollback does not rely automatically on `alembic downgrade`.
- [ ] Incident or recovery notes are captured when release verification fails.

## Closure

### Evidence and Closure

- [ ] Release commit is recorded.
- [ ] Pull requests included in the release are recorded.
- [ ] CI run URL or identifier is recorded.
- [ ] Migration result is recorded.
- [ ] Deployment time is recorded.
- [ ] Verification result is recorded.
- [ ] Unresolved warnings or accepted risks are recorded.
- [ ] Rollback or recovery decision is recorded.
- [ ] Operator or reviewer sign-off is recorded.
- [ ] Documentation updates are recorded.
- [ ] Follow-up issues or repository tasks are recorded without introducing a
      new issue-tracking platform.

### Stop Conditions

Stop the release when any of the following are true:

- [ ] CI failed, is incomplete, or did not run for the intended release commit.
- [ ] Required approval is missing.
- [ ] Branch, commit, or release-source evidence does not match the intended
      release.
- [ ] Protected-mode secret configuration is unsafe or missing.
- [ ] Target database is unreachable.
- [ ] Migration failed or current revision state is unknown.
- [ ] Application startup failed.
- [ ] Liveness, readiness, authentication, or protected smoke verification
      failed.
- [ ] Rollback or recovery position is unknown for a risky migration.
- [ ] Secret disclosure is suspected in commits, logs, documentation, pull
      requests, or release notes.
