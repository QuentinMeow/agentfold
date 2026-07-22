# The README/AGENTS split is about instructions, not readership

**Claimed-by:** claude (chat session)
**Mode:** async
**Filed:** 2026-07-22, by the repo owner (chat request, transcribed here — chat leaves no trace)
**Parent:** none

## Goal

Chat correction from the owner: agents don't "never read" the README — agents generate
it, and may skim it for the general picture. The real rules are: the README never
carries agent instructions, and the root `AGENTS.md` is always read by agents and must
be self-contained — acting correctly must never require the README. Current wording
overstates readership: root `AGENTS.md` says "Humans read `README.md` instead" and the
README's tour labels itself "(humans only; agents read AGENTS.md)".

## Acceptance criteria

- [ ] Root `AGENTS.md` states it is self-contained (never depends on the README) and
      that the README carries no agent instructions, without claiming agents never read it
- [ ] The README tour line no longer says "humans only"
- [ ] `automation/reconcile/reconcile.py --check` and `automation/run_tests.py` pass

## Links

- Chat request (this file is the transcription; chat leaves no trace)
- Refines the framing used in `memory/decisions/2026-07-22-root-readme-line-budget.md`
  (that ADR's budget decision stands; ADRs are immutable, so the refinement is a new
  ADR, not an edit)
