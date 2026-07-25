# Pick up the handover projection code-span repair

**Status:** open
**Filed:** 2026-07-25, by claude, from the end-of-session handover of the markdown edge graph Stage 0 work — `docs/designs/markdown-edge-graph.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-25-fix-handover-projection-code-span-copy/task.md`
**Request kind:** task-pickup
**If unanswered:** The task stays unclaimed in backlog and no session can commit a handover, because the live blocking action in the same task is unresolved.

## What you need to know

The handover projection compares a queue item's raw Why-you-might-care and If-you-do-nothing
bytes against handover prose that has had every inline code span blanked, so a field
containing a code span can never be copied into a conforming entry. One live decision item
has three such spans, which blocks the end-of-session ritual repository-wide.

The task file records the exact comparison, the five encodings that were tried and failed,
and the two reasons the queue item cannot be edited or deleted instead, so the repair needs
no re-derivation. The change is in the checker and its tests only.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
