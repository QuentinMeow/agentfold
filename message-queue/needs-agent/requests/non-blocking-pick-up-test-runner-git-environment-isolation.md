# Pick up the test-runner Git-environment isolation task

**Status:** open
**Filed:** 2026-07-24, by codex, from the recovered linked-worktree repair
**Action:** Claim task `2026-07-24-isolate-test-git-environment`, then remove this completed pickup request in the same coordination commit.
**Full context:** [task specification](tasks/0_backlog/2026-07-24-isolate-test-git-environment/task.md)
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog and linked-worktree commit/test operations remain blocked by the separate repair request.

## What you need to know

The task records and focused red regression were preserved only as uncommitted files
after the original linked-worktree incident. They are being admitted through the
current lifecycle before the already-selected repair is recorded.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this pickup request and its
`Queue actions` link have been removed in the same commit.
