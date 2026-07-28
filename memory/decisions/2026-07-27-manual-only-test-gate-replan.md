# Ship manual final verification until independent automatic enforcement exists

**Status:** decided
**Date:** 2026-07-27
**Decided-by:** human (explicit yes recorded in commit `bed486c` and claimed in `a789631`)
**Description:** The starter final gate is manual; automatic hard enforcement stays unavailable until an external test oracle and separately controlled publisher exist
**Review-by:** 2027-01-23
**Supersedes:** `memory/decisions/2026-07-27-trusted-pull-request-gate-boundary.md`

## Context

The proposed automatic pull-request gate used base-pinned tests so a candidate could not delete
the test files that judged it. That was not enough. Those tests still import candidate Python in
their own interpreter, and candidate code can call `os._exit(0)` before the trusted assertions
finish. The resulting zero exit code does not prove that the assertions completed.

The proposed publisher also had no independent way to distinguish that early exit from a
controlled completion. Publishing its result as a required GitHub status could therefore
authorize a merge without trustworthy completion evidence.

## Decision

This task will ship explicit manual final verification. The starter configuration uses
`mode = "manual"` and has no automatic trigger or merge-authorizing publisher.

The configuration language may continue to recognize `hard` so a future repository policy does
not need another syntax migration. In this version, however, every automatic or provider-hard
invocation fails closed because no controlled adapter is available.

Results from the current complete test runner are cooperative evidence. Reports must say that
they come from a same-interpreter process and are not eligible to enforce a merge. They may
inform a maintainer's manual judgment, but they must never be presented as independent proof
that candidate-controlled code allowed all assertions to complete.

Critical scopes remain non-deferrable. Because automatic enforcement is unavailable in this
task, a critical automatic transition stays blocked rather than accepting cooperative evidence
or silently falling back to a weaker check.

Real automatic enforcement is deferred to two ordered tasks:

1. `2026-07-27-control-external-test-oracle-and-stage-migration` must move completion judgment
   into a protected process that never imports candidate bytes.
2. `2026-07-27-publish-hard-gate-through-external-oidc-app` must let a separately controlled
   publisher validate that external evidence before it posts a merge-authorizing status.

## Alternatives considered

- Ship the existing automatic gate — rejected because a candidate can produce a successful
  process exit without proving that trusted assertions completed.
- Leave this task waiting for both external systems — rejected because the routine budget,
  explicit manual final lane, exact cache, and timing-investigation behavior are useful without
  making an automatic-enforcement claim.

## Consequences

This task removes the unsafe automatic publisher, makes manual final verification the starter
behavior, labels complete results honestly, and keeps hard invocations blocked. The earlier
activation request cannot activate the superseded design. Automatic merge enforcement remains
future work and requires both follow-up tasks plus fresh review and provider evidence.
