# Repair the unanimous test-gate merge-review blockers

**Status:** open
**Filed:** 2026-07-28, by codex, from the [current task](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/task.md)
**Action:** Repair all six unanimous-panel findings and rerun the revision-bound merge review.
**Check:** manual
**Subject:** [task.md](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/task.md)
**Resolution evidence:** `tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/verification.md`
**Blocks now:** operation:merge-configurable-test-gates

## Broken invariant

Git range `e530c428..64490ab5` received zero approvals and five blocking verdicts. Merge safety requires all six categories to be repaired together: a trusted pre-import authority guard must complete before candidate imports; execution must use one immutable snapshot and receipts must bind the full executed closure and environment; the obsolete pull-request check context must retire while diagnostic core-scope and merge admission are restored; a reported terminal outcome must be frozen rather than contradicted by later accounting; candidate-only new test namespaces must remain visible to complete coverage; and obsolete human asks must be resolved or withdrawn so they do not misstate the live boundary.

The durable task records are [task.md](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/task.md), [plan.md](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/plan.md), and [verification.md](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/verification.md).

## Fix

Implement and verify the pre-import authority guard; execute and receipt-bind one immutable full-closure/environment snapshot; retire the old pull-request check while restoring diagnostic core-scope and merge admission; freeze terminal reports after final accounting; include candidate-only namespaces in complete coverage; and resolve or withdraw obsolete human asks. Record exact evidence in the linked verification file, then obtain a fresh revision-bound panel before merge.

## Agent notes

Unclaimed. This retry blocks only `operation:merge-configurable-test-gates`; the task remains in progress while repairs proceed.
