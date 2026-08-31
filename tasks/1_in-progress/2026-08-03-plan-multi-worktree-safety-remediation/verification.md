# Verification — multi-worktree safety remediation plan

**Verified:** 2026-08-31 by codex

Only commands actually run and their real output are recorded here. This verifies the
records-only design candidate; it does not verify the deferred behavior changes or
disposable workflow scenarios.

## Full repository suite

```
$ python3 automation/run_tests.py --verbose
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_install.py
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
tests: 16/16 files passed
test elapsed: 52.40s
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
```

The six advisories predate this candidate: five describe line continuations in two frozen
human decisions, and one groups nine older questions that cannot be rewritten in place.

## Staged-path gate

```
$ python3 automation/check_core_scope.py --staged
core-scope: no core changes (independent review manual; not invoked)
$ python3 automation/run_tests.py --staged --verbose
test lane: staged
test reason: every staged path is a record path no test reads
selected test files:
  (none)
no discovered test file can be affected by the staged change
tests: 0/0 files passed
test elapsed: 0.01s
```

The `0/0` result is an explicit empty selection, not evidence that a test exercised these
records; the complete suite above is the repository-wide regression check.

## Clean Git clone

```
$ git clone --no-local --branch agents/2026-08-31-prove-and-land-the-common-8dba/parent-design /Users/quentinmiao/code/agentfold /private/tmp/agentfold-git-clone.yEORUx
Cloning into '/private/tmp/agentfold-git-clone.yEORUx'...
$ python3 automation/install.py
install: done (run once in every linked worktree; safe to rerun when skills or AGENTS.md files change)
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_install.py
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
tests: 16/16 files passed
test elapsed: 52.13s
```

## First fresh-context review

Two reviewers accepted the requirements and human-workflow lenses. The repository-contract
reviewer blocked publication because the first draft overstated one exact task-start gate as
applying to every new child and its worklog lacked resolvable evidence links. The draft was
repaired before publication; final revision-bound verdicts are recorded only after the
repaired bytes are committed and reviewed.
