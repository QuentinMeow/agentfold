# Accelerate the local development feedback loop

**Claimed-by:** codex
**Filed:** 2026-07-26, by codex, from the owner's request in chat to improve the test harness and agent development speed in one pull request
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Reduce the time an agent waits between a small staged change and a safe commit without
weakening the full repository verification boundary. Add a conservative changed-path
test lane for pre-commit use, keep an explicit full-suite path for CI and release
evidence, expose enough timing and selection evidence to prevent performance regressions,
and take only low-risk adjacent optimizations that survive independent review.

## Acceptance criteria

- [ ] WHEN the pre-commit hook sees a staged change with a known narrow test scope, THE
      SYSTEM SHALL run the core-scope gate, reconciler, and every test file mapped to
      that scope without running unrelated test files.
- [ ] WHEN the staged path cannot be mapped safely, THE SYSTEM SHALL fail closed to the
      full repository suite rather than silently omit tests.
- [ ] WHEN CI or a human invokes the existing full-suite interface, THE SYSTEM SHALL
      retain the isolated Git environment and run every discovered repository test.
- [ ] The runner reports the selected lane, selected test files, and useful elapsed
      timing in deterministic human-readable output.
- [ ] Focused tests cover narrow selection, cross-cutting fallbacks, empty/invalid Git
      state, and preservation of the full-suite default.
- [ ] Before-and-after measurements for the reconciler, a narrow staged-change path,
      and the full suite are recorded with the exact commands and real output in
      `verification.md`.
- [ ] `automation/AGENTS.md` and the hook documentation describe the fast and full
      verification boundaries without duplicating the selector implementation.

## Links

- `automation/hooks/pre-commit`
- `automation/run_tests.py`
- `automation/reconcile/reconcile.py`
- `handbook/principles/systems-over-instructions.md`
- `handbook/principles/eventual-consistency.md`
