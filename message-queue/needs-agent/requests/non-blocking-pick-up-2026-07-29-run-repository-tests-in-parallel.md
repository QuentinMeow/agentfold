# Pick up Run repository tests in parallel shards on the available cores

**Status:** open
**Filed:** 2026-07-29, by claude, from `docs/designs/fast-local-test-feedback.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-29-run-repository-tests-in-parallel/task.md`
**Request kind:** task-pickup
**If unanswered:** The measured improvement stays unmerged and every commit keeps paying the recorded 219-225s gate.

## What you need to know

The pre-commit gate was measured at 219.16s, and 231.54s for a two-line change. The suite is
`fork`/`exec`-bound: 13,261 Git subprocess calls per full run, with 92-93% of wall time inside
them. The design linked above records the measurements, the approaches compared, and what was
ruled out by measurement rather than opinion.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this request
and its reciprocal `Queue actions` link have been removed in the claim commit.
