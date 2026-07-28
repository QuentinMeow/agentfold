# Withdraw the superseded GitHub hard-test-gate activation

**Status:** decided
**Date:** 2026-07-27
**Decided-by:** human (the manual-only replan was authorized in commit `bed486c`)
**Description:** The obsolete GitHub hard-gate activation transition is withdrawn; any future enforcement needs the external oracle and OIDC publisher work
**Review-by:** 2027-01-23

## Context

The activation decision and source-branch clarification were filed before
`memory/decisions/2026-07-27-manual-only-test-gate-replan.md` superseded their design. This
record supplies their predeclared resolution evidence; the manual-only ADR remains the
controlling source.

## Decision

Withdraw `transition:activate-github-hard-pull-request-gate` without activating a GitHub rule.
Any future proposal must follow task `2026-07-27-control-external-test-oracle-and-stage-migration`
and task `2026-07-27-publish-hard-gate-through-external-oidc-app`, with fresh review and provider
evidence.

## Alternatives considered

- Activate the superseded design — rejected by the controlling manual-only ADR.
- Delete the asks without folding them — rejected because it would discard their delivery and
  resolution history.

## Consequences

The two obsolete human asks may close. No automatic hard gate is activated by this resolution.
