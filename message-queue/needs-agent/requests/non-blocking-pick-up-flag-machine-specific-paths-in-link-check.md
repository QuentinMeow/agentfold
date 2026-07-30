# Pick up flagging backticked absolute paths in the link check

**Status:** open
**Filed:** 2026-07-30, by claude, from the second CI failure of this shape in two days
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-flag-machine-specific-paths-in-link-check/task.md`
**Request kind:** task-pickup
**Resolution evidence:** `tasks/0_backlog/2026-07-30-flag-machine-specific-paths-in-link-check/task.md`

**If unanswered:** Records keep passing the local gate and failing the pushed one whenever they name an absolute path, and the author learns about it only from a red run.

## What you need to know

The relevant code is the link check's outside-the-repository fallback: when
`relative_to` raises for a candidate, existence is decided by a live probe of the host
filesystem instead of the repository, and that probe is the only part of the check whose
answer differs between machines.

The repair is small and local to that fallback. The surrounding structure already
separates root-relative from file-relative resolution, and the absolute case can be
decided before either is attempted, since an absolute path can never be a repository
link.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
