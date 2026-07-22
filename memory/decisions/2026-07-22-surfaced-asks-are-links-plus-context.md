# A surfaced needs-human item is a clickable link plus context, never a bare name

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** human (directed in chat; transcribed by agent — chat leaves no trace)
**Description:** Handovers and final replies surface pending items as a clickable link to the queue file plus 2–3 sentences of context; the file links onward to its sources
**Review-by:** 2027-01-18

## Context

Handovers and every session's final reply must re-surface open `needs-human/` items —
but the texts governing this (`templates/handover.md`, the root `AGENTS.md`
message-queue ritual, `skills/session-handover/SKILL.md`) only said "with links",
so a bare mention like "pending decision: ABC" satisfied them. The human directed the
intended shape in chat: name the item as a clickable link to the queue file, follow
with a few sentences of context sufficient to act without opening anything, and let
the queue file link onward to the design doc or other source of truth (it is a
projection — `memory/decisions/2026-07-22-queue-items-are-regenerable-projections.md`).

## Decision

The format lives in one place — the "Needs your attention" section of
`templates/handover.md`: `[short name](path to queue item)` followed by 2–3 sentences
(what the choice is, why it came up, the default path). Ritual step 4 in the root
`AGENTS.md` and the session-handover skill require the format and link to the template
rather than restating it.

## Alternatives considered

- Restate the format in all three texts — violates single source of truth and the
  copies would drift.
- A reconciler check — the reply/handover prose isn't mechanically checkable without
  brittle heuristics; the template is the enforcement surface schemas get.

## Consequences

A human reading a handover or reply can always click through: reply → queue item →
source of truth. Revisit if a mechanical check for handover format becomes practical.
