# Pick up the contain-test-temporary-directories task

**Status:** open
**Filed:** 2026-07-30, by claude, from a well-scoped developer-velocity fix requested in chat
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-contain-test-temporary-directories/task.md`
**Request kind:** task-pickup
**If unanswered:** The test runner keeps leaving an interrupted run's fixture Git repositories scattered across the real system temp directory (`history/conversations/2026-07-29-1833PDT-fast-local-test-feedback/handover.md`: "killing leaks them... This session removed 937 leaked directories").

## What you need to know

`automation/run_tests.py` already isolates every run inside one scratch root and points
child `HOME`/`XDG_CONFIG_HOME`/Git identity inside it, but never redirects the child
processes' own `TMPDIR`. Every fixture's `tempfile.mkdtemp()`/`TemporaryDirectory()` call
(no `dir=` anywhere) resolves against the real system temp directory instead, which is
invisible on a completed run (each fixture's own context manager cleans up) but scatters
debris across the real system temp directory when a run is killed — the ordinary way a
developer stops a slow suite mid-development.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
