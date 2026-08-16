# Pick up the withdrawn-exemption edge repair

**Status:** open
**Filed:** 2026-08-08, by claude, from task `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** [backlog task](tasks/0_backlog/2026-08-08-stop-a-withdrawn-exemption-from-dirtying-past-edges/task.md)
**Resolution evidence:** `tasks/1_in-progress/2026-08-08-stop-a-withdrawn-exemption-from-dirtying-past-edges/task.md`
**If unanswered:** The merge-transition check keeps reporting findings from historical edges whose exemption was later withdrawn; branch heads stay clean and the merge gate stays advisory, so nothing stops.
**Request kind:** task-pickup

## What you need to know

`task-action-origin` judges each commit edge on that commit's own bytes, so withdrawing a
parser exemption retroactively dirties every historical edge that relied on it. The
review-receipt branch reached this state: its head is clean, two intermediate commits are
not, and no head-side edit can repair them. The merge gate is advisory, so this reports
rather than stops anything.

## Done when

The backlog task is claimed, moved to `1_in-progress` with its `Claimed-by` set, and this
request is deleted in that same coordination commit.
