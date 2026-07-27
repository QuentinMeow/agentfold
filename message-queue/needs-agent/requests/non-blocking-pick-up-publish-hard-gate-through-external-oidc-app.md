# Pick up the external OIDC App publisher task

**Status:** open
**Filed:** 2026-07-27, by codex, from task `2026-07-27-publish-hard-gate-through-external-oidc-app`
**Action:** After the external test-oracle task is done, claim the OIDC App publisher task, create its plan and worklog, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-27-publish-hard-gate-through-external-oidc-app/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-27-publish-hard-gate-through-external-oidc-app/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed; no automatic hard status or provider-enforcement claim is added.

## What you need to know

Publishing must happen outside candidate-controlled Actions and only after an external oracle
has proved controlled completion for the exact candidate. OIDC supplies short-lived identity;
the dedicated App supplies the narrowly scoped status-writing authority.

## Done when

The prerequisite task is complete, this task has a claimant and has moved to `1_in-progress`,
its plan and worklog exist, and this request and reciprocal task link are removed.
