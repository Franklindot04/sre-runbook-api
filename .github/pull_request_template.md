# Pull Request

## Summary

Describe what this pull request changes and why the change is needed.

## Problem or Context

Explain the problem, operational need, defect, or repository concern being
addressed. Use "Not applicable" for small documentation or maintenance changes.

## Scope

Identify what is included, what is intentionally excluded, and whether this
change is focused or depends on follow-up work.

## What Changed

List the main implementation or documentation changes.

## Validation

Record actual validation results for the checks that apply:

- Ruff
- pytest
- CI
- PostgreSQL-backed validation
- Alembic or migration lifecycle checks
- documentation-link validation
- manual verification

Only include checks that are relevant to this pull request. Do not rely on a
permanent test total; use the current output for this commit.

## Database and Migration Impact

Describe whether this change affects database models, Alembic migrations,
upgrade behavior, downgrade behavior, SQLite development behavior, PostgreSQL
behavior, or data compatibility.

Use "No database or migration impact" when appropriate.

## Security and Privacy

Describe whether this change affects authentication, authorization, secrets,
sensitive configuration, personal information, public logs, or public errors.

Do not include credentials, tokens, private reports, personal data, or exploit
details in this pull request.

## Compatibility and Rollback

Describe backward-compatibility effects, breaking changes, rollback
considerations, and downgrade considerations.

Use "Not applicable" when appropriate.

## Documentation

State what documentation was updated, or explain why no documentation change is
needed.

## Review Notes

Call out areas requiring careful review, known limitations, intentional
trade-offs, or follow-up work.

## Checklist

- [ ] Scope is focused.
- [ ] Committed files match the intended change.
- [ ] Validation results are recorded accurately.
- [ ] Tests were added or updated where appropriate.
- [ ] Migration implications were considered.
- [ ] Documentation was updated where appropriate.
- [ ] No credentials or private information were added.
- [ ] Authorship and acknowledgements accurately reflect contributions.
