# Pick up migrating the Review verdicts heading

**Status:** open
**Filed:** 2026-08-07, by claude, from task `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`
**Request kind:** task-pickup
**Action:** claim `tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading` and rename the nineteen older `## Review verdicts` headings to the exact spelling
**Full context:** `tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/task.md`
**Resolution evidence:** `tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/verification.md`
**If unanswered:** the nineteen records keep the older heading; nothing fails until a review is actually run against one of them, and then the receipt is refused with a message naming the spelling it found.

## What you need to know

The review-receipt parser now requires an exact `## Review verdicts` heading. Nineteen
tracked verification records still carry `## Review verdicts (when a review was explicitly
run)`, four of them live `**Repository scope:** core` tasks that will be the first
`--require-review` consumers.

A repo-wide rename is the trap. The review-receipt task's own record already carries both
spellings, so renaming there would give it two exact headings and collapse the receipt it
already holds. The task file states the safe handling.

## Done when

Every tracked verification record carries the exact heading or no heading at all, no record
carries two, and the full suite plus `reconcile.py --check` pass with real output recorded.
