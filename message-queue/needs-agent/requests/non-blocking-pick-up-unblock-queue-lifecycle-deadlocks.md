# Pick up the queue lifecycle deadlock repair

**Status:** open
**Filed:** 2026-07-30, by claude, from an audit of the queue lifecycle checks in `automation/reconcile/reconcile.py`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-unblock-queue-lifecycle-deadlocks/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; a `needs-agent` item claimed before its resolution evidence stays undeletable, and a generated `stale-task` retry keeps blocking every merge after its finding is fixed.

## What you need to know

Both defects are reproduced, not suspected. `claim_identity` freezes `Resolution evidence`
across a committed claim, which closes all three exits for an item claimed before its
evidence was worked out. `stale-task` is emitted by the reconciler but is not a key in
`CHECKS`, so its generated retry escapes garbage collection, survives the fix it describes,
and then blocks every pull request at `transition:merge`. The task file records the exact
functions, line numbers, and observed messages, so no re-derivation is needed.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
