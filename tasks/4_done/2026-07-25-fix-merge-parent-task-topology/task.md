# Stop task-admission from reading a merge parent edge as a lifecycle step

**Claimed-by:** claude
**Filed:** 2026-07-25, by claude, from the CI failure on the push of the pull request 13 merge commit 74b9d0dfd98f13c17124a9b40d955ff9461e0572
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

The `task-admission` topology check reports a false violation on any merge whose
incoming branch was cut before one of the repository's tasks existed. That is the
ordinary shape of parallel task work, so the finding fires routinely and `main` goes red
on a correct merge.

The mechanism is in `automation/reconcile/reconcile.py`. `queue_revision_edges` yields
one parent/candidate pair for **every** parent of a governed candidate, which is right:
other queue and admission checks need per-edge evaluation, and dropping edges would lose
real coverage. `task_topology_problems` then treats each of those pairs as a single
linear lifecycle step. For a merge commit that is wrong on the parent that predates the
task: the task is absent in that parent's tree and present in the merge's tree, so the
`if not prior:` branch concludes the task was created directly in a non-backlog status
and emits `new task:<id> was created directly in <status>`.

The observed instance: merge commit 74b9d0dfd98f13c17124a9b40d955ff9461e0572 has parents
fef828849653ece624ecf5a9d2b92e7416fcf7f1 (the tip of `main`) and
35582c25f00a0c7bd43db69aa9a27b59c6bacf83 (the pull request 13 branch tip, cut from
17c1e16138632fe914e5ee69882eb26e9f4890c7). Task
2026-07-25-fix-handover-projection-code-span-copy was filed in `0_backlog` by
b4c1ec5e9184824404db58b4ba45aa3bbd2bdad6 and claimed into `1_in-progress` by
0456738d3d9f6e45532c32b71f6441e1e3f0551c, both after that cut, so
`git ls-tree -r --name-only 35582c2` carries no record of it. The task's real lifecycle
was correct on the other parent, where the edge sees the same status on both sides and
passes.

The task's own history is what governs its lifecycle, and every parent that carries the
task still supplies an edge that validates the transition, so an edge from a parent that
never saw the task is not a lifecycle step for it at all.

## Acceptance criteria

- [x] `python3 automation/reconcile/reconcile.py --check --range fef828849653ece624ecf5a9d2b92e7416fcf7f1...74b9d0dfd98f13c17124a9b40d955ff9461e0572`
      reports 0 findings and exits 0, with its real output in `verification.md`
- [x] WHEN a task record is absent at one parent of a merge candidate and present at
      another parent of the same merge candidate, THE CHECK SHALL NOT report it as newly
      created in a non-backlog status on the absent parent's edge
- [x] WHEN a task record is newly introduced in a non-backlog status across a
      single-parent edge, THE CHECK SHALL still report
      `new task:<id> was created directly in <status>`
- [x] WHEN no parent of a merge candidate carries a task record and the merge introduces
      it in a non-backlog status, THE CHECK SHALL still report that finding
- [ ] WHEN one parent of a merge candidate carries a task in `0_backlog` and the merge
      moves it to `1_in-progress`, THE CHECK SHALL behave exactly as it does today
- [x] The task-id rename rule, the duplicate-incarnation guard, the deletion rule, the
      status-transition table, and the `adopting` escape in the same function are
      unchanged, and a test covers the `adopting` escape across the repair
- [x] `automation/tests/test_reconcile_queue.py` gains tests built on real merge commits,
      each recorded in `verification.md` with the verdict it produced before the repair,
      so the discriminating ones are identifiable
- [x] `python3 automation/reconcile/reconcile.py --check` exits 0 and
      `python3 automation/run_tests.py` passes, with both outputs in `verification.md`
- [x] `design.md` states which of the two candidate shapes was chosen, what the rejected
      shape would do to each of the three preserved cases, and carries a complete
      `## Core fit` receipt

**One criterion stays unchecked, and not because the work is missing.** The
`0_backlog`-to-`1_in-progress` merge advance did *not* behave before the repair the way it
behaves now: `verification.md` records
`test_task_admission_accepts_a_merge_claiming_a_backlog_task` as FAIL against the pre-fix
checker and ok after it, so that legal advance was being reported as a false creation too
and the repair fixed a second false positive rather than preserving existing behaviour.
The transition table still governs the case — `still_rejects_an_illegal_merge_advance`
proves an illegal jump survives the suppression — so the intent behind the criterion holds
even though its literal wording does not.

## Links

- The check and both functions involved: `automation/reconcile/reconcile.py`
- Lifecycle topology contract the check enforces: `tasks/AGENTS.md`
- Rule that `main` stays green: `handbook/git-workflow.md`
- Tests for the same check: `automation/tests/test_reconcile_queue.py`
