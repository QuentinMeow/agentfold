# Pick up the queue machine-record fold

**Status:** open
**Filed:** 2026-08-18, by claude, from chat
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** [backlog task](tasks/0_backlog/2026-08-18-fold-the-queue-machine-record/task.md)
**Resolution evidence:** `tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record/task.md`
**If unanswered:** New human queue items keep printing ten to fifteen bookkeeping lines under the answer line, which is the status quo; nothing stops and no live item changes.
**Request kind:** task-pickup

## What you need to know

Every question an agent files the owner ends with a block of labelled machine fields sitting
under the line he answers on. On a narrow screen that block is taller than the question, so
the ask arrives buried in paths and checksums. The proposed repair collapses it into one
`<details>` fold in the three `needs-human` templates and adds the checks that make the new
shape safe to write, without touching a single live item: folding a live one changes its
action identity, and the resolution gate refuses that.

## Done when

The backlog task is claimed, moved to `1_in-progress` with its `Claimed-by` set and its
`plan.md` and `worklog.md` added, and this request is deleted in that same coordination
commit.
