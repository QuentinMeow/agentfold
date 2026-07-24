# Pick up trusted-check bootstrap and hermetic link validation

**Status:** open
**Filed:** 2026-07-23, by codex, from task `2026-07-23-bootstrap-new-trusted-ci-checks`
**Action:** After the parent change's first human review is recorded, claim the trusted-check bootstrap task and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-23-bootstrap-new-trusted-ci-checks/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; PR #7 keeps its recorded failing checks and no fix is implied.

## What you need to know

One trusted-base job checks out main and then invokes a collector that exists only on
the candidate branch; copying or executing that candidate collector would break the
trust boundary. A separate check treated a developer-local executable path recorded in
the worklog as a repository link, so local existence hid the CI failure.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
