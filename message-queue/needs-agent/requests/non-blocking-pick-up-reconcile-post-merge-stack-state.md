# Pick up post-merge stack reconciliation

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-reconcile-post-merge-stack-state`
**Action:** Claim the post-merge stack reconciliation task, align its durable queue and task state with exact GitHub evidence, and clean source branches only after their tips reach main.
**Full context:** `tasks/0_backlog/2026-07-24-reconcile-post-merge-stack-state/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-24-reconcile-post-merge-stack-state/worklog.md`
**Request kind:** task-pickup
**If unanswered:** The consolidation branch preserves the implementation and the observed mismatch remains explicit; no review answer or completed lifecycle transition is inferred.

## What you need to know

PR #7 merged to `main` before PRs #8 and #10 were merged into PR #7's still-existing
head branch. The consolidation branch joins those later descendants onto the latest
`main`, but several queue items and task records still describe their publication or
review boundaries as pending. PR #5 was explicitly closed as rejected core scope and
superseded by PR #6, so its branch is audit history rather than missing main-bound work.

## Done when

The task has a claimant, has moved to `1_in-progress`, this request and its `Queue
actions` link have been removed in the claim commit, and the task worklog records exact
post-merge evidence and any branch deletions.
