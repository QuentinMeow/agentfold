# Pick up the honest-check-failure-reporting task

**Status:** open
**Filed:** 2026-07-30, by claude, from a reconciler audit that reproduced four defects
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-report-check-failures-honestly/task.md`
**Resolution evidence:** `tasks/0_backlog/2026-07-30-report-check-failures-honestly/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; the reconciler keeps exiting 1 with no findings on an unreadable file, and staged violations stay hideable.

## What you need to know

The reconciler reports a crashed check as exit 1, the same code it uses for "findings
exist", and discards every finding already found. It also raises `TypeError` on a task
id whose date is impossible, and it hides staged violations whose worktree copy was
deleted. Each defect has a reproduction recorded in the task.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
