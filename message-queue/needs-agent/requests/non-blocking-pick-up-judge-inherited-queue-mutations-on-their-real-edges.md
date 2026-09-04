# Pick up the judge-inherited-queue-mutations-on-their-real-edges task

**Status:** open
**Filed:** 2026-09-04, by claude, from task `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-09-04-judge-inherited-queue-mutations-on-their-real-edges/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; no current work is blocked.

## What you need to know

The reconciler's displaced-tip check now explains an inherited queue *deletion* from the merge base and validates the real deletion edge, but the sibling *mutation* stream on the same synthetic old-tip-to-new-head edge is still a raw two-tree diff. A base-side identity change that the base's own gate admitted with edge context (a claim edge, a folded human answer, a sanctioned migration) can therefore still be attributed to a restacked branch as a rewritten live action. The same discriminator the deletion path uses closes the gap: one merge base, an old-tip copy unchanged since it, and validation of the real base-side edge.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
