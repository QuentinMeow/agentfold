# Pick up deciding how a queue-format migration is undone

**Status:** open
**Filed:** 2026-08-01, by claude, from the human-action format redesign — `message-queue/AGENTS.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-record-that-a-format-migration-is-one-way/task.md`
**Request kind:** task-pickup
**If unanswered:** No live queue item is being rewritten today, so there is nothing to undo; the question only becomes real if the countersigned migration proceeds.

## What you need to know

Any mechanism that admits one commit rewriting live queue items admits exactly the edge
that turns the format marker on. Reverting that commit is a second rewrite on an edge
whose parent already carries the marker, so `queue_mutation_problem` refuses it. Such a
migration can be performed and cannot be undone with `git revert`.

That is a property to state and design around, not a rule to loosen: either the migration
admits its own countersigned reversal edge, or the recovery path is to supersede the
items rather than restore them, written down before it is needed.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
