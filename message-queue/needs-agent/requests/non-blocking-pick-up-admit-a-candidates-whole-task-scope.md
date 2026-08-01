# Pick up repairing the two gates that require opposite things

**Status:** open
**Filed:** 2026-08-01, by claude, from six pull requests blocked by contradictory gates — `tasks/0_backlog/2026-08-01-admit-a-candidates-whole-task-scope/task.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-admit-a-candidates-whole-task-scope/task.md`
**Request kind:** task-pickup
**If unanswered:** The task stays unclaimed in backlog; the projection gate keeps refusing every candidate that touches more than one task record with exit 2, and no `transition:*` queue action can be introduced through a merged candidate.

## What you need to know

The reconciler requires a queue item bound to `task:<id>` to be listed in that task's
`Queue actions`, so filing one edits another task's record. The action-projection gate then
refuses the resulting candidate outright because it maps to more than one task scope. Each
gate is enforcing something real; together they leave no legal commit.

The merge-boundary check has the same root: it treats every task whose records a candidate
touched as a task whose merge is happening, so an action the candidate itself files is
judged to have reached a boundary in the range that created it.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
