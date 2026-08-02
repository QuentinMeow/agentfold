# Design notes — clear the four stuck queue items against real repository state

**Status:** decided

## Problem

Four live items were stuck. Only one of them was stuck for a reason a rule change could
fix, and treating the other three the same way would have destroyed a real pending human
judgment to make a checker green.

The merged code-span repair request was mechanically stuck: its declared evidence,
`automation/reconcile/reconcile.py`, already carried the repair, so the deletion edge had
nothing left to change. Task 2026-07-30-admit-evidence-that-landed-earlier widened that
comparison, and applying it is arithmetic, not judgment.

The three merge reviews are stuck for a different reason. Each says
`Blocks at: transition:merge`, each binds an exact Git range, and every one of those ranges
is already an ancestor of `main`. The gate they exist to hold was crossed while they sat
unanswered. Nothing in Git can un-cross it, so there is no repository action that turns them
into resolved items — and the reason they are still open is that a judgment was requested
and never given.

## Options considered

### Option A — Answer, retract, or close them so the queue is empty
Treat "four stuck items" as one problem and clear all four in this task.
*Example consequence:* Three human response slots that have never been filled get disposed
of by the agent that noticed they were inconvenient. The repository's own checks resist this:
staging the deletion of one is refused for having no committed folding claim with a concrete
response, and it simultaneously turns that task's acceptance-criteria link back into an
unqueued human action. Both refusals are the contract working exactly as intended.

### Option B — Resolve the one item the widened rule admits, and escalate the three
Delete the merged request, complete its task, and file one canonical decision item for the
three, leaving them live, unanswered, and byte-identical.
*Example consequence:* One item leaves the queue with real evidence behind it, three keep
their unfilled response lines, and the choice between recording the crossing, answering the
old question, and asking a new one reaches the person who was asked in the first place.
The three tasks stay in review, which is what their records already said and what the
measurement confirms.

### Option C — Leave all four alone and only report
*Example consequence:* Nothing is destroyed, but the one item the stack's whole effort was
built to unstick stays stuck, and the acceptance test the widening was written for is never
run against live state.

## Chosen

Option B.

The dividing line is whether the item's obstacle is mechanical or human. The code-span
request declared what would resolve it, that thing happened, and the repository can attribute
it: `6d4e337` is an ancestor of `main` and carries the trailer naming the task that linked
the request. Deleting it destroys nothing, because the evidence it asked for exists.

The three reviews declared that a human would judge a diff before it merged. That did not
happen, and no later commit can make it have happened. Their remaining content is an unfilled
human response slot, which is precisely the thing the repository's guardrails say an agent
may never edit or discard. Three separate items asking the same question would also be three
copies of one choice, so the disposition was filed once, as
`message-queue/needs-human/decisions/future-blocking-dispose-merge-reviews-whose-boundary-already-passed.md`,
with the three tasks named in its boundary and linking it reciprocally.

That item is `future-blocking` on `transition:complete` rather than `blocking`. The tasks are
not stopped now — their work merged — and a `blocking` item naming a task id would force
those three tasks into `2_blocked`, which is a backwards status edge from `3_in-review` and
would misdescribe them. `transition:complete` is the boundary that is genuinely closed.

The recommendation inside that item is retract-and-refile, because it is the only disposition
that neither invents an answer nor discards the request, and the only one that leaves the
three tasks with a boundary a commit can actually cross. It is a recommendation and not a
decision; the item presents all three options with their consequences.

### What was deliberately not done

- No response, outcome, revision, or status was written into any of the three reviews.
- No retraction was performed. Retracting to `awaiting-artifact` is a contract-supported
  edge for an unanswered review, but it also silently converts "may this merge" into
  "should this stay". That substitution is the decision itself, so it was offered rather
  than taken.
- The three tasks were not moved. `3_in-review` is not the false part of their state: their
  worklogs already record the merges, and `4_done` requires `Queue actions: none`, which
  cannot be true while an unanswered review is live. What was missing was the measurement
  showing the state is permanent, and that is what this task appended.

## Core fit

Not required: this task's `Repository scope` is `records-only`. It changes queue items, task
records, one roadmap entry, and no tracked executable or contract.
