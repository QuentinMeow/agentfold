# Make an empty selection report itself in the same parseable shape as any other run

**Claimed-by:** claude
**Filed:** 2026-07-30, by claude, from `memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

The runner prints `tests: N/M files passed` on every run that selects at least one file,
and every `verification.md` in this repository transcribes that line as its evidence. A
run that selects nothing returns success without printing it at all, so a gate that
correctly proved there was nothing to run is indistinguishable, to any reader or parser,
from a gate that died before it could summarize. In a repository whose contract forbids
fabricating test results, a success that cannot be parsed is the wrong failure mode.

This is what survives from experiment exp/c-tiered, whose central rule was rejected in
the decision record linked above. Two further gaps come with it: the skipped-file report
names what did not run but not where that coverage actually happens, and the inert-probe
test calls a runner function that was renamed when the Git shell wrapper was removed, so
the record-free projection proof raises `AttributeError` instead of running.

## Acceptance criteria

- [ ] WHEN a run selects no test file, THE SYSTEM SHALL print the same
      `tests: N/M files passed` summary line every other run prints, keeping the existing
      sentence that explains why nothing was selected.
- [ ] THE SYSTEM SHALL name where the coverage of an unrun file happens, not only that it
      did not run.
- [ ] `AGENTFOLD_INERT_PROBE=1` SHALL reach the projection it is meant to check, rather
      than failing on a renamed attribute.
- [ ] Each change above SHALL be covered by a test that fails without it.

## Links

- `memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`
- `docs/designs/fast-local-test-feedback.md`
