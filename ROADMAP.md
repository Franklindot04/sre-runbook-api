# Project Roadmap

## Purpose

This roadmap records what the repository has completed, how the project is
currently maintained, which improvements may be considered later, and how
future work should be evaluated. It is directional rather than a release
promise: it separates committed repository work from ideas that would need
separate review, validation, and approval.

## Current State

The planned implementation and final repository-polish series for
`sre-runbook-api` are complete. The project-completion review is current, and
the repository at `~/Desktop/sre-runbook-api` is in a stable state that can
pause or continue through focused future work.

Current repository evidence shows a stable `main`, passing local validation,
passing CI validation, PostgreSQL migration coverage in CI, and documentation
and governance foundations in place. Validation totals can change as tests
evolve, so current Ruff, pytest, warning, skip, and CI results should be
reviewed for each pull request instead of treated as permanent counts.
The current state also reflects consistent alignment between local development behavior
and CI validation, ensuring contributors experience predictable results across environments.

## Completed Foundations

### API and domain foundation

The repository provides a FastAPI application structure for operational
services, runbooks, alerts, incidents, service ownership relationships, public
authentication endpoints, liveness and readiness endpoints, request correlation
IDs, and structured API error handling.
This foundation also ensures that operational entities share consistent validation and 
response patterns, reducing ambiguity for both automated systems and human responders.


### Authentication and access control

Implemented authentication includes public user registration, login, password
hashing, signed bearer access tokens, API-key protection for operational
routes, active-user checks, ownership filtering, authorization boundaries, safe
not-found behavior for cross-user resources, bearer-token negative-path
coverage, and protected configuration behavior for staging and production
authentication secrets.
These controls collectively ensure that operational actions remain scoped to 
the correct user context, preventing accidental or unauthorized cross-service interactions.

### Persistence and migrations

The persistence layer uses SQLAlchemy models and sessions with SQLite defaults
for local development and PostgreSQL integration coverage in CI. Alembic
migrations create the operational tables, authentication users, and service
ownership relationship. Migration validation includes direct PostgreSQL
upgrade checks and lifecycle coverage for upgrade, downgrade to base, and
re-upgrade behavior.This lifecycle validation helps ensure that schema changes remain predictable
across environments, reducing migration-related surprises during development or CI execution.

### Quality and reliability

Quality work includes pytest coverage, isolated database fixtures, Ruff,
GitHub Actions validation, configuration checks, error-contract coverage,
security response headers, structured logging safeguards, database readiness
checks, PostgreSQL migration verification, and release-readiness guidance.
These safeguards help ensure that both functional behavior and operational boundaries 
remain stable as the codebase evolves, reducing regressions and unexpected runtime conditions.

### Documentation and governance

The repository includes a project [README](README.md), [contribution
guide](CONTRIBUTING.md), [deployment guide](docs/deployment-environment-guide.md),
[release-readiness checklist](docs/release-readiness-checklist.md),
[project-completion review](docs/project-completion-review.md),
[maintainer guide](MAINTAINERS.md), [Code of Conduct](CODE_OF_CONDUCT.md),
[NOTICE](NOTICE), [migration notes](migrations/README), issue forms, a
pull-request template, and [Apache License 2.0 license text](LICENSE).
Together, these documents provide a consistent governance baseline that helps contributors 
understand expectations, workflows, and operational responsibilities across the project.

## Current Maintenance Priorities
Ongoing maintenance focuses on keeping daily contributor workflows smooth and predictable while preserving the project’s validated operational behavior.
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

## Completed Repository Polish

The final repository-polish series is complete. It refreshed the project
identity and README, added a Code of Conduct, added a project NOTICE, reconciled
the roadmap, added maintainer guidance, added GitHub collaboration templates,
and completed this final consistency review.

These were documentation and governance changes. They did not introduce new
runtime behavior or start another application-feature stage.
This polish pass ensures that the repository presents a coherent, 
contributor-friendly structure that accurately reflects the project’s completed state.

## Potential Future Directions

Optional improvements listed here serve as reference ideas that can be evaluated independently when contributors explore new work.
Future directions are optional and evidence-driven. They should not be treated
as commitments until they are proposed, reviewed, validated, and accepted in a
focused pull request.

### Repository governance

Governance adjustments in this area are typically lightweight and can be adopted gradually as workflow needs evolve.
Repository operators may consider branch protection, required status checks,
repository rulesets, deletion protection, private vulnerability reporting, and
collaborator-permission adjustments if those controls fit the project workflow.

### Release management

Release-related refinements often emerge naturally as contributors 
seek clearer version history or more predictable distribution patterns.
Release maturity could improve through release tags, release notes, a changelog
policy, versioning conventions, or published container images. The repository
does not currently define automated release publishing or generated release
artifacts.

### Operational visibility

Visibility enhancements often arise from practical needs 
discovered during troubleshooting or workflow refinement.
The current API includes structured request logging and readiness checks.
Possible future observability work could include metrics, tracing, expanded
structured logging, service-level objective documentation, or operational
dashboard examples.

### API evolution

API refinements often emerge from practical usage patterns that 
highlight opportunities for clearer operational flow or more expressive queries.
Future API work should remain grounded in the existing SRE domain. Possible
areas include richer filtering or search, runbook version history, incident
timelines, alert lifecycle improvements, audit history, pagination refinements,
or query enhancements.

### Deployment maturity

Deployment-related refinements often emerge from practical hosting 
needs or integration patterns discovered during real-world usage.
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
