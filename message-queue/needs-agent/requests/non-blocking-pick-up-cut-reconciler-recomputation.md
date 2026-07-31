# Pick up the reconciler recomputation cut

**Status:** open
**Filed:** 2026-07-31, by claude, from task `2026-07-31-cut-reconciler-recomputation`
**Action:** Claim the reconciler recomputation task and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-31-cut-reconciler-recomputation/task.md`
**Request kind:** task-pickup
**If unanswered:** The task stays unclaimed in backlog and the reconciler keeps its current wall time; no measurement or behaviour claim is implied.

## What you need to know

Git object-read caching already landed, so the remaining cost is pure recomputation rather
than object reads: the same Markdown text is re-parsed per admitted edge, single-path index
questions scan the whole index, and one governed edge walk re-asks Git for the same parents
once per consumer. The acceptance bar is behaviour parity, so whoever claims this needs a
differential harness that runs the old and new reconciler against one working tree and diffs
the finding lists.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
