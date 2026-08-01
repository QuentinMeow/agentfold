# Pick up the human-attention format redesign

**Status:** open
**Filed:** 2026-07-31, by claude, from the live redesign request — `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-31-redesign-human-action-files/task.md`
**Request kind:** task-pickup
**If unanswered:** The task stays unclaimed in backlog and every file that asks the owner for attention keeps the shape he already rejected.

## What you need to know

The owner accepted what the message-queue contract does and rejected how its files read.
The repair has a decided implementation spec: an ask-first header of exactly three
fields, a context block that separates today from the proposal, explicit choices with
per-choice example consequences, a recommendation carrying its own counter-case and a
graded confidence, and every machine field below the answer line.

The work is bounded. It enforces structure and never rendered prose, so it does not
touch `automation/markdown_semantics.py`. The riskiest part is a one-shot migration
carve-out in `queue_mutation_problem`, which must refuse any item that already carries a
human answer.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
