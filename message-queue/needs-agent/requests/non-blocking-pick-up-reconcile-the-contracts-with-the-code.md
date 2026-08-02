# Pick up correcting the contract text that no longer matches the code

**Status:** open
**Filed:** 2026-08-02, by claude, from a contract-drift audit verified at revision `1871d5f`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-reconcile-the-contracts-with-the-code/task.md`
**Request kind:** task-pickup
**If unanswered:** Fourteen contract statements stay wrong. Three of them tell an agent to do something the pre-commit hook then refuses, so the agent's first correct-looking commit fails and it has no way to learn why from the contract it obeyed.

## What you need to know

The contracts are this repository's API, and an audit found fourteen places where they no
longer describe the code or contradict each other. The reconciler is green through every
one, because none of these has a shape a check can see.

The severe three all descend from human-gating v1: a near-immutable principle, the
authoritative timing table in `templates/README.md`, and the `pair` column of
`handbook/collaboration-modes.md` each still describe a human review holding a merge, which
the queue grammar now makes unspellable. The principle is not editable — it needs a decision
item — and the `pair` column is a real choice between changing the doc and scoping the rule
by mode.

The rest are direct repairs: undocumented link-check exemptions, a roadmap that says a
decision is pending sixteen lines before saying it was answered, a lifecycle diagram missing
two legal transitions, a rule stated unconditionally that the code applies only to blocked
tasks, and a memory fact listing one of six tags.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
