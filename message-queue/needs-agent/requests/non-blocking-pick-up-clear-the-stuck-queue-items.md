# Pick up the stuck-queue clearing task

**Status:** open
**Filed:** 2026-07-30, by claude, from chat
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-clear-the-stuck-queue-items/task.md`
**Request kind:** task-pickup
**If unanswered:** The four stuck items stay exactly as they are; one agent request stays undeletable, three human reviews stay unanswered, and no current work is blocked.

## What you need to know

The widened `resolution_evidence_problem` admits a deletion whose work landed in an earlier
commit that the repository already attributes to a linked task. Exactly one live item has
that shape. Three others are human merge reviews whose bound Git ranges are already
ancestors of `main`, so no rule change can resolve them and their disposition is not an
agent's to invent.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
