# Worklog — parallel test shards

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — fast-local-test-feedback continuation (claude)

- Claimed from the backlog after PRs 20, 21 and 22 merged, which removed the shell
  wrapper, cut reconciler Git spawns, and added input-ownership selection.
- Re-measured the complete suite on merged main: 198.57s wall, 81.70s user, 102.63s sys.
  System time still exceeds user time, so the suite remains bound by process creation.
- Why this task still matters after the selector merged: input-ownership selection makes
  a records-only commit cost 0.02s, but a change to `automation/reconcile/reconcile.py`
  still selects `automation/tests/test_reconcile_queue.py`, which is 68-79% of the suite.
  Selection is already correct for that case; the selected unit is simply too large. That
  is the population parallel sharding serves.
- Implemented test-method sharding in `automation/run_tests.py`: `--jobs N` over one
  shared projection, `ast` discovery of class-and-method names with a whole-file fallback
  whenever the walk cannot prove it saw everything, longest-file-first chunks through a
  thread pool, per-shard buffered output, and a reported serial tail.
- The suite holds 653 test methods across 11 files. The `ast` walk sees all 653 and
  agrees exactly with the standard loader for every file, so nothing currently falls
  back — the fallback exists for the next test file that needs it.
- Concurrency-safety sweep found no second unsafe file: nothing in the repository calls
  `os.chdir`, every test writes only under a temporary directory, and no test writes into
  the shared projection, so patched module attributes and environment edits stay
  process-local once each shard is its own process. `automation/tests/test_run_tests.py`
  remains the only quarantine, because it re-runs the whole runner inside itself.
- Corrected the quarantine's printed reason after an independent profiler failed to
  reproduce the process-global-state hazard in seven concurrent runs of that file. The
  reason now claims only the effect that is verifiable from the source — nesting a second
  worker pool inside the first — because an unverified reason in the run's own output is
  worse than no reason.
- The thread pool is in the parent, which imports no repository module; the module-global
  `git cat-file` pipe in `automation/reconcile/reconcile.py` and the direct environment
  edits in `automation/tests/test_check_action_projection.py` would both corrupt under
  threads, and both live only inside shard processes.
- Surprise worth not repeating: the verbose-log name extractor first reported 650 of 653
  tests. The standard runner prints a documented test's name and its docstring on two
  lines, so the naive "name ... result" pattern silently missed exactly the three tests
  that carry docstrings. A set-equality check is only as honest as its parser.
- Latent bug noticed but deliberately left alone, to keep this branch's diff on the
  runner: `test_the_whole_suite_passes_against_a_record_free_projection` still names
  `install_isolated_git_wrapper`, which is now `install_isolated_git_configuration`. That
  test is opt-in behind an environment variable, so the rename never failed anything; it
  would raise an attribute error today.
