# Pick up the layered cross-zone operation planner task

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After `2026-07-24-declare-layered-workspace-manifest` is done, claim the cross-zone planner task, create its plan and worklog, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-24-route-layered-cross-zone-operations/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-24-route-layered-cross-zone-operations/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed; cross-zone operations remain manual and no automated deletion or declassification is introduced.

## What you need to know

This is a reversible planning slice, not a file-operation engine. It should make gates
and rollback explicit while leaving destructive, declassifying, and publication
authority outside the implementation.

## Done when

The prerequisite is done, the task has a claimant and has moved to `1_in-progress`,
its plan and worklog exist, and this request and its reciprocal task link are removed.
