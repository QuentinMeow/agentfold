# Pick up the review-verdict action-classification repair

**Status:** open
**Filed:** 2026-08-04, by codex, from task `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`
**Action:** Claim the review-verdict action-classification task and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/task.md`
**Request kind:** task-pickup
**If unanswered:** Formal revision-bound core reviews remain impossible to record without a false human-action finding.

## What you need to know

The review parser and task-action parser disagree about the repository's canonical verdict
syntax. The repair must preserve scanning of the verdict's finding text so a real human ask
cannot hide inside a review receipt.

## Done when

The task has one claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal task link have been removed in the claim commit.
