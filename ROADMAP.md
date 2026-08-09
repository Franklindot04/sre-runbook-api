# Project Roadmap

## Purpose

This roadmap records what the repository has completed, how the project is
currently maintained, which improvements may be considered later, and how
future work should be evaluated. It is directional rather than a release
promise: it separates committed repository work from ideas that would need
separate review, validation, and approval.

## Current State

The planned implementation and review roadmap for `sre-runbook-api` is
complete. The project-completion review is also complete, and the repository at
`~/Desktop/sre-runbook-api` is in a stable state that can pause or continue
through focused future work.

Current repository evidence shows a stable `main`, passing local validation,
passing CI validation, PostgreSQL migration coverage in CI, and documentation
and governance foundations in place. Validation totals can change as tests
evolve, so current Ruff, pytest, warning, skip, and CI results should be
reviewed for each pull request instead of treated as permanent counts.

## Completed Foundations

### API and domain foundation

The repository provides a FastAPI application structure for operational
services, runbooks, alerts, incidents, service ownership relationships, public
authentication endpoints, liveness and readiness endpoints, request correlation
IDs, and structured API error handling.

### Authentication and access control

Implemented authentication includes public user registration, login, password
hashing, signed bearer access tokens, API-key protection for operational
routes, active-user checks, ownership filtering, authorization boundaries, safe
not-found behavior for cross-user resources, bearer-token negative-path
coverage, and protected configuration behavior for staging and production
authentication secrets.

### Persistence and migrations

The persistence layer uses SQLAlchemy models and sessions with SQLite defaults
for local development and PostgreSQL integration coverage in CI. Alembic
migrations create the operational tables, authentication users, and service
ownership relationship. Migration validation includes direct PostgreSQL
upgrade checks and lifecycle coverage for upgrade, downgrade to base, and
re-upgrade behavior.

### Quality and reliability

Quality work includes pytest coverage, isolated database fixtures, Ruff,
GitHub Actions validation, configuration checks, error-contract coverage,
security response headers, structured logging safeguards, database readiness
checks, PostgreSQL migration verification, and release-readiness guidance.

### Documentation and governance

The repository includes a project [README](README.md), [contribution
guide](CONTRIBUTING.md), [deployment guide](docs/deployment-environment-guide.md),
[release-readiness checklist](docs/release-readiness-checklist.md),
[project-completion review](docs/project-completion-review.md), [Code of
Conduct](CODE_OF_CONDUCT.md), [NOTICE](NOTICE), [migration notes](migrations/README),
and [Apache License 2.0 license text](LICENSE).

## Current Maintenance Priorities

Current maintenance priorities are ongoing responsibilities rather than
unfinished application features:

- Keep dependency and security updates reviewable through focused pull
  requests.
- Preserve migration compatibility and verify PostgreSQL coverage when
  persistence behavior changes.
- Keep CI reliable and aligned with local validation commands.
- Maintain documentation accuracy when settings, startup behavior, endpoints,
  validation commands, or operational boundaries change.
- Triage issues by operational value, security impact, reliability impact, and
  repository scope.
- Preserve test isolation and avoid leaking local or credential-bearing values
  into repository text.
- Keep `.env.example` aligned with the settings model without publishing real
  secrets.

## Planned Repository Polish

This roadmap belongs to a defined repository-polish series. Remaining
repository-governance work is expected to stay high level and documentation
focused:

- Maintainer guidance that clarifies repository stewardship and review
  expectations.
- Collaboration templates that make issues and pull requests easier to scope,
  validate, and review.
- A final repository consistency and polish review.

These are not application-feature stages and do not commit the project to new
runtime behavior.

## Potential Future Directions

Future directions are optional and evidence-driven. They should not be treated
as commitments until they are proposed, reviewed, validated, and accepted in a
focused pull request.

### Repository governance

Repository operators may consider branch protection, required status checks,
repository rulesets, issue templates, pull-request templates, and clearer
maintainer ownership if those controls fit the project workflow.

### Release management

Release maturity could improve through release tags, release notes, a changelog
policy, versioning conventions, or published container images. The repository
does not currently define automated release publishing or generated release
artifacts.

### Operational visibility

The current API includes structured request logging and readiness checks.
Possible future observability work could include metrics, tracing, expanded
structured logging, service-level objective documentation, or operational
dashboard examples.

### API evolution

Future API work should remain grounded in the existing SRE domain. Possible
areas include richer filtering or search, runbook version history, incident
timelines, alert lifecycle improvements, audit history, pagination refinements,
or query enhancements.

### Deployment maturity

Operators may later add documented deployment targets, container publication,
managed database deployment examples, backup and recovery exercises, or
infrastructure automation. The current repository does not commit to a
particular cloud platform, Kubernetes rollout, Terraform module, Helm chart, or
hosted service.

## Decision Criteria for Future Work

Future proposals should be evaluated against operational value, security
impact, reliability impact, maintenance cost, migration risk, testability,
documentation requirements, backward compatibility, and repository scope.

Significant work should use focused branches, pull requests, validation, and
review. GitHub-recognized co-author attribution should be used only where
genuine joint contribution occurs.

## Out of Scope or Not Currently Committed

This roadmap does not currently commit the project to hosted SaaS operation, a
managed cloud service, Kubernetes deployment, a mobile or browser frontend,
commercial support, automated release publishing, public service availability,
support guarantees, or delivery dates.

## Contributing to the Roadmap

Roadmap proposals should open a focused issue or pull request, state the
problem and expected operational value, identify security, migration, and
compatibility effects, include a validation approach, and avoid bundling
unrelated work. See the [Contribution and Review Process](CONTRIBUTING.md) for
the repository workflow.

## Roadmap Status

The original implementation roadmap is complete, the repository is stable and
validated, and future work is optional and evidence-driven. This roadmap should
be updated when priorities materially change.
