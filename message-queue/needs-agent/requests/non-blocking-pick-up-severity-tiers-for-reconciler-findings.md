# Pick up the reconciler severity-tiers task

**Status:** open
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-22-severity-tiers-for-reconciler-findings/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; no current work is blocked.

## What you need to know

This task separates structural reconciler failures from advisory age and maintenance
findings so eventual consistency cannot lock the repository.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
