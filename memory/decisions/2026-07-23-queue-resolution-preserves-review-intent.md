# Queue resolution preserves review intent across revisions and rejected proposals

**Status:** decided
**Date:** 2026-07-23
**Decided-by:** agent (delegated two-way-door lifecycle repair after independent adversarial review)
**Description:** Review bindings retract before revision, requested changes keep a successor, terminal rejection closes, and displaced Git tips preserve live actions
**Review-by:** 2027-02-25
**Supersedes:** `memory/decisions/2026-07-23-queue-resolution-is-git-evidence.md`

## Context

The first Git-backed lifecycle treated every non-approved review alike and made a
published target immutable even before a human responded. That protected a review from
silent rebinding, but it also trapped two valid workflows: revising a stale artifact and
ending a proposal the reviewer explicitly rejected. A separate modular-adoption repair
allowed removal of the complete queue service, but initially let that removal erase live
actions. Divergent force pushes could do the same by dropping the old tip from the
checked history.

## Decision

A review has explicit, history-visible transitions:

- an unanswered `waiting` review may retract to `awaiting-artifact` only by restoring
  pending target/revision and blank response fields in a committed edge;
- a later commit may publish a replacement target and revision by returning to
  `waiting`; direct rebinding and any retraction/publication edge that adds a response
  remain invalid;
- `approved`, `rejected`, and `abandoned` are terminal dispositions;
- `changes-requested` keeps the dependency open and therefore requires a new
  same-timing review successor; legacy `not-approved` has that same meaning; and
- every concrete response remains bound to the exact published revision and becomes
  immutable when first committed.

Git admission checks both the candidate history and continuity from an explicitly
supplied displaced ref tip. A divergent update may not discard an action that was live
at the published old tip. Removing the entire optional `message-queue/` service is
allowed only when the removal edge contains no live action; retaining any part of the
service retains its v1 anti-downgrade rule. Provider adapters only supply immutable
candidate and prior-tip context.

## Alternatives considered

- Allow direct unanswered rebinding — fewer commits, but a reviewer can answer the old
  artifact while an agent silently replaces it.
- Require a successor after every non-approval — preserves work after requested
  changes, but fabricates a pending action when the human rejects or abandons the
  proposal.
- Forbid removing the queue service once adopted — prevents erasure, but contradicts
  AgentFold's folder-as-a-service adoption model.
- Inspect only the new side of a force push — simple, but actions unique to the
  discarded tip disappear without a resolution edge.

## Consequences

Artifact revision costs two explicit lifecycle commits: retract, then republish.
Reviewers can distinguish “revise this” from “stop this,” and only the former creates a
successor. Providers that expose ref rewrites must pass the displaced full object id;
an unavailable nonzero tip fails closed. Repositories remain free to remove the queue
service after resolving its live actions.
