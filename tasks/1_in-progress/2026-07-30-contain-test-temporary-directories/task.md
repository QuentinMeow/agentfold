# Contain the test suite's temporary Git repositories to one scratch root

**Claimed-by:** claude
**Mode:** async
**Filed:** 2026-07-30, by claude, from chat — a well-scoped developer-velocity fix
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`automation/run_tests.py` already isolates every test run inside one scratch root
(`agentfold-tests-*`, an outer `tempfile.TemporaryDirectory`), but it never redirects the
child processes' own `TMPDIR`/`TMP`/`TEMP`. Every fixture that calls `tempfile.mkdtemp()` or
`tempfile.TemporaryDirectory()` without `dir=` — the git-repository fixtures in
`automation/tests/test_reconcile_queue.py`, `test_check_action_projection.py`,
`test_github_action_projection_workflow.py`, and others — therefore resolves against the
real system temp directory. A completed run's own context managers still clean these up,
but a killed run (`history/conversations/2026-07-29-1833PDT-fast-local-test-feedback/handover.md`
recorded "each run creates ~596 git repositories in `$TMPDIR`, killing leaks them... This
session removed 937 leaked directories (~410 MB)") leaves them scattered, unnamed, and
indistinguishable from the thousands of unrelated files already in a shared machine's temp
directory. Redirect every child process's temp directory into this run's own scratch root so
an interrupted run leaves at most one named, discoverable, single-`rm -rf`-able directory
instead of hundreds of anonymous ones.

## Acceptance criteria

- [x] Real before/after measurements of directories created and leaked, for both a completed
      run and a killed run, recorded in `verification.md` — not the historical 596/937 figures.
- [x] The leak site(s) are identified with file:line evidence.
- [x] A completed run leaks zero new directories, before and after the fix (this already held;
      the fix must not regress it).
- [x] A killed run, before the fix, leaves multiple scattered directories in the real system
      temp directory; after the fix, it leaves at most one named `agentfold-tests-*` directory,
      with every fixture repository nested inside it.
- [x] The fix does not change what any test asserts, and the full suite still passes.
- [x] Full-suite runtime before and after is measured and reported; no measurable regression
      attributable to the change (one `mkdir` and three dict assignments per run).
- [x] A regression test proves the redirection end-to-end (a real child process, not just a
      dict check).
- [x] `automation/reconcile/reconcile.py --check` reports 0 findings before commit.

## Links

- Problem record: `history/conversations/2026-07-29-1833PDT-fast-local-test-feedback/handover.md`
  (dead end: "Killing tests on a deadline is actively harmful").
- Design and rationale: `design.md`
- Plan: `plan.md`
- Verification: `verification.md`
- Changed file: `automation/run_tests.py` (new `install_isolated_scratch_tmpdir`, wired into
  `main()`); regression tests in `automation/tests/test_run_tests.py`.
