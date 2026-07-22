# Enforce provenance-over-position mechanically

**Claimed-by:** unclaimed
**Filed:** 2026-07-22, by claude (design review; owner directed in chat — report: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`)
**Parent:** none

## Goal

`handbook/principles/provenance-over-position.md` (added 2026-07-22) says external
changes to instruction-bearing paths get human review before any agent acts on them
— but per systems-over-instructions, an unchecked "always" is a preference. Make it
mechanical: a CODEOWNERS file (or CI required-review rule) covering every
`AGENTS.md`, `skills/`, `templates/`, `automation/`, and `message-queue/`; plus a
reconciler check that queue items carry a `**Filed:** …, by <who>` naming a known
author (the owner, a listed maintainer, or the reconciler). Decide where the
maintainer list lives (one home).

## Acceptance criteria

- [ ] A PR from a non-maintainer touching any instruction-bearing path cannot merge
      without maintainer review (demonstrated, not asserted, in `verification.md`)
- [ ] A queue item whose `Filed:` names no known author is a reconciler finding
- [ ] The maintainer list has exactly one home; principle and CONTRIBUTING link it

## Links

- Principle: `handbook/principles/provenance-over-position.md`
- ADR: `memory/decisions/2026-07-22-provenance-over-position-principle.md`
- Design review, finding 1.6: `history/conversations/2026-07-22-0130PDT-design-review-grill/artifacts/design-review.md`
