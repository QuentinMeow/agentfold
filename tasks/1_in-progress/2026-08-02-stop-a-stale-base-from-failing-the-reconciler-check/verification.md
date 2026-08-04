# Verification — stale-base pull-request admission

**Verified:** 2026-08-04 by sol-high implementer

Only commands actually run and their real output are recorded here.

## What the fixture proves

The tests extract the literal `run:` block from `Reconciler — pull-request merge boundary`
and execute it with `bash -e`, the shell behavior GitHub Actions uses. A local bare Git
repository supplies direct-head, two-parent advanced-base, wrong-head, non-merge,
three-parent, and unrelated-base commits. A capture-only `python3` stand-in records the
arguments the adapter would pass to the canonical reconciler; it does not imitate or replace
the reconciler's own tests.

The fixture simulates the observable Git state after a provider recomputes a merge ref. It
does not race a live GitHub pull request and makes no claim about provider timing.

## Focused literal-block fixtures

```
$ python3 -m unittest -v automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests.test_reconciler_candidate_binds_direct_head_and_advanced_base automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests.test_reconciler_candidate_rejects_unbound_checked_out_commits automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests.test_reconciler_candidate_binding_has_no_mutable_resolution_loop automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests.test_reconciler_head_guard_is_load_bearing automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests.test_reconciler_advanced_base_admission_is_load_bearing
test_reconciler_candidate_binds_direct_head_and_advanced_base (automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests)
The literal adapter emits the PR leg the reconciler can bind. ... ok
test_reconciler_candidate_rejects_unbound_checked_out_commits (automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests)
A moved base is admitted without weakening any parent binding. ... ok
test_reconciler_candidate_binding_has_no_mutable_resolution_loop (automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests)
An immutable checkout fails directly rather than polling a mutable ref. ... ok
test_reconciler_head_guard_is_load_bearing (automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests)
Deleting the second-parent comparison makes the bad fixture pass. ... ok
test_reconciler_advanced_base_admission_is_load_bearing (automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests)
Removing the new admission makes the stale-base fixture fail again. ... ok

----------------------------------------------------------------------
Ran 5 tests in 4.182s

OK
```

The last two cases run weakened copies of the literal workflow block. Deleting the head
comparison makes a wrong-head candidate reach the reconciler invocation; removing the new
advanced-base admission makes the stale-base fixture fail again. The passing suite therefore
depends on both the admission and its fail-closed guard.

## Complete workflow adapter module

```
$ python3 automation/tests/test_github_action_projection_workflow.py
.........................
----------------------------------------------------------------------
Ran 25 tests in 12.410s

OK
```

## Full repository suite

```
$ python3 automation/run_tests.py
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
test workers: 8
test shards: 47
  serial tail: automation/tests/test_run_tests.py -> not concurrency-safe, its tests re-run this whole runner, so a shard of it would nest a second worker pool inside the first
....s..........test lane: full
test reason: full suite requested
selected test files:
  automation/tests/test_git_init_probe.py
test workers: 8
test shards: 1
  whole file: automation/tests/test_git_init_probe.py -> test discovery could not see every test
.PASS automation/tests/test_git_init_probe.py
tests: 1/1 files passed
test elapsed: 0.19s
test lane: full
test reason: full suite requested
selected test files:
  automation/tests/test_first.py
  automation/tests/test_second.py
.PASS automation/tests/test_first.py
PASS automation/tests/test_second.py
tests: 2/2 files passed
test elapsed: 0.00s
test lane: full
test reason: full suite requested
selected test files:
  automation/tests/test_probe.py
..................................................
----------------------------------------------------------------------
Ran 67 tests in 7.181s

OK (skipped=1)
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.00s
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
test elapsed: 66.30s
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Core-scope receipt

The branch is intentionally uncommitted and this linked worktree's real Git index is outside
the writable sandbox. The successful check used a throwaway index and object directory under
ignored `tmp/`, with the main object database read only as an alternate; the real index was
not modified.

```
$ env GIT_INDEX_FILE=/private/tmp/agentfold-stale-base-fix-20260804/tmp/stale-base-core-scope-20260804/index GIT_OBJECT_DIRECTORY=/private/tmp/agentfold-stale-base-fix-20260804/tmp/stale-base-core-scope-20260804/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=/Users/quentinmiao/code/ai-harness/.git/objects python3 automation/check_core_scope.py --staged --branch task/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check
core-scope: pass (2 core path(s), task 2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check; independent review manual; not invoked)
```

`--require-review` was not run: there is no commit revision to bind an independent review
receipt to, and this delegated implementation was explicitly forbidden from committing or
publishing. That review remains part of plan step 5.
