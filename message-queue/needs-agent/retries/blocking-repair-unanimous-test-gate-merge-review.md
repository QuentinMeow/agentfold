# Repair the unanimous test-gate merge-review blockers

**Status:** in-repair
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

Claimed in commit `43b627e`; status remains `in-repair`. The six findings from the original
0-approve/5-block panel were repaired, and product commit
`3a342013063f37516b8f65e707e26e4f0c655e0a` received a fresh 3-approve/2-block review. That
review still found one P1 product flaw: potentially unbounded Git discovery, candidate
materialization, and controller planning can run before the configured absolute deadline exists.
It also found the durable records stale and the original final report/stdout unavailable after
the fixed report path was overwritten. The records now state the surviving evidence and loss
plainly, but the P1 requires a product repair, another exact final run, a commit, and another
fresh revision-bound panel. This retry continues to block only
`operation:merge-configurable-test-gates`; the task remains in progress while repair proceeds.

The absolute-deadline repair, exact full-receipt reuse for reversible routine work, and separate
execution, cleanup, validation, and terminal-delivery cutoffs are now implemented in the task
worktree. Independent focused verification passed 34 deadline-protocol tests, 103 gate tests
with one existing skip, 28 configuration tests, 6 generation tests, compilation, diff checks,
and reconciliation with zero findings. A focused adversarial rereview returned `APPROVE`.
These results are not the final merge review. The complete intended candidate is now staged; the
two generated timing journals remain deliberately unstaged. The next agent should verify that
split without changing staged bytes, run one exact explicit final gate, and commit normally so
the routine hook proves receipt reuse. A fresh five-reviewer panel over that committed revision
is still required before this retry can be resolved.
