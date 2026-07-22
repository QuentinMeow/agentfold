# The root README gets a reconciler line budget

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** human (directed in chat; transcribed by agent — chat leaves no trace)
**Description:** README.md is a human landing page — short pitch + map, depth linked in handbook/ — and the reconciler enforces a 140-line budget on it
**Review-by:** 2027-01-18

## Context

The agent/human audience split (`AGENTS.md` for agents, `README.md` for humans) was
already stated, but nothing bounded the README's depth: the reconciler budgeted
`AGENTS.md` and `SKILL.md` files while the README could grow without limit. The human
directed in chat that the README stay free of deep technical detail, with depth living
in referenced documents — in this repo, `handbook/` (a separate `references/` folder
was rejected: `handbook/naming-conventions.md` bans generic buckets, and `handbook/`
already is that home).

## Decision

The root `README.md` is a short pitch + repo map for humans; every technical detail it
mentions links to its `handbook/` (or other single-source) home rather than being
restated. Enforced mechanically: the reconciler's `agents-budget` check now budgets the
root README at 140 lines — the same ceiling as the root `AGENTS.md`, and comfortably
above the current ~120.

## Alternatives considered

- A new `references/` folder — duplicates `handbook/`'s role and violates the
  naming-convention ban on generic buckets.
- Advisory rule only, no budget — this repo's own principle is systems over
  instructions; an unenforced style rule is a wish.

## Consequences

Additions to the README must displace something or move depth into `handbook/`.
Revisit the number if the README legitimately needs more room (superseding ADR).
