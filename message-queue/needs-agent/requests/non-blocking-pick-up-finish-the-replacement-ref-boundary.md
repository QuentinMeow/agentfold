# Pick up finishing the replacement-ref boundary

**Status:** open
**Filed:** 2026-07-31, by claude, from a branch-cleanup audit that found the boundary half-built — `docs/designs/queue-resolution-order-independence.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-31-finish-the-replacement-ref-boundary/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; the reconciler keeps reading its cached objects through a bare `git cat-file --batch`, and the regression tests that would stop the gap reopening stay on an unmerged branch.

## What you need to know

`main` hardened 39 Git invocations with `--no-replace-objects` but left the
`git cat-file --batch` reader bare — the single reader every cached object read was later
routed through, so the newest performance work funnels through the one unhardened site.
`git cat-file -t`, which validates a Git review target's type, is bare too.

The fix already exists, written and tested, on an unmerged branch whose headline rule was
rejected by measurement. Porting the boundary work lets that branch be retired without
losing it. The task file names each function and both regression sets, and states plainly
which parts must not be ported.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
