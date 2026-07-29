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
two generated timing journals remained deliberately unstaged. Test-only bridge commits
`8cd250c` and `84c4a90` admitted the exact repaired generation across the trusted base floor.
Candidate `d9d630b3…` then passed the explicit final gate with 18 selected files and no deferred
or incomplete coverage, and the unchanged normal hook reused its full receipt before creating
product commit `d966c19`.

The following five-reviewer panel found five more valid blockers: overly broad reversible path
ownership, repository-local Git identity outside receipt inputs, lost policy facts on a static
post-policy timeout, overwrite-prone concurrent budget-task filing, and quote-specific service
ownership. The current repair narrows the policy, fixes and binds isolated Git identity, retains
validated policy and candidate facts in static timeout claims, publishes canonical pairs
exclusively without later pathname deletion, and configures generic service dependencies.

Three pre-final rereviews found and repaired five more defects: the dependency key needed a
trusted parser floor; safe Git identity variables were filtered before the bound component
environment; rollback still had pathname races; static duration used the maximum rather than an
observation; and static stdout could block. Exact dual-generation bridges `5397fc5` and
`68af0e4` landed first. Two exact parser-floor attempts failed honestly on the bridge gaps; the
third passed candidate `c122a31f…` in 442.08 seconds, and normal hook reuse created `236b90d`
in 17.29 seconds. The remaining repair passes 28 filer tests, 41 deadline tests, and 42 exact
configuration/generation tests. Its expanded focused set, exact final gate, normal commit, and a
fresh no-blocker panel remain required before this retry can be resolved.

The six-file compatibility bridge passed exact candidate `bb4a6cef…` and landed as `01a58fd`
through receipt reuse. The complete repair then passed exact candidate `677e74a3…`; after the
final invocation reproduced Git's author-only hook environment, the normal hook reused that
receipt in 13.78 seconds and created product commit `962cca3`. No hook was bypassed. A fresh
five-reviewer revision-bound panel with no valid blocker is now the sole remaining requirement
before this retry can be deleted and the task moved to review.

The first post-product panel approved correctness/cache but found valid blockers in canonical
journal inode safety and mutation truth, root-contract risk classification, configured dependency
validation, and the new-project baseline/install sequence. Its restricted-process-table result
was expected fail-closed behavior and did not authorize weaker cleanup claims. The valid blockers
are repaired; exact dual-generation bridge `63b12b7` passed candidate `477ebfb0…` and reused its
receipt normally. The combined product repair, its exact final gate and commit, and a completely
fresh no-blocker panel remain required.

The combined repair's immutable staged tree `ed3650f6…` passed exact final candidate
`6b159196…` in 309.88 seconds with all 19 files selected and none deferred or incomplete. The
unchanged normal hook reused the full receipt in 13.94 seconds and created product commit
`d513a70d0d18538fc0e5fd32946f2efd0a59945f`; no hook was bypassed. A completely fresh
five-reviewer revision-bound panel with no valid blocker is now the sole condition for resolving
this retry and moving the task to review.
