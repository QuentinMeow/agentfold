# Pick up the repair for a queue item whose evidence already merged

**Status:** open
**Filed:** 2026-07-26, by claude, from the coordination session that claimed and then could not resolve the handover code-span repair — `handbook/git-workflow.md`
**Action:** Claim the backlog task 2026-07-26-resolve-queue-items-whose-evidence-already-merged and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-26-resolve-queue-items-whose-evidence-already-merged/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog. One `needs-agent` request stays live at `in-repair` declaring a blocker its merged repair already cleared, and one task stays at `1_in-progress` because it cannot reach `Queue actions: none`.

## What you need to know

The deletion half of the `queue-resolution` check requires an item's predeclared resolution
evidence to change in the deletion commit itself. An item whose work merged before its claim
edge was committed therefore has no honest resolving commit available, because the evidence
file already holds the repair and cannot change again.

That state is live on `main`, not hypothetical. The task record carries the measured defect
with line numbers, the two existing escapes that do not reach an ordinary request, and
fail-closed criteria for the repair. `automation/` is core, so the claiming session also owes
the substitution receipt in `design.md`.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
