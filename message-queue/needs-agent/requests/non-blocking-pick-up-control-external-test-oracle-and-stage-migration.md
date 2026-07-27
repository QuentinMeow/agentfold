# Pick up the external test-oracle and migration task

**Status:** open
**Filed:** 2026-07-27, by codex, from task `2026-07-27-control-external-test-oracle-and-stage-migration`
**Action:** Claim the external test-oracle task, create its plan and worklog, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-27-control-external-test-oracle-and-stage-migration/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-27-control-external-test-oracle-and-stage-migration/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed; automatic final transitions and provider-hard execution stay unavailable.

## What you need to know

The current base-pinned floor stops test deletion but still trusts the candidate interpreter's
return code. This task must establish externally observed completion before any automatic gate
can consume that evidence.

## Done when

The task has a claimant, has moved to `1_in-progress`, its plan and worklog exist, and this
request and its reciprocal task link have been removed in the claim commit.
