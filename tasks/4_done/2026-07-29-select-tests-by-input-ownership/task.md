# Select repository tests from the staged paths that can affect them

**Claimed-by:** claude
**Filed:** 2026-07-29, by claude, from `docs/designs/fast-local-test-feedback.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

The existing `--staged` lane covers only the two example services, so its measured hit rate
over the whole repository history is zero. An explicit ownership table, fail-closed on any
unregistered path, lets record-only commits select no tests at all — which a corruption
experiment showed cannot change any outcome.

## Acceptance criteria

- [ ] WHEN every staged path is a record path, THE SYSTEM SHALL select no test files.
- [ ] WHEN a staged path is unregistered, or a non-record path is removed or renamed, THE
      SYSTEM SHALL select the full suite.
- [ ] A guard test SHALL fail if a test begins reading a record path.
- [ ] The selection is replayed over real repository history and the hit rate recorded.

## Links

- `docs/designs/fast-local-test-feedback.md`
