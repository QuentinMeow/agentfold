# Pick up the action-projection Git read batching task

**Status:** open
**Filed:** 2026-07-30, by claude, from task `2026-07-30-write-fixture-git-objects-in-process`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-batch-action-projection-git-reads/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; no current work is blocked.

## What you need to know

The action-projection gate reads the index once per inspected path. Measurement over its
own test module attributes 1,288 of 1,496 Git spawns to that helper, which makes the
module the second most expensive file in the suite.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
