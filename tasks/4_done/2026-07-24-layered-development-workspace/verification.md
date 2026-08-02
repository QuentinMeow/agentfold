# Verification — layered development workspace

**Verified:** 2026-07-24 by codex

Only commands actually run and their real output are recorded below. Output is trimmed
to the meaningful result while retaining failures/skips and aggregate counts.

## Focused topology-inspector tests

```
$ python3 automation/tests/test_inspect_workspace_boundaries.py
......................s............
----------------------------------------------------------------------
Ran 35 tests in 7.175s

OK (skipped=1)
```

The skipped case is the non-UTF-8 path-byte case: this macOS Git rejects the fixture
path before the inspector can observe it.

## Repository test suite

```
$ python3 automation/run_tests.py
Ran 118 tests in 19.034s
OK
Ran 55 tests in 0.897s
OK (skipped=1)
Ran 24 tests in 0.008s
OK
Ran 9 tests in 0.009s
OK
Ran 35 tests in 7.242s
OK (skipped=1)
Ran 262 tests in 65.995s
OK
Ran 9 tests in 0.002s
OK
Ran 11 tests in 0.181s
OK
PASS automation/tests/test_probe.py
tests: 1/1 files passed
Ran 5 tests in 0.092s
OK
Ran 3 tests in 0.227s
OK
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 10/10 files passed
```

The reconciler snapshot-error lines emitted inside its negative-path tests were expected;
the enclosing 262-test file completed `OK`.

## Core-scope boundary

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD
core-scope: pass (47 core path(s), task 2026-07-24-layered-development-workspace; independent review manual; not invoked)
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## Diff and worktree hygiene

```
$ git diff --check origin/main...HEAD
```

No output; exit status 0.

```
$ git status --short
```

No output; exit status 0.

## Review verdicts (when a review was explicitly run)

**Reviewed revision:** `2fa68ce190e759abb1d69806a5df987be16523c9`

- executable correctness / candidate710_executable: no blocker found
- control-plane contract / precommit_dependency_audit: no blocker found
- confidentiality and recovery / layered_final_confidentiality: no blocker found

## Superseded blocked review history

- `feddac15eb51dbe7cd23129a8f427fcc98e4ebd1` — all three reviewers blocked:
  layered_review_ergonomics, layered_review_confidentiality, and
  layered_review_authority_portability.
- `7fc3bca74b6f36409bbf1c8f1fd18dd1a1f5775d` — all three reviewers blocked:
  layered_candidate_ergonomics, layered_candidate_confidentiality, and
  layered_candidate_authority_portability.
- `a46b39189c234ede265142d54f949b4a0d526746` — all three reviewers blocked:
  layered_final_implementation, layered_final_contract, and
  layered_final_confidentiality.
- `31a5ff1220bf6767dc2fecaec4b3369906dbedac` — all three reviewers blocked:
  layered_release_implementation, layered_release_contract2, and
  layered_release_confidentiality.
- `710578bc9242988bcbb51be7a82af54282b435ca` — all three reviewers blocked:
  candidate710_executable, precommit_dependency_audit, and
  layered_final_confidentiality.

The concrete findings and repairs for every blocked revision are appended in
`worklog.md`; no blocked verdict is counted toward acceptance.

## Recovered-candidate no-Git marker regression

```
$ python3 automation/tests/test_inspect_workspace_boundaries.py
.........................s..............
----------------------------------------------------------------------
Ran 40 tests in 11.897s

OK (skipped=1)
```

The new case constructs an external `HEAD` plus `commondir` administration layout,
confirms that Git discovers it from a nested raw root, and confirms the inspector
rejects that root as Git-contained.

## Recovered publication review verdicts

**Reviewed revision:** `8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b`

- executable correctness lens — approved
- control-plane contract lens — approved
- confidentiality and blast-radius lens — approved

The exact range
`c154d87737de7c141784e13f3eb520664b9838f6...8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b`
also passed the core-scope check, reconciler, and diff hygiene; it contained no changed
paths under `tasks/0_backlog/` or `message-queue/needs-agent/requests/`.
