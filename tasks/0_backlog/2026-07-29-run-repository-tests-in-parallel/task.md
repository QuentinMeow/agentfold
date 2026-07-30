# Run repository tests in parallel shards on the available cores

**Claimed-by:** unclaimed
**Filed:** 2026-07-29, by claude, from `docs/designs/fast-local-test-feedback.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-2026-07-29-run-repository-tests-in-parallel.md`

## Goal

The suite runs strictly serially. File-level parallelism is capped at 1.27-1.46x because one
file is 68-79% of the work, so sharding must be at test granularity; `unittest.main()` accepts
test names positionally, so no test file needs changing. A validated prototype ran all 625
tests in 26-30s. One file, `test_run_tests.py`, is not concurrency-safe and costs 2.2s, so a
serial tail is sufficient.

## Acceptance criteria

- [ ] THE SYSTEM SHALL accept a worker count, defaulting to the physical core count, with a
      single-worker mode that reproduces today's behaviour exactly.
- [ ] THE SYSTEM SHALL run the known non-concurrency-safe file serially and say so.
- [ ] The sharded run SHALL pass the same test set as the serial run, repeated to check for
      concurrency-induced flakiness.
- [ ] Wall time is recorded at several worker counts on an otherwise idle machine.

## Links

- `docs/designs/fast-local-test-feedback.md`
