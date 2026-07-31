# Pick up the unresolved-human-action projection task

**Status:** open
**Filed:** 2026-07-30, by claude, from chat — the owner reported the repeated ask
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-project-only-unresolved-human-actions/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; handovers and chat replies keep repeating human actions their owner has already answered.

## What you need to know

The reconciler selects the human actions a handover must project by path alone, so an item
an agent has already claimed and folded reads exactly like one nobody has touched. This
task makes that selection state-aware without changing any already-committed record.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
