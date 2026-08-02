# Pick up stopping the merge-ref recompute race

**Status:** open
**Filed:** 2026-08-01, by claude, from task `2026-08-01-stop-human-answers-from-gating-git-edges`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack/task.md`
**Request kind:** task-pickup
**If unanswered:** `review-state-action-projection` keeps failing whenever a parent pull request merges, and it can never become a required check.

## What you need to know

The job compares the candidate revision against the expected one and exits 1 on any
difference. Merging a parent moves its children's base, GitHub recomputes
`refs/pull/N/merge`, and the two differ until it finishes — so the check fails on the
single most ordinary event in a stack.

This is the named prerequisite in the decision item that recommends requiring only
`reconcile-and-test` today.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
