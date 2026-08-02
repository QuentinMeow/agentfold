# Pick up the countersigned migration of the eight live asks

**Status:** open
**Filed:** 2026-08-01, by claude, from the human-action format redesign — `handbook/human-action-guide.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-countersign-the-live-human-item-migration/task.md`
**Request kind:** task-pickup
**If unanswered:** The eight existing asks stay exactly as they are and age out as they resolve; every new ask is already written in the current format, so nothing waits on this.

## What you need to know

The human-attention format governs new asks only. Migrating the eight files already in
`message-queue/needs-human/` was attempted under a fenced carve-out in
`queue_mutation_problem` and withdrawn: with every frozen field byte-identical and the
reconciler reporting zero findings, a migration could still change the question, invert a
scope limit the owner had set, delete a choice, and flip the recommendation. The fences
cover field labels; the ask a human reads is the title, the context, the choices, and the
recommendation.

So the migration needs the owner's countersignature: a queue item showing the per-file
before and after, answered and committed before anything is rewritten.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
