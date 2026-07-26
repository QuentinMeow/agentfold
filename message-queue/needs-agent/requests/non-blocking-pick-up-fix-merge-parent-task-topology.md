# Pick up the merge-parent task-topology repair

**Status:** open
**Filed:** 2026-07-25, by claude, from task `2026-07-25-fix-merge-parent-task-topology`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-25-fix-merge-parent-task-topology/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; the false `task-admission` finding keeps firing on merges of branches cut before a task existed.

## What you need to know

`task_topology_problems` in `automation/reconcile/reconcile.py` evaluates every
parent/candidate pair as one linear lifecycle step. On a merge whose incoming branch was
cut before a task was filed, the edge from that branch sees the task absent on the parent
side and present in a non-backlog status on the merge side, so it reports a creation that
never happened. The task's real lifecycle is validated on the merge's other parent.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
