# Pick up binding task-branch pushes to observed tips

**Status:** open
**Filed:** 2026-08-03, by codex, from task `2026-08-03-bind-task-branch-pushes-to-observed-tips`
**Action:** Claim the explicit-lease task and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-03-bind-task-branch-pushes-to-observed-tips/task.md`
**Request kind:** task-pickup
**If unanswered:** A stale worker can still rely on a sibling-refreshed tracking ref and overwrite an intervening task-branch update with bare `--force-with-lease`.

## What you need to know

The audit reproduced the overwrite against a disposable remote and confirmed an explicit
expected object ID rejects the same stale publication.

## Done when

The task has one claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal task link have been removed in the claim commit.
