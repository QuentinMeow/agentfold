# Verification — accelerate the local development feedback loop

**Verified:** 2026-07-26 by codex

Only commands actually run + real output, never expected or paraphrased output (root
`AGENTS.md` guardrail). A reader must be able to re-run every line.

## Focused test-runner tests

```
$ python3 automation/tests/test_run_tests.py
................................
----------------------------------------------------------------------
Ran 32 tests in 1.433s

OK
```

## Narrow staged-path probe

The temporary alternate index changed only the selection input. The isolated runner
still tested current working-tree bytes, as documented by the runner.

```
$ set -e
$ AGENTFOLD_PROBE_DIR="$(mktemp -d /private/tmp/agentfold-fast-lane.XXXXXX)"
$ export GIT_INDEX_FILE="$AGENTFOLD_PROBE_DIR/index"
$ git read-tree HEAD
$ AGENTFOLD_PROBE_OBJECT="$(git rev-parse HEAD:services/quote-api/quote_api.py)"
$ git update-index --info-only --cacheinfo "100644,$AGENTFOLD_PROBE_OBJECT,services/quote-cli/quote_cli.py"
$ python3 automation/run_tests.py --staged
test lane: staged
test reason: all staged paths map to known service dependencies
selected test files:
  services/quote-cli/tests/test_quote_cli.py
...
----------------------------------------------------------------------
Ran 3 tests in 0.337s

OK
PASS services/quote-cli/tests/test_quote_cli.py
tests: 1/1 files passed
test elapsed: 1.15s
```

## Repository invariants

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

The pre-change median was 5.28 seconds. The implementation did not redesign the
reconciler; its post-change wall time remained effectively unchanged.

```
$ /usr/bin/time -p python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
real 5.43
user 3.64
sys 1.70
```

## Full commit gate

The pre-change full-suite measurement was 219.97 seconds. Because the staged change
included automation and task paths, the implementation commit correctly fell back to
all discovered tests.

```
$ git commit -m "Speed up staged service feedback" -m "Keep full isolated verification as the default while using a conservative, fail-closed service dependency lane during pre-commit." -m "task: 2026-07-26-accelerate-development-feedback"
pre-commit: core scope
core-scope: pass (4 core path(s), task 2026-07-26-accelerate-development-feedback; independent review manual; not invoked)
pre-commit: reconciler
reconcile: 0 finding(s)
pre-commit: staged-path repository tests
test lane: full
test reason: staged path is outside the known narrow service scopes
selected test files:
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
test elapsed: 218.90s
pre-commit: OK
[task/2026-07-26-accelerate-development-feedback a46c9e8] Speed up staged service feedback
 8 files changed, 598 insertions(+), 15 deletions(-)
```

## Diff hygiene

```
$ git diff --check
```

## Review verdicts (when a review was explicitly run)

**Reviewed revision:** pending
