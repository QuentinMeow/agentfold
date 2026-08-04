# Verification — stop completed review verdicts from looking like human asks

**Verified:** 2026-08-04 by codex sol-high implementer

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Focused receipt, hostile-tail, task-origin, and core-scope regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_normalize_receipt_near_misses automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_accepts_receipt_but_rejects_its_hostile_finding automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict automation.tests.test_check_core_scope.CoreScopeTests.test_blocking_review_without_approve_majority_fails automation.tests.test_check_core_scope.CoreScopeTests.test_approve_majority_preserves_historical_block
.......
----------------------------------------------------------------------
Ran 7 tests in 0.256s

OK
```

## Full action-projection and core-scope modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope
...........................................................................................................................................................................................s..............
----------------------------------------------------------------------
Ran 202 tests in 17.611s

OK (skipped=1)
```

## Full repository suite

```
$ python3 automation/run_tests.py --jobs 4
test lane: full
test reason: full suite requested
selected test files:
  automation/tests/test_check_action_projection.py
  automation/tests/test_check_core_scope.py
  automation/tests/test_collect_github_review_actions.py
  automation/tests/test_github_action_projection_workflow.py
  automation/tests/test_inspect_workspace_boundaries.py
  automation/tests/test_integrate.py
  automation/tests/test_markdown_semantics.py
  automation/tests/test_mine_cochange.py
  automation/tests/test_pull_request_schema.py
  automation/tests/test_reconcile_open_actions.py
  automation/tests/test_reconcile_queue.py
  automation/tests/test_resolve_github_external_sources.py
  automation/tests/test_run_tests.py
  services/quote-api/tests/test_quote_api.py
  services/quote-cli/tests/test_quote_cli.py
test workers: 4
test shards: 29
  serial tail: automation/tests/test_run_tests.py -> not concurrency-safe, its tests re-run this whole runner, so a shard of it would nest a second worker pool inside the first
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
test elapsed: 68.19s
```

## Repaired exact-path and formal-region regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_normalize_receipt_near_misses automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_the_exact_receipt_path_and_region automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_accepts_receipt_but_rejects_its_hostile_finding automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_ignores_verdicts_before_the_revision_field automation.tests.test_check_core_scope.CoreScopeTests.test_blocking_review_without_approve_majority_fails automation.tests.test_check_core_scope.CoreScopeTests.test_approve_majority_preserves_historical_block
.........
----------------------------------------------------------------------
Ran 9 tests in 0.411s

OK
```

## Repaired action-projection and core-scope modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope
.............................................................................................................................................................................................s..............
----------------------------------------------------------------------
Ran 204 tests in 16.194s

OK (skipped=1)
```

## Staged diff and core-scope gate

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (5 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Review verdicts (when a review was explicitly run)

**Reviewed revision:** 85a044e67c725cf03d918432514c76ba1655c984

Panel result: 0 approve, 3 block.

- adversarial panel / reviewer 1: block — basename-only matching lets nested notes/verification.md and case-variant Verification.md files hide approval-like prose that the core gate never accepts as a receipt.
- adversarial panel / reviewer 2: block — a matching line outside the one real Review verdicts section, or before its one valid full-commit field, receives an exception the formal gate never grants.
- adversarial panel / reviewer 3: block — duplicate or missing sections and revision fields leave receipt lookalikes unbound, so neutralizing their verdict token can hide a real human ask.

This adversarial panel reviewed the prior revision. `--require-review` was not invoked;
the repaired commit still needs its own independent revision-bound review.

## Repaired staged diff and core-scope gate

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (6 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Repaired reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```
