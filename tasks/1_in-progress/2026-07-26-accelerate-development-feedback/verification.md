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

## Diff hygiene

```
$ git diff --check
```

## Review verdicts (when a review was explicitly run)

**Reviewed revision:** pending
