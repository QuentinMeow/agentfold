# Stop the workspace-boundary tests from flaking under parallel sharding

**Claimed-by:** unclaimed
**Filed:** 2026-08-16, by claude, from publishing the stale-base pull request
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-workspace-boundary-tests-from-flaking-under-sharding.md`

## Goal

`python3 automation/run_tests.py` reported `automation/tests/test_inspect_workspace_boundaries.py`
failing once on branch `task/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check`
at revision `021bc8b`, giving `tests: 14/15 files passed`. The same module passed standalone
in that worktree and on `main` (`Ran 40 tests ... OK (skipped=1)`), and the immediate re-run
of the full suite passed `15/15`. The failure is therefore in how the run is executed, not in
what it asserts.

`run_tests.py` shards selected tests at test-method granularity across workers sharing one
projection, and `QUARANTINED_TEST_FILES` already names the files that must run alone. This
module inspects Git-metadata topology and worktree cleanliness, which is shared mutable state
across workers, so it is a candidate either for quarantine or for a repair that removes the
shared dependency. A test suite that fails once in two identical runs teaches everyone to
re-run rather than to read the failure, which is the same trust problem the advisory merge
gate already has.

## Acceptance criteria

- [ ] WHEN the full suite runs repeatedly under the default sharded lane, THE SUITE SHALL
      report the same result every time. Demonstrate with a repeat count, not a single run.
- [ ] The cause is named: either the shared state two workers contend for, or the reason the
      module must run alone. A quarantine entry carries the reason the runner prints.
- [ ] WHEN the module's own invariants are violated, THE SUITE SHALL still fail. Prove the
      tests still bite rather than being skipped or weakened.
- [ ] `python3 automation/run_tests.py` passes, with real repeated output in `verification.md`.

## Links

- Observed while publishing pull request #86, whose Notes record the same run
- The runner and its quarantine list: `automation/AGENTS.md`, `automation/run_tests.py`
