# Contribution and Review Process

This guide describes how to prepare, validate, review, merge, and clean up
changes for `sre-runbook-api`. It reflects the repository's current workflow:
focused topic branches into `main`, local validation with Ruff and pytest, and
GitHub Actions coverage for PostgreSQL, Alembic, linting, and tests.

## Contribution Boundaries

Each pull request should have one clear purpose. Keep production behavior,
tests, migrations, documentation, CI, deployment assets, and runtime
configuration changes separated when they need different review attention.
Avoid broad refactors, unrelated formatting churn, generated files, and local
developer artifacts in feature or documentation branches.

Security-sensitive findings should not be disclosed in public issues, pull
requests, logs, or screenshots. Use a maintainer-approved private reporting
channel when one is available, and keep credentials, tokens, API keys, JWT
secrets, database passwords, and credential-bearing URLs out of repository text.

## Development Prerequisites

The package is installed from `src` and requires Python `>=3.12`. CI currently
runs on Python 3.12. Create a project environment and install development
dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Local development defaults to SQLite. PostgreSQL is used for production-style
deployment and CI integration coverage. The pytest configuration adds `src` to
the import path, and the supported application module is:

```text
sre_runbook_api.main:app
```

Apply local migrations before running the API manually:

```bash
alembic upgrade head
uvicorn sre_runbook_api.main:app --reload
```

See the [Deployment Environment Guide](docs/deployment-environment-guide.md) for
environment variables, protected-mode secret validation, PostgreSQL deployment
behavior, and migration startup ordering.

## Focused Branches

Synchronize with `main` before starting work, then create a descriptive topic
branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c docs/example-guide
```

Observed branch categories include `docs/...`, `test/...`, `ci/...`,
`security/...`, `refactor/...`, `chore/...`, and `feat/...`. Do not commit
directly to `main` in normal project work. Keep the branch limited to the
approved purpose and split unrelated changes into separate pull requests.

## Making Changes Safely

Preserve existing behavior unless the pull request explicitly changes it. Add
or update tests for behavior changes, especially around authentication,
authorization, ownership boundaries, error contracts, logging, configuration,
and database behavior.

Schema changes should include Alembic migration revisions when they genuinely
change persisted structure. Do not edit existing migration history casually.
Keep PostgreSQL migration responsibilities separate from ordinary SQLite-backed
test fixtures: local PostgreSQL lifecycle coverage may skip without a
`CI_POSTGRES_DATABASE_URL`, while CI must run the PostgreSQL migration lifecycle
without skips.

Configuration and authentication changes must use placeholders or synthetic
values. Update relevant documentation when behavior, operator steps,
environment variables, validation commands, or security expectations change.

## Local Validation

Run validation through the active project environment:

```bash
.venv/bin/ruff check .
PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -p no:cacheprovider
git diff --check
```

Zero Ruff and pytest failures are required. Review pytest totals from the
current run instead of treating any historical test count as permanent. The
known third-party warning should be checked for unexpected changes. If Markdown
changes include links, verify every relative link resolves to a tracked
repository path. Run an installed Markdown linter when the repository
environment already provides one; do not add a linter as part of an unrelated
change.

## Commit Preparation

Stage only the files that belong to the pull request and inspect the staged
scope before committing:

```bash
git diff --name-only
git diff --cached --name-only
git diff --cached --check
```

Use focused, factual commit subjects. Recent history uses conventional prefixes
such as `docs:`, `test:`, `ci:`, `security:`, `refactor:`, `chore:`, and
`feat:`. Avoid PR numbers in commit subjects unless a maintainer explicitly
asks for one. Confirm the configured author identity is intentional, but do not
publish local Git identity values in pull request text.

Never commit secrets, credential-bearing URLs, personal filesystem paths,
temporary files, local environment files, or generated cache artifacts.

## Co-Author Credit

When someone contributes directly to a commit, credit them using a
`Co-authored-by` trailer:

```text
Co-authored-by: <contributor-name> <contributor-email>
```

Confirm the attribution with the contributor and use one trailer for each
co-author. For GitHub to display the credit correctly, use an email address
connected to the contributor’s GitHub account.

## Pull Requests

Open one pull request per topic branch, targeting `main`. The title should
accurately describe the change, and the body should explain what changed, why it
changed, validation results, and reviewer focus areas. Identify source, tests,
migrations, workflows, documentation, and deployment guidance changed by the PR
accurately. Use draft state only while the PR is intentionally not ready for
review, and do not open duplicate PRs for the same branch.

Exclude sensitive values, credential-bearing URLs, contributor email addresses,
and personal filesystem paths from PR text. CI success does not replace review;
it provides shared evidence for the current head commit.

## CI Requirements

The current CI workflow for pull requests to `main` includes:

- PostgreSQL service initialization.
- PostgreSQL connectivity verification.
- Direct Alembic migration validation with `alembic upgrade head` and
  `alembic current --check-heads`.
- Ruff.
- Full pytest suite.
- PostgreSQL migration lifecycle execution.

The PR is not ready to merge while required checks are pending or failing. CI
uses synthetic PostgreSQL credentials; keep them synthetic and avoid exposing
credentials in logs or copied output.

## Reviewer Responsibilities

Reviewers should check that the PR title, body, and diff agree; the scope is
focused; the implementation is correct; tests and assertions cover the risk;
authentication and authorization boundaries remain intact; configuration uses no
real secrets; database and migration changes are safe; fixtures clean up
resources; documentation and links are accurate; CI passed for the current head;
commit attribution is legitimate; and unrelated files or generated artifacts
are absent.

Request changes when evidence is incomplete, the current head has not been
reviewed, CI is failing, migration or authentication impact is unclear, or
rollback implications are not understood.

## Responding to Review

Address each review comment directly and ask for clarification when a request is
ambiguous. Keep corrective changes on the same branch and pull request, rerun
the relevant validation, and update the PR body when validation evidence
changes. Do not resolve review conversations without addressing the concern.
New commits can require fresh review or approval of the current head.

Avoid rewriting shared branch history after review unless a maintainer
explicitly authorizes a metadata-only correction.

## Approval and Merge

Recent project work has used reviewed pull requests into `main` with normal
merge commits. The repository currently does not expose branch protection for
`main`, so approval and merge expectations are project convention unless
maintainers configure enforcement later.

Before merge, maintainers should confirm approval applies to the current PR
head, required checks are successful, requested changes are resolved, scope
matches the PR purpose, and migration or authentication risks are understood.
Use merge steps that protect against a changed head when possible. Contributors
should not self-merge without required approval. Administrative bypass,
auto-merge, squash, and rebase merges are not the observed project workflow.

## Post-Merge Cleanup

After merge, synchronize local `main`, confirm the feature commit is contained
in `main`, and run post-merge validation when appropriate:

```bash
git switch main
git pull --ff-only origin main
git branch --merged main
```

Delete merged topic branches locally and remotely with normal merged-branch
deletion. Preserve intentionally excluded local-only developer files. Do not
begin unrelated work on a completed branch.

## Security and Privacy

Never commit production credentials, API keys, JWT secrets, tokens, database
passwords, credential-bearing URLs, or real secret values. Use placeholders in
documentation and PR bodies. Avoid personal filesystem paths in public text.
Review logs and test output before posting them publicly. Do not place
contributor emails in PR text merely because they appear in commit trailers.

## Stop Conditions

Stop before submission or merge when any of these are true:

- Working tree state is dirty or uncertain.
- Base branch or topic branch is wrong.
- Unexpected files are in scope.
- Ruff, pytest, or whitespace validation failed.
- CI is incomplete, pending, skipped unexpectedly, or failing.
- Migration, authentication, authorization, or configuration changes are not
  reviewed with the right focus.
- Secret handling, credential URLs, logs, or documentation are unsafe.
- PR head differs from the reviewed or approved commit.
- Requested changes remain unresolved.
- Required approval is missing.
- Rollback implications for migration-bearing changes are unclear.

For release-specific gates after approved work is merged, use the
[Release Readiness Checklist](docs/release-readiness-checklist.md).
