# Pick up staged-merge provenance admission

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-complete-staged-merge-provenance-admission`
**Action:** After the publication stack has received human review, claim the staged-merge provenance task, finish the remaining handover creation-edge admission, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-24-complete-staged-merge-provenance-admission/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-24-complete-staged-merge-provenance-admission/worklog.md`
**Request kind:** task-pickup
**If unanswered:** The incomplete implementation remains preserved in its draft PR and the task stays unclaimed; no current review or merge is silently treated as complete.

## What you need to know

The publication audit closed queue-response rollback, deletion provenance,
cache-isolation, unrelated-root task admission, and live handover-incarnation cases.
It then found one remaining invariant class: creation checks are still selected from
the final path set, so a governed handover add followed by deletion, or one of two
byte-identical parallel additions, can escape exact creation-snapshot validation.

## Done when

The task has a claimant, has moved to `1_in-progress`, this request and its `Queue
actions` link have been removed in the claim commit, and the remaining audit reproducers
are recorded in the task worklog.
