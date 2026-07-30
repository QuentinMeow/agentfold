# Isolate child Git configuration by environment instead of a shell wrapper

**Claimed-by:** claude
**Filed:** 2026-07-29, by claude, from `docs/designs/fast-local-test-feedback.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`automation/run_tests.py` isolated child Git by writing a `#!/bin/sh` script named `git` onto
the child `PATH`, so every Git call spawned a shell that then `exec`d Git. Measured at 34-42%
of the whole gate. `HOME`, `XDG_CONFIG_HOME` and `GIT_CONFIG_NOSYSTEM` are inherited, so the
same isolation costs no process.

## Acceptance criteria

- [ ] WHEN a repository test runs, THE SYSTEM SHALL resolve plain `git` to the real binary.
- [ ] WHEN a test child or grandchild runs Git, THE SYSTEM SHALL NOT read the caller's global
      or `XDG` configuration.
- [ ] THE SYSTEM SHALL keep the projected test view a non-repository.
- [ ] The improvement is recorded from a controlled before/after, not estimated.

## Links

- `docs/designs/fast-local-test-feedback.md`
