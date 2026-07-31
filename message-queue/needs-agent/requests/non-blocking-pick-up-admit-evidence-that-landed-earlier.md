# Pick up the earlier-evidence admission task

**Status:** open
**Filed:** 2026-07-30, by claude, from chat
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-admit-evidence-that-landed-earlier/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; `blocking-repair-handover-projection-code-span-copy.md` stays undeletable and no current work is blocked.

## What you need to know

`resolution_evidence_problem` compares the declared evidence file across the deletion edge
only, so work that merged earlier is byte-identical on both sides and its item can never be
deleted honestly. Widening that window to "changed at some point" was measured to make 14 of
14 live ordinary requests deletable with no work. This task ships the narrow widening: the
evidence may have landed earlier only in a commit the repository already attributes to a
task that linked this exact queue path and was already past pickup at that commit.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
