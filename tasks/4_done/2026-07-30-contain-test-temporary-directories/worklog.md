# Worklog — Contain the test suite's temporary Git repositories to one scratch root

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — contain-test-temporary-directories (claude)

- Measured before touching anything: a completed `python3 automation/run_tests.py` leaks
  zero new directories into the real system temp directory (proven with a snapshot-diff
  script; the historical 596/937 figures were not reproduced and are not trusted — this
  session's suite is already sharded and runs in ~35-50s, not the 219s the historical
  session measured).
- Simulated the actual reported failure: started the runner in its own process group and
  `SIGKILL`'d the whole group 15s in (matching "killing tests on a deadline"). Before any
  fix, this left 18 new directories scattered as top-level siblings in the real system
  temp directory (8 `agentfold-git-fixture-*` skeleton caches, 1 `agentfold-tests-*` outer
  scratch root, 9 per-test `tmp*` fixture repositories). Reproduced twice with consistent
  shape (12-18 new entries depending on exact kill timing).
- Root cause: `automation/run_tests.py` already builds one scratch root per run and points
  child `HOME`/`XDG_CONFIG_HOME`/Git identity inside it, but never redirects `TMPDIR`. Every
  fixture's `tempfile.mkdtemp()`/`TemporaryDirectory()` call (no `dir=` anywhere) therefore
  resolves through the child process's ambient `TMPDIR`, i.e. the real system temp
  directory, not the run's own scratch root.
- Fix: added `install_isolated_scratch_tmpdir(scratch_root, child_environment)` in
  `automation/run_tests.py`, called once in `main()` right after
  `install_isolated_git_configuration`. It creates `scratch_root / "tmp"` and points
  `TMPDIR`, `TMP`, and `TEMP` at it in the one `child_environment` dict every worker
  subprocess (and the `--jobs 1` serial path) already receives.
- Re-ran the same kill simulation with the fix: exactly one new directory
  (`agentfold-tests-<random>`) appeared; `find` confirmed the 7 skeleton caches and 8 fixture
  repositories that would previously have scattered were nested inside it instead. A
  completed run still leaks zero (re-verified after the fix, sequentially, several times).
- Added a regression test (`test_isolated_scratch_tmpdir_redirects_child_fixture_repositories`)
  that spawns a real child Python process and checks where `tempfile.mkdtemp()` actually
  lands — not just that the dict carries the right keys — plus extended
  `test_main_passes_the_isolated_environment_to_each_test` with the same assertion for the
  keys `main()` hands every child.
- Timing: ran the full suite 5× on the original code and 9× on the fixed code (some
  interleaved via `git stash`/`stash pop` to reduce machine-noise bias, per
  `history/conversations/2026-07-29-1833PDT-fast-local-test-feedback/handover.md`'s
  documented 2x run-to-run variance on this machine). Ranges overlapped almost entirely
  (unfixed 35.86-49.49s, fixed 33.74-54.35s); averages differed by about 5.5s (13%), well
  inside the previously documented noise floor for this machine. Full numbers in
  `verification.md`.
- Full suite: 11/11 files pass, 66 tests (1 intentionally skipped, unchanged) in
  `test_run_tests.py`. `automation/reconcile/reconcile.py --check`: 0 findings.
- Not solved, by design: interruption itself. `SIGKILL` (and an uncaught `SIGTERM`) skip
  every `finally`/context-manager/`atexit` hook; nothing running inside the killed process
  can react. What changed is where the unavoidable debris lands: one named, discoverable,
  single-`rm -rf`-able directory instead of a scattered, anonymous handful.
