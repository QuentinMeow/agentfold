# The owner confirmed all eight July goals, three of them with changes

**Status:** decided
**Date:** 2026-09-04
**Decided-by:** human (the owner answered in chat; transcribed into the clarification before folding)
**Description:** All eight goals agents wrote in July stand as owner-confirmed goals; per-skill canaries become manual and optional, and one-command adoption and the task viewer are deferred to the end of the priority order
**Review-by:** 2027-03-03

## Context

`roadmap/desired-state.md` held eight goals written by agents on 2026-07-22 and 2026-07-24
that the owner had never confirmed, while every task filed since traced to one of them. The
2026-09-04 provenance change marked them as agent proposals and asked the owner, in one
clarification, whether they still describe where the repository should go.

## Decision

The owner confirmed all eight. Four stand as written (G1 first-clone agents, G2 every schema
enforced, G7 the design-review repairs, G8 the guardrails). Three carry the owner's changes,
quoted in their goal entries: G4 per-skill canaries become manual and optional, never a merge
condition; G6 the task viewer is wanted eventually as a web kanban of overall progress and is
deferred; G3 one-command adoption is wanted later, not now, and is deferred. G5 the layered
public/private workspace stands, with the owner's reason: his `jobs-finder-toolkit`
repository already keeps real data in a private overlay by hand.

## Alternatives considered

- Retire some goals: the owner kept every one.
- Keep the deferred goals in their July positions: rejected, because position is priority and
  the owner said "not now" for G3 and G6, so they sit last.

## Consequences

Every live task can name a confirmed goal, so the "agent-proposed goal" reminder no longer
fires. G4 changes from a merge gate to a hand-run check. Reordering G3 or G6 back up is a
decision item, as any re-prioritisation of a confirmed goal is.
