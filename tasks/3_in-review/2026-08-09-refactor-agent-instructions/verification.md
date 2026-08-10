# Verification — Refactor repository agent instructions

**Verified:** 2026-08-09 by codex

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Personal global compatibility default

```
$ rg -n -A2 'Remove obsolete internal compatibility code' /Users/quentinmiao/.codex/AGENTS.md
14:- Remove obsolete internal compatibility code after supported callers and stored data have
15-  migrated. Do not add speculative aliases, shims, fallbacks, or migrations. Preserve explicit
16-  public and persisted contracts unless the user authorizes a breaking change.
```

## Contract size and diff hygiene

```
$ wc -l AGENTS.md automation/AGENTS.md history/AGENTS.md
      79 AGENTS.md
      40 automation/AGENTS.md
      44 history/AGENTS.md
     163 total
$ git diff --check
```

## Repository invariants

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
$ python3 automation/check_core_scope.py
core-scope: pass (5 core path(s), task 2026-08-09-refactor-agent-instructions; independent review manual; not invoked)
```

## Full test suite

```
$ python3 automation/run_tests.py
test lane: full
test reason: full suite requested
test workers: 8
test shards: 47
Ran 67 tests in 13.026s
OK (skipped=1)
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 104.87s
```
