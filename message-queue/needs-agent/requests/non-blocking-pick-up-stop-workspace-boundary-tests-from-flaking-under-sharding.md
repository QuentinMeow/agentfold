# Pick up the workspace-boundary test flakiness repair

**Status:** open
**Filed:** 2026-08-16, by claude, from task `2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** [backlog task](tasks/0_backlog/2026-08-16-stop-workspace-boundary-tests-from-flaking-under-sharding/task.md)
**Resolution evidence:** `tasks/1_in-progress/2026-08-16-stop-workspace-boundary-tests-from-flaking-under-sharding/task.md`
**If unanswered:** The full suite keeps failing intermittently on one module; every other gate still runs, and a re-run passes, so nothing stops.
**Request kind:** task-pickup

## What you need to know

One full-suite run reported `automation/tests/test_inspect_workspace_boundaries.py` failing
while the same module passed standalone and on the immediate re-run. The module reads
Git-metadata topology and worktree cleanliness, which the sharded runner shares across
workers, so the contention is the likely cause rather than the assertions.

## Done when

The backlog task is claimed, moved to `1_in-progress` with its `Claimed-by` set, and this
request is deleted in that same coordination commit.
