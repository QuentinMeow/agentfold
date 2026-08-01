# Stop task-admission from reading a merge parent edge as a lifecycle transition

**Claimed-by:** unclaimed
**Filed:** 2026-08-01, by claude, from the reconciler failure reproduced by merging `origin/main` (8811770) into `origin/task/2026-07-31-finish-the-replacement-ref-boundary`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-merge-parent-transition-false-positives.md`

## Goal

`origin/main` looks green on its own, because with no `MERGE_HEAD` the reconciler never
re-walks history. Merge `main` into any live branch and `task-admission` reports a
lifecycle violation about `main`'s own already-governed history, so every branch that
needs to catch up with the trunk is blocked.

The mechanism is the transition half of the defect that
task:2026-07-25-fix-merge-parent-task-topology already repaired for task
*creations*. `queue_revision_edges` yields one parent/candidate pair for **every** parent
of a governed candidate, which is right — `queue-resolution`, `queue-boundary`,
`task-action-origin`, and the handover checks all need per-edge evaluation.
`task_topology_problems` then reads each pair as a single linear lifecycle step. On a
merge commit that is wrong for the parent whose lineage did not take the step: the task
sits at its old status in that parent's tree and at the incoming branch's status in the
merge's tree, so the transition table sees one jump where the incoming lineage actually
took two properly governed edges.

The observed instance: PR #41's merge commit `84e3524ef36c8aed5734c48248131f6c2b397ce8`
has parents `7c2854a1fb3a885423f080f3957d76f132b32b27` (the trunk tip, which records
task:2026-07-25-fix-handover-projection-code-span-copy at `1_in-progress`) and
`ed3a9ee2d9314cd5dde59348eca1b7e02ccdfe43` (the branch tip, which records the same task
at `4_done`). The branch reached `4_done` through two governed commits, `07de276`
(`1_in-progress → 3_in-review`) and `6de7954` (`3_in-review → 4_done`). Viewed from the
trunk-side parent alone, that reads as an illegal `1_in-progress → 4_done` jump. The
`--check` run on the merged tree reports it twice, once for the historical snapshot and
once for the staged candidate.

The task's own history is what governs its lifecycle, and the parent that already sat at
the resulting status reached it through its own governed edges — which
`queue_revision_edges` yields for the same candidate — so an edge from a parent whose
lineage did not take that step is not a lifecycle step for that task at all.

## Acceptance criteria

- [ ] The reproduction transcript of the pre-fix failure, taken with the exact commands
      that produced it, is recorded in `verification.md`
- [ ] WHEN a merge candidate holds a task at a status that another parent of the same
      candidate already held, THE CHECK SHALL NOT report a lifecycle jump on the parent
      whose lineage did not take that step
- [ ] WHEN a merge candidate advances a task to a status no parent held, THE CHECK SHALL
      still report `task:<id> jumped from <prior> to <status>`
- [ ] WHEN a lifecycle jump crosses a single-parent edge, THE CHECK SHALL behave exactly
      as it does today
- [ ] The suppression matches on the exact status, not merely on the task being recorded
      at a sibling parent — proved by a test that fails against the weaker shape
- [ ] The task-id rename rule, the duplicate-incarnation guard, the deletion rule, the
      creation rule, and the `adopting` escape in the same function are unchanged
- [ ] Every new test in `automation/tests/test_reconcile_queue.py` is recorded in
      `verification.md` with the verdict it produced before the repair, so the
      discriminating ones are identifiable
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 blocking findings and
      `python3 automation/run_tests.py` passes 11/11 files, both with real output in
      `verification.md`
- [ ] The merge probe that reproduced the defect reports no `task-admission` finding after
      the repair, with its real output in `verification.md`
- [ ] `design.md` states which shape was chosen, what the rejected shapes do to each
      preserved case, and carries a complete `## Core fit` receipt

## Links

- The check and both functions involved: `automation/reconcile/reconcile.py`
- The creation half of the same repair: task `2026-07-25-fix-merge-parent-task-topology`
- Lifecycle topology contract the check enforces: `tasks/AGENTS.md`
- Rule that `main` stays mergeable: `handbook/git-workflow.md`
- Tests for the same check: `automation/tests/test_reconcile_queue.py`
