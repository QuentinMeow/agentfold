# Unresolved queue delivery state is not regenerable

**Status:** decided
**Date:** 2026-07-23
**Decided-by:** human (required every human and durable agent action to be queued)
**Description:** Durable background can be reconstructed, but deleting an unresolved queue item loses its canonical action identity and delivery state
**Review-by:** 2027-02-20
**Supersedes:** `memory/decisions/2026-07-22-queue-items-are-regenerable-projections.md`

## Context

The earlier projection decision correctly kept durable design background outside the
queue, but concluded that deleting or rewriting any queue item was always safe. The
owner later made the queue the mandatory first-class action surface. Under that model,
an unresolved item's actor, timing, status, and response slot exist nowhere else;
reconstructing its background does not prove that the same action was delivered.

The queue-ownership decision remains
`memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`. This ADR corrects
only the older deletion claim without rewriting either decided record.

## Decision

Queue content has two different durability properties:

- background and completed reasoning belong in tasks, designs, memory, or code and may
  be reconstructed from those sources;
- the live action identity and unresolved delivery state belong only to the queue file
  and are not regenerable without loss of evidence.

Move a misfiled live item, and reclassify or resolve a stale one. Delete only after a
response is folded, the action is completed, or a duplicate/moot disposition is
recorded. Git can recover an accidental deletion; it is not the live delivery surface.

## Alternatives considered

- Edit the old ADR — clearer in isolation, but violates immutable decision records.
- Treat git history as the queue — it can recover bytes but cannot expose current actor,
  timing, or status without reconstructive judgment.
- Permit silent regeneration — recreates prose, not proof that the original action and
  any not-yet-folded response were preserved.

## Consequences

Agents must not clear unresolved messages merely because their background is linked
elsewhere. Active guidance and automation distinguish generated repair content from
actor-owned queue state, while completed reasoning still avoids duplication.
