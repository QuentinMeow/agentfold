# Verification — linked-worktree bootstrap concurrency

**Verified:** 2026-08-03 by codex / sol-high implementer

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Focused linked-worktree and failure-path tests

```
$ python3 automation/tests/test_install.py -v
test_already_executable_hook_keeps_git_index_stat_cache_clean (__main__.InstallTests) ... ok
test_correct_shared_hook_config_is_not_rewritten (__main__.InstallTests) ... ok
test_persistent_shared_config_lock_never_reports_success (__main__.InstallTests) ... ok
test_real_adapter_path_is_preserved_and_fails_with_one_actionable_error (__main__.InstallTests) ... ok
test_six_fresh_and_twelve_repeated_concurrent_linked_worktree_installs (__main__.InstallTests) ... ok
test_stale_symlink_replaced_by_real_file_during_observation_is_preserved (__main__.InstallTests) ... ok
test_symlink_creation_marks_only_skill_targets_as_directories (__main__.InstallTests) ... ok
test_temporary_shared_config_lock_is_retried_until_config_is_verified (__main__.InstallTests) ... ok
test_worktree_hook_override_is_converged_without_rewriting_common_config (__main__.InstallTests) ... ok

----------------------------------------------------------------------
Ran 9 tests in 8.036s

OK
```

## Stat-cache regression canary

The fixed installer passes without any pre-install Git inspection or index refresh:

```
$ python3 automation/tests/test_install.py InstallTests.test_already_executable_hook_keeps_git_index_stat_cache_clean -v
test_already_executable_hook_keeps_git_index_stat_cache_clean (__main__.InstallTests) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.401s

OK
```

The same corrected test fails against a safe copy whose installer restores the parent
revision's unconditional `chmod`:

```
$ python3 /private/tmp/agentfold-stat-cache-canary/automation/tests/test_install.py InstallTests.test_already_executable_hook_keeps_git_index_stat_cache_clean -v
test_already_executable_hook_keeps_git_index_stat_cache_clean (__main__.InstallTests) ... FAIL

======================================================================
FAIL: test_already_executable_hook_keeps_git_index_stat_cache_clean (__main__.InstallTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/agentfold-stat-cache-canary/automation/tests/test_install.py", line 220, in test_already_executable_hook_keeps_git_index_stat_cache_clean
    self.assertEqual(0, dirty.returncode, dirty.stdout + dirty.stderr)
AssertionError: 0 != 1 :

----------------------------------------------------------------------
Ran 1 test in 1.584s

FAILED (failures=1)
```

The test waits across the filesystem timestamp boundary but performs no Git read before
bootstrap. That makes the unnecessary `chmod` change cached ctime deterministically
without normalizing the state under test.

## Corrected-test staged lane

```
$ GIT_INDEX_FILE=/private/tmp/agentfold-bootstrap-canary-final-index-20260803 python3 automation/run_tests.py --staged
test lane: staged
test reason: every staged path maps to its registered test owners
staged paths: 1
  automation/tests/test_install.py -> test_install.py
selected test files:
  automation/tests/test_install.py
PASS automation/tests/test_install.py
tests: 1/1 files passed
test elapsed: 6.79s
```

## Isolated staged lane

```
$ GIT_INDEX_FILE=/private/tmp/agentfold-bootstrap-stat-cache-index-20260803 python3 automation/run_tests.py --staged
test lane: staged
test reason: every staged path maps to its registered test owners
staged paths: 2
  automation/install.py -> test_check_core_scope.py, test_install.py
  automation/tests/test_install.py -> test_install.py
selected test files:
  automation/tests/test_check_core_scope.py
  automation/tests/test_install.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_install.py
tests: 2/2 files passed
test elapsed: 6.57s
```

## Test-runner ownership and isolation tests

```
$ python3 automation/tests/test_run_tests.py -v
----------------------------------------------------------------------
Ran 67 tests in 6.845s

OK (skipped=1)
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.00s
```

The one skip is the test file's explicit `AGENTFOLD_INERT_PROBE=1` opt-in for rerunning
the entire suite against a record-free projection.

## Full repository suite

```
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
test elapsed: 73.77s
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Exact GitHub merge candidate after the stat-cache repair

```
$ python3 automation/install.py && git diff-files --quiet --ignore-submodules=all -- && python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe --range 73492c532d8b3ff5fd21402111e4bc7df32eb5a6...e0508b61729fd0914dbcc44180ccb18b07488443
git hooks (common repository): core.hooksPath -> automation/hooks (already configured; no write)
git hooks (this worktree): effective core.hooksPath -> automation/hooks (already effective; no write)
CLAUDE.md shims (this worktree): 12 in place
skill adapters (this worktree): .claude, .cursor, .agents -> skills/
install: done (run once in every linked worktree; safe to rerun when skills or AGENTS.md files change)
reconcile: 0 blocking finding(s)
```

The command ran in a freshly added detached worktree at GitHub merge candidate
`2f90660f33475c7df0b433355d12c41775ea7e3f`. No Git status, diff, or index-refresh
command ran between checkout and bootstrap; the raw `git diff-files` guard produced no
output and exited 0 before the range-bound reconciler ran.

## Actual linked-worktree rerun

```
$ python3 automation/install.py
git hooks (common repository): core.hooksPath -> automation/hooks (already configured; no write)
git hooks (this worktree): effective core.hooksPath -> automation/hooks (already effective; no write)
CLAUDE.md shims (this worktree): 12 in place
skill adapters (this worktree): .claude, .cursor, .agents -> skills/
install: done (run once in every linked worktree; safe to rerun when skills or AGENTS.md files change)
```
