# The README/AGENTS split is instructions, not readership

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** human (directed in chat; transcribed by agent — chat leaves no trace)
**Description:** Agents may read (and do write) the README for the big picture; the split is that the README never carries agent instructions and the root AGENTS.md is self-contained, never depending on the README
**Review-by:** 2027-01-18

## Context

Earlier wording framed the split as readership: "Humans read `README.md` instead",
"(humans only; agents read AGENTS.md)". The owner corrected the model in chat: agents
generate the README and may skim it for the general picture, so a readership ban is
both false and unenforceable. The durable asymmetry is about *content and dependency*,
not about who opens the file.

## Decision

Two rules replace the readership framing. The README never carries agent
instructions — an agent must never need it to act correctly. The root `AGENTS.md` is
always read by agents and is self-contained: it may link depth (handbook, templates)
but never depends on the README. Reworded in the root `AGENTS.md` intro and the
README's tour line. This refines the framing in
`memory/decisions/2026-07-22-root-readme-line-budget.md`; that ADR's budget decision
is unchanged.

## Alternatives considered

- Keep "humans only" as shorthand — actively wrong: agents write the file, and the
  shorthand invites putting agent-relevant content nowhere.
- Supersede the budget ADR — nothing in it is reversed; a refinement is a new record.

## Consequences

Agents may cite the README for orientation but never as a contract source; anything an
agent must obey lives in an `AGENTS.md`, a template, or the handbook. Revisit only if
the README ever needs to carry normative agent content (it shouldn't).
