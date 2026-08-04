# Pick up making linked-worktree bootstrap concurrency-safe

**Status:** open
**Filed:** 2026-08-03, by codex, from task `2026-08-03-make-linked-worktree-bootstrap-concurrency-safe`
**Action:** Claim the bootstrap task and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe/task.md`
**Request kind:** task-pickup
**If unanswered:** Linked worktrees keep requiring manual repair, and concurrent installers may continue failing on the shared Git configuration lock.

## What you need to know

The audit reproduced both missing per-worktree adapters and concurrent `.git/config` lock
failures. The task deliberately excludes optional runtime session hooks.

## Done when

The task has one claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal task link have been removed in the claim commit.
