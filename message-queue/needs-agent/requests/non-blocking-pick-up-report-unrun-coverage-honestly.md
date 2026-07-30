# Pick up making an empty selection report in the same parseable shape as any other run

**Status:** open
**Filed:** 2026-07-30, by claude, from `memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-report-unrun-coverage-honestly/task.md`
**Request kind:** task-pickup
**Resolution evidence:** `tasks/0_backlog/2026-07-30-report-unrun-coverage-honestly/task.md`

**If unanswered:** A run that selects nothing keeps returning success without a summary line, which stays readable to a person and unparseable to anything else.

## What you need to know

Every run that selects at least one test file prints `tests: N/M files passed`, and every
verification record in this repository transcribes that line as its evidence. The
empty-selection path returns success without printing it, so a gate that correctly proved
there was nothing to run looks the same as a gate that died before summarizing.

This is the part of experiment exp/c-tiered worth keeping. That branch's central rule
was rejected because it would have converted eleven fail-closed selector branches into an
empty selection, but its reporting instinct was sound. Two smaller gaps travel with it:
the skipped-file report names what did not run without naming where that coverage
happens, and the inert-probe test still calls the runner function that was renamed when
the Git shell wrapper was removed, so `AGENTFOLD_INERT_PROBE=1` raises `AttributeError`.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
