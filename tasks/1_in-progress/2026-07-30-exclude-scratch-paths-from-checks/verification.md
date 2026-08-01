# Verification — exclude scratch paths from the reconciler's filesystem walks

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Reproducing the bug (before the fix)

A copy of the root `AGENTS.md` under `tmp/` (untracked, `tmp/` is in `.gitignore`):

```
$ mkdir -p tmp && cp AGENTS.md tmp/AGENTS.md && wc -l tmp/AGENTS.md
     119 tmp/AGENTS.md
$ python3 automation/reconcile/reconcile.py --check; echo "EXIT:$?"
[agents-budget] tmp/AGENTS.md: 119 lines exceeds the 60-line budget
    fix: move depth into a linked doc (handbook/principles/progressive-disclosure.md)
reconcile: 1 finding(s)
EXIT:1
```

The "stray scratch clone" shape (a plain over-budget file nested a directory deeper
under `tmp/`, matching a clone's shape rather than a hand-copied file):

```
$ rm -rf tmp && mkdir -p tmp/scratch-clone
$ python3 -c "
open('tmp/scratch-clone/AGENTS.md','w').write('# Nested project\n\n' + '\n'.join(f'line {i}' for i in range(80)) + '\n')
"
$ wc -l tmp/scratch-clone/AGENTS.md
      82 tmp/scratch-clone/AGENTS.md
$ python3 automation/reconcile/reconcile.py --check; echo "EXIT:$?"
[agents-budget] tmp/scratch-clone/AGENTS.md: 82 lines exceeds the 60-line budget
    fix: move depth into a linked doc (handbook/principles/progressive-disclosure.md)
reconcile: 1 finding(s)
EXIT:1
```

## After the fix: both scratch files together, no finding

```
$ mkdir -p tmp/scratch-clone
$ cp AGENTS.md tmp/AGENTS.md
$ python3 -c "
open('tmp/scratch-clone/AGENTS.md','w').write('# Nested project\n\n' + '\n'.join(f'line {i}' for i in range(80)) + '\n')
"
$ python3 automation/reconcile/reconcile.py --check; echo "EXIT:$?"
reconcile: 0 finding(s)
EXIT:0
```

## A tracked file at the same ignored-looking path is still checked

```
$ mkdir -p tmp && cp AGENTS.md tmp/AGENTS.md && git add -f tmp/AGENTS.md
$ python3 automation/reconcile/reconcile.py --check; echo "EXIT:$?"
[agents-budget] tmp/AGENTS.md: 119 lines exceeds the 60-line budget
    fix: move depth into a linked doc (handbook/principles/progressive-disclosure.md)
reconcile: 1 finding(s)
EXIT:1
$ git reset tmp/AGENTS.md && rm -rf tmp
```

## The regression test fails without the fix, passes with it

With the `reconcile.py` change reverted (test file kept):

```
$ git stash push -- automation/reconcile/reconcile.py
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_agents_budget_ignores_an_untracked_scratch_file_under_gitignored_tmp -v
======================================================================
FAIL: test_agents_budget_ignores_an_untracked_scratch_file_under_gitignored_tmp (automation.tests.test_reconcile_queue.ReconcileQueueTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 12727, in test_agents_budget_ignores_an_untracked_scratch_file_under_gitignored_tmp
    self.assertEqual([], list(RECONCILE.check_agents_budget()))
AssertionError: Lists differ: [] != [<reconcile_queue.Finding object at 0x10ebb58d0>]
----------------------------------------------------------------------
Ran 1 test in 0.184s

FAILED (failures=1)
$ git stash pop
```

Restored, both new tests pass:

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_agents_budget_ignores_an_untracked_scratch_file_under_gitignored_tmp automation.tests.test_reconcile_queue.ReconcileQueueTests.test_agents_budget_still_checks_a_tracked_file_at_an_ignored_looking_path -v
test_agents_budget_ignores_an_untracked_scratch_file_under_gitignored_tmp (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_agents_budget_still_checks_a_tracked_file_at_an_ignored_looking_path (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.226s

OK
```

## Full test suite

```
$ python3 automation/run_tests.py
...
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 55.71s
```

(`test_run_tests.py` exercises the test runner itself against small generated fixture
suites in a temporary directory as part of the same run; those fixtures are not
repository files. All passed.)

## The reconciler on the repository itself, at commit time

```
$ python3 automation/reconcile/reconcile.py --check; echo "EXIT:$?"
reconcile: 0 finding(s)
EXIT:0
```

## Core-scope gate (this task touches `automation/reconcile/reconcile.py`)

```
$ python3 automation/check_core_scope.py --staged --branch task/2026-07-30-exclude-scratch-paths-from-checks
core-scope: pass (2 core path(s), task 2026-07-30-exclude-scratch-paths-from-checks; independent review manual; not invoked)
```

## Staged-path test selection (what the pre-commit hook actually runs)

```
$ python3 automation/run_tests.py --staged
...
selected test files:
  automation/tests/test_reconcile_queue.py
...
PASS automation/tests/test_reconcile_queue.py
tests: 1/1 files passed
test elapsed: 26.56s
```
