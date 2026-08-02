# Pick up judging a handover by its creation grammar

**Status:** open
**Filed:** 2026-08-01, by claude, from a reproduced merge failure on PR #44 and a latent one on `main`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-judge-a-handover-by-its-creation-grammar/task.md`
**Request kind:** task-pickup
**Resolution evidence:** `tasks/1_in-progress/2026-08-01-judge-a-handover-by-its-creation-grammar/worklog.md`
**If unanswered:** PR #44 stays unmergeable, the handover already on `main` keeps failing every future range that contains its creation commit, and each later entry-version bump strands one more branch.

## What you need to know

`handover_action_entry_version_for` returns the highest entry-schema version reachable from the
candidate, so an immutable handover is judged by a grammar that did not exist when it was
written. `Queue action-entry schema: v3` was activated at `03ec388`, withdrawn at `b4c6627`, and
the number was then reused at `219ae1f` for an unrelated label rename, so records written while
the contract said v2 are told to use labels invented later.

The repair keeps the admission-edge ratchet for the rejecting clauses — an agent must not evade a
newer rejection by cutting a branch early — and takes the required suffix spelling from the
marker in the record's own creation snapshot.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this request
and its reciprocal `Queue actions` link have been removed in the claim commit.
