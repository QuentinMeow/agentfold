# Pick up the stop-a-merge-from-borrowing-a-claim-across-an-absence task

**Status:** open
**Filed:** 2026-09-04, by claude, from task `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-09-04-stop-a-merge-from-borrowing-a-claim-across-an-absence/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; no current work is blocked.

## What you need to know

`claimed_lifecycle_problem` decides whether a queue item was committed as claimed before it was deleted. On a linear history it stops at the item's absence, so a claim from an earlier incarnation cannot justify a later deletion; at a merge it accepts a claim from any parent, so a claim reachable only through a parent that never carried the deleted incarnation can be borrowed across an absence boundary. This is an ordinary-path defect shared by every caller, found during the 2026-09-04 design review of the restack repair and deliberately left out of that task.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
