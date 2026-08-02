# Plan — Contain the test suite's temporary Git repositories to one scratch root

- [x] 1. Measure the current suite: full-run wall time, and whether a completed run leaks
      anything into the real system temp directory (a snapshot-diff script under `tmp/`).
- [x] 2. Locate every `tempfile.mkdtemp`/`TemporaryDirectory` call site under `automation/`
      and classify which are per-test scratch (already context-managed) versus per-process
      skeleton caches (`atexit`-registered).
- [x] 3. Simulate an interrupted run (`SIGKILL` the whole process group mid-run, matching how
      a developer actually stops a slow suite) and measure how many directories it leaves in
      the real system temp directory, before any fix.
- [x] 4. Implement the fix: `install_isolated_scratch_tmpdir()` in `automation/run_tests.py`,
      wired into `main()` right after `install_isolated_git_configuration()`, redirecting
      `TMPDIR`/`TMP`/`TEMP` for every child test process into a subdirectory of the run's own
      `agentfold-tests-*` scratch root.
- [x] 5. Re-measure: completed-run leak count (must stay zero), killed-run leak count (must
      drop to one directory), and full-suite wall time (must not measurably regress).
- [x] 6. Add a regression test that spawns a real child process and proves `TMPDIR` actually
      redirects fixture creation, plus extend the existing `main()` isolation test.
- [x] 7. Run the full suite and `automation/reconcile/reconcile.py --check`; fix any findings.
- [x] 8. Write `verification.md` with only real commands and real output; fill `design.md`'s
      Core fit receipt; move the task to review-ready state.
