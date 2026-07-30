# Give the commit gate a routine lane and let the push boundary own completeness

**Claimed-by:** unclaimed
**Filed:** 2026-07-29, by claude, from `docs/designs/fast-local-test-feedback.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-2026-07-29-defer-full-suite-to-push-boundary.md`

## Goal

`.github/workflows/harness.yml` already runs the full suite on every push of every branch with
no path filter, so the local full suite duplicates a gate that already blocks. A routine lane
plus an honest deferred-coverage report removes the duplicate. This task depends on input
ownership selection landing first: without it the routine lane selects nothing for an
`automation/` change, which would stop testing the file every agent depends on.

## Acceptance criteria

- [ ] WHEN the routine lane defers coverage, THE SYSTEM SHALL name every deferred file and
      where that coverage happens, before any test starts.
- [ ] THE SYSTEM SHALL leave the bare runner invocation running the full suite unchanged.
- [ ] Any configuration knob SHALL be an environment variable, not a new config file.
- [ ] A test SHALL fail if the workflow stops running the full suite on every push.

## Links

- `docs/designs/fast-local-test-feedback.md`
