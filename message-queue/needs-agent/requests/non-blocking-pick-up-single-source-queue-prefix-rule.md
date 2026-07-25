# Pick up the queue prefix-rule single-sourcing task

**Status:** open
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-25-single-source-queue-prefix-rule/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; the five templates keep their duplicated prefix comment and the live "a named date" versus "UTC" inconsistency stays in the repository.

## What you need to know

All five queue templates restate the delivery-prefix rule owned by
`message-queue/AGENTS.md` in a byte-identical comment at their lines 1-7, and none of them
names that contract. Commit aca7014 updated the rule in the owner and in every template's
`Blocks at` field line while leaving line 4 of each template on the older wording, so the
duplication is not hypothetical drift — it is drifted now. The task deletes the restatement
and links the owner instead; the exact files, line numbers, and both wordings are recorded
in the task file so no re-derivation is needed.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
