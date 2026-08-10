# Maintainer Guide

## Purpose

Maintainer guidance works best when decisions remain grounded in practical 
repository evidence rather than assumptions about contributor intent.
This guide records how `sre-runbook-api` is stewarded and how maintainers
evaluate, review, merge, document, and preserve changes. It complements
[CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
[ROADMAP.md](ROADMAP.md), and the repository [licence](LICENSE). Those
documents remain the source for contributor workflow, conduct expectations,
project direction, and licence terms.

The guide is practical repository guidance. It does not by itself grant GitHub
permissions, enforce branch rules, or create support commitments.

## Project Roles

### Project Owner and Maintainer

Stewardship in this role benefits from consistent attention to how changes 
affect long-term maintainability and contributor experience.
Franklin Ajero (`@Franklindot04`) is the Project Owner and Maintainer.
Repository-owner responsibilities include project direction, administrative
GitHub settings, access and permission decisions, merge-policy decisions,
release and tag decisions, final scope decisions, repository archival or
transfer decisions, and security-sensitive administrative action.

Technical decisions should still be grounded in review evidence, validation,
and repository scope. Owner authority is the final responsibility for
repository administration and scope, not a substitute for technical reasoning.

### Co-Author and Reviewer

Review contributions in this role often help maintain clarity and consistency 
across changes without altering administrative boundaries.
Ellesmaris (`@ellesmaris`) is a Co-Author and Reviewer. This role may include
contributing to shared changes, reviewing pull requests, checking scope and
clarity, validating documentation and implementation reasoning, and approving
changes when review requirements are met.

This role is not described here as repository administration unless GitHub
permissions and repository evidence support that separately.

### Contributors

Effective contribution often comes from presenting changes in a way that 
helps reviewers understand intent without needing extensive back-and-forth.
Contributors may propose focused changes through issues and pull requests.
They are responsible for explaining the change, keeping scope tight, providing
evidence and validation, updating documentation when needed, protecting
sensitive information, and responding to review.

## Maintainer Responsibilities

Responsible engineering stewardship requires understanding how each change 
affects long-term system stability and the workflows of other contributors.
Maintainers should keep `main` stable, preserve repository scope, review
changes for correctness and maintainability, protect sensitive information, and
keep documentation aligned with implementation. They should assess
compatibility and migration risk, maintain useful validation, keep roadmap
statements accurate, and avoid merging incomplete or misleading work.

Stewardship also includes removing stale or contradictory guidance when it is
proven wrong and keeping governance documents mutually consistent.

## Decision-Making

Clear decision-making often benefits from separating operational facts 
from preference-driven arguments so reviewers can focus on measurable impact.
Decisions should be based on repository scope, operational value, security
impact, reliability impact, maintenance burden, migration risk, backward
compatibility, testability, documentation quality, and evidence from
implementation and validation.

Significant disagreements should be resolved through documented technical
reasoning rather than authority alone where practical. The project owner
retains responsibility for final repository-administration and scope decisions.

## Issue Triage

Effective triage often depends on distinguishing actionable reports from 
exploratory questions so review effort stays focused where it adds the most value.
Maintainers should confirm whether an issue is within repository scope, separate
defects from support questions and enhancement proposals, and request
reproduction steps or evidence when needed. Security-sensitive reports should
not remain public when a private GitHub-supported or maintainer-approved path
is available.

When repository tooling supports it, issues may be labeled or categorized.
Duplicates, invalid reports, and out-of-scope requests should be closed with a
clear explanation. Avoid promising implementation dates.

## Pull-Request Review

Good reviews often emerge when changes are evaluated in terms of
how they influence operational clarity and long-term maintainability.
Review should consider focused scope, correctness, tests, migrations,
compatibility, security, error behavior, documentation, CI results, privacy,
maintainability, and rollback or downgrade implications where relevant.

Reviewers may request clearer evidence, smaller scope, additional tests,
migration changes, documentation updates, or safer handling of configuration
and sensitive data. Feedback should stay focused on the work rather than the
contributor.

## Authorship and Review Credit

Clear attribution helps maintain an accurate record of how changes were shaped and who contributed meaningful review effort.
Use co-author attribution when a commit genuinely represents shared authorship.
Reviews, approvals, comments, and acknowledgements should reflect the type of
contribution made.

## Merge Standards

Project work should use focused branches and pull requests into `main`.
Successful validation is required before merge, and approval should apply to
the current pull-request head. Avoid merging stale commits or commits changed
after approval without renewed review.

Recent repository history uses normal merge commits to preserve project
history. Do not bypass required checks casually, resolve review conversations
before merging, verify the merge result, synchronize local `main`, and delete
merged feature branches safely. Do not force-delete unmerged work.

These are documented workflow expectations unless matching GitHub settings have
been verified directly.

## Validation Expectations

Current validation categories include Ruff, pytest, PostgreSQL-backed CI
coverage, direct Alembic validation, migration upgrade and downgrade lifecycle
checks, whitespace validation, documentation-link checks when documentation
changes, and privacy and secret checks for public content.

Actual output is the source of truth for each commit under review. CI passing
does not replace human review.

## Database and Migration Stewardship

Migration files should reflect model changes. Upgrade and downgrade paths
should be considered, and SQLite development behavior and PostgreSQL CI
behavior should remain understood. Destructive or incompatible migration
changes require explicit review.

Schema changes should include tests and documentation where appropriate.
Maintainers should avoid editing applied migration history casually.

## Security and Sensitive Information

Maintainers should prevent credentials and secrets from entering Git history,
avoid publishing private reports or personal information, and move sensitive
security discussions to an available private GitHub-supported or
maintainer-approved channel. Do not claim confidentiality that the repository
cannot guarantee.

Conduct concerns are handled separately from vulnerability handling; see
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for conduct matters. Repository-owner
coordination is required when permissions, settings, or other administrative
controls are involved.

## Documentation Stewardship

Maintainers should keep the README, contribution guidance, Code of Conduct,
NOTICE, roadmap, deployment guidance, release-readiness guidance, API
documentation, and configuration documentation aligned with the implementation.

Documentation changes should be reviewed with the same care as implementation
changes because inaccurate operational guidance can be as damaging as a code
regression.

## Roadmap and Scope Management

Use [ROADMAP.md](ROADMAP.md) as the source for current direction and optional
future work. Completed work should not remain described as unfinished, and
possible future directions should not be presented as promises.

Significant scope expansion should be justified. Roadmap updates should follow
material priority changes, and unrelated technologies should not be added
merely to make the project appear broader.

## Releases and Change Management

Maintainers should assess whether a change requires release notes or a version
decision, keep compatibility effects visible, document migration requirements,
and verify release-readiness checks before a formal release.

Tags or releases should be used only through an intentional owner-approved
process. The repository currently does not define automated release publishing,
generated artifacts, published images, or a formal semantic-versioning policy.
Release publication remains an owner-controlled future decision.

## GitHub Repository Settings

Administrative controls may include branch protection, rulesets, required
checks, review requirements, force-push restrictions, deletion protection,
vulnerability-reporting settings, repository visibility, and collaborator
permissions.

These settings must be verified directly on GitHub and changed only by an
authorized repository administrator. Do not claim a setting is enabled unless
the setting has been verified.

## Continuity and Handover

Maintainers should leave the repository understandable after a pause. Keep
`main` clean and synchronized, record important project state in tracked
documentation, avoid relying only on private notes, document known limitations,
and keep open work clearly separated from completed work.

Avoid leaving abandoned branches or misleading open pull requests. Verify
repository state before resuming work.

## Maintainer Checklist

Before accepting a change:

- Scope is understood.
- Evidence has been reviewed.
- Validation is defined.
- Security and migration impact are considered.
- Documentation impact is considered.

Before merging:

- Current head is reviewed.
- Required checks passed.
- Discussions are resolved.
- Committed files match intended scope.
- Public content contains no sensitive information.

After merging:

- `main` is synchronized.
- Validation is reconfirmed when appropriate.
- Merged branches are cleaned up safely.
- Documentation and roadmap are updated when needed.
- Unresolved follow-up work is recorded clearly.
