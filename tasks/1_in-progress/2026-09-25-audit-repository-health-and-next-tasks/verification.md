# Verification — Repository health and next-task assessment

**Verified:** 2026-09-25 by codex-repo-health

## Environment

```text
$ python3 --version && git --version
Python 3.14.7
git version 2.55.0
```

## Baseline suite in the adopted worktree

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1
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
PASS automation/tests/test_reconcile_provenance.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 17/17 files passed
test elapsed: 170.18s
```

## Fresh-checkout gate and suite

The clone was created from the local repository with the task branch selected. The full
suite ran at candidate `f24ed4b2bd1acda323d9ec9a6ae494f30b561bf9`. Its records were later
corrected; all runtime, hook, test, contract, template and service bytes remained identical
at revised candidate `5a696f502d4e56f3822f28cb987d2f1b62468735`.

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 tmp/repo-audit/cold-clone/automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
```
```text
$ PYTHONDONTWRITEBYTECODE=1 python3 tmp/repo-audit/cold-clone/automation/run_tests.py --jobs 1 --verbose
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
PASS automation/tests/test_reconcile_provenance.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 17/17 files passed
test elapsed: 163.79s
```

The verbose run reported these five skips:

```text
test_non_utf8_git_metadata_path_remains_redacted (__main__.WorkspaceBoundaryInspectorTests.test_non_utf8_git_metadata_path_remains_redacted) ... skipped 'filesystem or Git rejected a non-UTF-8 path'
Inertness measured, not scoped: run it on every tracked Markdown file. ... skipped 'no Git checkout: this measurement needs the real repository'
Integrity needs a view that is total, and this asserts that it is. ... skipped 'no Git checkout: this measurement needs the real repository'
Measured against this repository's own queue history, not a fixture. ... skipped 'no Git checkout: this measurement needs the real repository'
The expensive half of the inert proof: delete the records, run everything. ... skipped 'set AGENTFOLD_INERT_PROBE=1 to run the whole suite against a record-free projection'
```

## Real-corpus and history checks on the revised candidate

The linked-worktree attempt skipped all three checks because these tests require a `.git`
directory. After the disposable clone fetched and selected revised candidate `5a696f5`,
the same three checks ran there without skips.

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 tmp/repo-audit/cold-clone/automation/tests/test_reconcile_queue.py ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history -v
test_record_swallow_is_inert_on_every_live_item_in_this_repository (__main__.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository)
Inertness measured, not scoped: run it on every tracked Markdown file. ... ok
test_the_frozen_skeleton_accounts_for_every_byte_of_the_file (__main__.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file)
Integrity needs a view that is total, and this asserts that it is. ... ok
test_the_frozen_skeleton_files_no_new_refusal_on_real_history (__main__.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history)
Measured against this repository's own queue history, not a fixture. ... ok

----------------------------------------------------------------------
Ran 3 tests in 4.338s

OK
```

## Runtime-byte equality after the record corrections

```text
$ git diff --exit-code f24ed4b2bd1acda323d9ec9a6ae494f30b561bf9..5a696f502d4e56f3822f28cb987d2f1b62468735 -- automation handbook templates skills services .github AGENTS.md

```

The command produced no output and exited 0.

## Acceptance counterexample

The direct probe is recorded in the verification of task
`2026-08-18-fold-the-queue-machine-record`; its actual output was:

```text
.github/pull_request_template.md 1 fold-shape finding(s)
message-queue/open-actions.md 1 fold-shape finding(s)
templates/pull-request.md 1 fold-shape finding(s)
```

## Limits

The inherited-mutation reproduction and the five owner workflow experiments did not run.
The opt-in record-free full-suite probe and the unavailable non-UTF-8 filesystem case did
not run. No cross-vendor review ran; the pre-existing external-review authorization remains
unchanged. No Python 3.9 matrix was run because this change modifies records only. Historical
verification retained inside the six completed tasks is evidence from its stated dates.

## Independent verification

**Reviewed revision:** 5a696f502d4e56f3822f28cb987d2f1b62468735

- correctness / verify-correctness: `approve` — the disputed task remains in review throughout revised history and its completion action is reciprocal.
- requirements / verify-requirements: `approve` — source-only diagnosis is explicit; owner words, priorities and the five-scenario scope remain unchanged.
- blast radius / verify-blast-radius: `approve` — queue boundaries, generated indexes and immutable records remain valid.

Final panel: 3 of 3. Initial panel at `f24ed4b` passed 1 of 3; the two findings were repaired
before this verdict. A separate challenger independently confirmed the acceptance mismatch
and the safe unpublished-history correction. Full original and revised report text is
preserved in this task's `review-evidence/` JSON artifacts. Cross-vendor refuter: DID NOT RUN
(S2 native panel; no additional external transmission authorized).
