# Requested review changes route through an agent repair before re-review

**Status:** decided
**Date:** 2026-07-23
**Decided-by:** agent (delegated, reversible queue-lifecycle repair after independent review)
**Description:** A changes-requested review creates one agent-owned repair and a distinct artifact-pending human re-review at the same boundary
**Review-by:** 2027-01-19
**Supersedes:** `memory/decisions/2026-07-23-queue-resolution-preserves-review-intent.md`
**Amended-by:** `memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md` (the re-review may no longer bind the repair's merge, so a changes-requested review whose repair has already landed carries its question `non-blocking-`; the agent-repair-plus-distinct-re-review pair stands)

## Context

The prior lifecycle kept a requested-change review open by requiring only another
`needs-human/reviews` item. That preserved the review boundary, but it did not record
the requested repair under `needs-agent`, even though an agent acts next. A precise
repair could therefore survive only in review prose while the queue falsely routed
the next move to the human.

## Decision

Resolving `changes-requested` (including legacy `not-approved`) introduces both actions
at the same dependency timing:

- the old review's `Successor action` names one new open `needs-agent` item. Its
  `Action` is the sole live statement of the repair, its `Full context` and timing
  match the old review, it predeclares non-queue `Resolution evidence`, and
  `Supersedes` points to the old review; and
- that repair's `Follow-up review` names one distinct new `needs-human/reviews` item.
  It starts `awaiting-artifact`, keeps the same context and timing, points to the old
  review with `Supersedes`, and names the repair with `Depends on`. Its `Action` is
  the later judgment, never a copy of the repair.

The old review may be deleted only when both successors are introduced in its
resolution edge. This keeps the original boundary closed until the follow-up review
eventually receives an `approved`, `rejected`, or `abandoned` disposition. Review
binding, terminal-outcome, and displaced-tip rules from the superseded decision remain
unchanged.

## Alternatives considered

- Keep only the human successor — preserves re-review but misroutes the next action and
  leaves repair ownership implicit.
- Keep only the agent successor — routes the repair correctly but could let completion
  erase the unaccepted review boundary.
- Copy the repair into both successor actions — appears explicit, but creates two live
  sources for one action that can drift.
- Defer creating the follow-up review until repair completion — avoids an
  artifact-pending item, but requires a second coupled deletion invariant and leaves
  review intent less discoverable during repair.

## Consequences

Requested repairs are discoverable and claimable by the correct actor, while the human
judgment remains durable and cannot be mistaken for repair work. Resolution creates two
queue files because they are two different actions; only the agent item states the
repair. Repositories adopting custom agent leaves may use them when they satisfy the
same generic Action, context, timing, and resolution-evidence contract.
