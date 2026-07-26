# Verification — Let a queue item resolve when its resolution evidence landed earlier

**Verified:** 2026-07-26 by codex

Only commands actually run and their real output are recorded. Long per-test output is
trimmed to the summary and any meaningful failure.

## Focused ordinary-request behavior

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue -k ordinary_request
Ran 14 tests in 5.039s

OK
```

## Deterministic 300-commit process budget

The test asserts exactly one `git rev-list --parents --topo-order`, exactly one persistent
`git cat-file --batch`, no per-revision `rev-list`/`ls-tree`/`show`/`cat-file` command, and
zero additional process calls for a repeated creation lookup.

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_creation_lookup_bounds_git_calls_across_300_unrelated_commits
test_creation_lookup_bounds_git_calls_across_300_unrelated_commits (...) ... ok

Ran 1 test in 8.292s

OK
```

## Representative staged-and-range timing

```
$ /usr/bin/time -p python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_accepts_surviving_change_before_claim_staged_and_range
test_ordinary_request_accepts_surviving_change_before_claim_staged_and_range (...) ... ok

Ran 1 test in 2.294s

OK
real 3.82
user 1.77
sys 1.25
```

## Compatibility failure and repair

The first full run identified one shared cause across 14 errors: the new cached historical
reader assumed a commit root, while task admission intentionally supplies Git's empty-tree
object. The reader was generalized to accept validated commit or tree roots.

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue
Ran 320 tests in 234.356s

FAILED (errors=14)
reconcile_queue.GitSnapshotError: captured object 4b825dc642cb6eb9a060e54bf8d69288fbee4904 is not a Git commit
```

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue -k task_admission
Ran 13 tests in 21.118s

OK
```

## Final queue reconciler suite

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 320 tests in 311.668s

OK
```

## Staged admission check

```
$ python3 automation/reconcile/reconcile.py --check
(no output; exit 0)
```

## Full repository suite

```
$ python3 automation/run_tests.py
Ran 118 tests in 100.568s — OK
Ran 55 tests in 2.710s — OK (skipped=1)
Ran 24 tests in 0.015s — OK
Ran 9 tests in 0.020s — OK
Ran 40 tests in 16.857s — OK (skipped=1)
Ran 28 tests in 11.670s — OK
Ran 320 tests in 253.838s — OK
Ran 9 tests in 0.007s — OK
Ran 19 tests in 3.727s — OK
Ran 5 tests in 0.264s — OK
Ran 3 tests in 0.651s — OK
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
```

## Review verdicts

**Reviewed revision:** ee0f36e9d384278ce75717ae282a6d69edb0d39e

- correctness / independent adversarial panel: block — the exact synthetic merge admission candidate was not checked for a restoration to creation bytes
- contract / independent adversarial panel: block — commit parsing crossed the raw header boundary and the established unchanged-evidence diagnostic phrase drifted
- blast radius / independent adversarial panel: block — creation lookup launched several Git processes per intervening commit and had no deterministic process-budget regression

The blocked revision was not published. Repair verification and a fresh revision-bound review
follow before this task crosses into review.
