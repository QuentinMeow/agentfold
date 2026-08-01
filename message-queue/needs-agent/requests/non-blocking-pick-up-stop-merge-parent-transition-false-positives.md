# Pick up the merge-parent lifecycle-transition repair

**Status:** open
**Filed:** 2026-08-01, by claude, from task `2026-08-01-stop-merge-parent-transition-false-positives`
**Action:** Claim the merge-parent lifecycle-transition task, move it to `1_in-progress`, and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-stop-merge-parent-transition-false-positives/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-08-01-stop-merge-parent-transition-false-positives/task.md`
**Request kind:** task-pickup
**If unanswered:** The task stays unclaimed in backlog. Merging `main` into a branch keeps reporting a `task-admission` lifecycle jump about `main`'s own governed history, so branches catch up with the trunk only by suppressing a red check.

## What you need to know

`task_topology_problems` reads every merge-parent edge as one linear lifecycle step. The
creation half of that defect was repaired by task
`2026-07-25-fix-merge-parent-task-topology`; the transition half is still open, and it
fires on `main` itself as soon as a `MERGE_HEAD` exists.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
