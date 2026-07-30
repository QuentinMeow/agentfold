# Verification — parseable reporting for an empty selection

Commands actually run in the task worktree on branch
task/2026-07-30-report-unrun-coverage-honestly, with their real output.

## Each new test fails without its change

Each change was reverted in turn and its test run alone, to prove the test is a guard and
not a restatement of the code.

Reverting the inert-probe call site back to the pre-rename name:

```
$ python3 -m unittest automation.tests.test_run_tests.InputOwnershipTests.test_every_runner_attribute_this_file_names_actually_exists
----------------------------------------------------------------------
Ran 1 test in 0.051s

FAILED (failures=1)
```

Removing the summary line from the empty-selection path:

```
$ python3 -m unittest automation.tests.test_run_tests.StagedTestSelectionTests.test_an_empty_selection_still_prints_a_parseable_summary
----------------------------------------------------------------------
Ran 1 test in 0.011s

FAILED (failures=1)
```

Removing the coverage destination from the skipped-file line:

```
$ python3 -m unittest automation.tests.test_run_tests.StagedTestSelectionTests.test_report_names_where_skipped_coverage_happens
----------------------------------------------------------------------
Ran 1 test in 0.008s

FAILED (failures=1)
```

## The runner's own test file passes

```
$ python3 -m unittest automation.tests.test_run_tests
Ran 50 tests in 1.883s

OK (skipped=1)
```

## The inert probe reaches the projection instead of raising

Before the change this raised `AttributeError` on the renamed wrapper installer. The
probe is gated behind an environment variable the suite never sets, which is why the
breakage stayed invisible.

```
$ AGENTFOLD_INERT_PROBE=1 python3 -m unittest automation.tests.test_run_tests

OK
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.00s
```

## An empty selection now reports in the same shape as any other run

One record path staged:

```
$ python3 automation/run_tests.py --staged
test lane: staged
test reason: every staged path is a record path no test reads
staged paths: 1
  tasks/1_in-progress/2026-07-30-report-unrun-coverage-honestly/design.md -> record path, no test reads it
selected test files:
  (none)
skipped test files: 11 (no staged path owns them); the complete suite still runs on every push
  automation/tests/test_check_action_projection.py
  automation/tests/test_check_core_scope.py
  automation/tests/test_collect_github_review_actions.py
  automation/tests/test_github_action_projection_workflow.py
  automation/tests/test_inspect_workspace_boundaries.py
  automation/tests/test_mine_cochange.py
  automation/tests/test_reconcile_queue.py
  automation/tests/test_resolve_github_external_sources.py
  automation/tests/test_run_tests.py
  services/quote-api/tests/test_quote_api.py
  services/quote-cli/tests/test_quote_cli.py
no discovered test file can be affected by the staged change
tests: 0/0 files passed
test elapsed: 0.04s
```

## The complete suite passes on this branch

Run with nothing staged, which is one of the selector's fail-closed branches and
correctly escalates to the full suite:

```
$ python3 automation/run_tests.py --staged
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 191.46s
```

That elapsed time is not a comparable benchmark: other agents were using this machine
throughout, and timings on it are only comparable between variants interleaved inside one
measurement session.
