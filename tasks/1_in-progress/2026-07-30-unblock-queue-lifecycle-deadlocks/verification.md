# Verification — give claimed agent queue items and generated retries a legal way out

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

Every reproduction below is re-runnable: each defect is reproduced by a regression test in
`automation/tests/test_reconcile_queue.py`, so reverting the fix and running the named
test reproduces the original failure with the reconciler's own message. The revert used
for each "before" block is `git stash push automation/reconcile/reconcile.py`, which
leaves the new tests in place against the unfixed reconciler.

## Bug 1 before the fix — the claim-before-evidence deadlock

```
$ git stash push -q automation/reconcile/reconcile.py
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_claimed_agent_retry_may_establish_its_resolution_evidence automation.tests.test_reconcile_queue.ReconcileQueueTests.test_live_agent_request_may_establish_its_resolution_evidence
FF
======================================================================
FAIL: test_claimed_agent_retry_may_establish_its_resolution_evidence (automation.tests.test_reconcile_queue.ReconcileQueueTests)
Claiming first and working the evidence out second must have an exit.
----------------------------------------------------------------------
AssertionError: Lists differ: [] != [<reconcile_queue.Finding object at 0x10160a950>]
- []
+ [<reconcile_queue.Finding object at 0x10160a950>] : ['deleted unresolved queue item: action identity or response changed after it was claimed']

======================================================================
FAIL: test_live_agent_request_may_establish_its_resolution_evidence (automation.tests.test_reconcile_queue.ReconcileQueueTests)
An agent request filed without the field must not be undeletable.
----------------------------------------------------------------------
AssertionError: Lists differ: [] != [<reconcile_queue.Finding object at 0x10160a290>]
- []
+ [<reconcile_queue.Finding object at 0x10160a290>] : ['live queue action was rewritten: action identity changed while the queue item remained live']

----------------------------------------------------------------------
Ran 2 tests in 0.427s

FAILED (failures=2)
```

The second failure settles the sub-case the audit marked suspected: an ordinary
`needs-agent` request cannot even have `**Resolution evidence:**` added while it is live,
so one filed without the field is undeletable from birth.

All three exits were confirmed closed against the same claimed item, using a scratch
driver over the same code path the test uses (`check_queue_resolution` on a staged
worktree). Its real output:

```
=== BUG 1 / generated retry: claim first, then evidence ===
--- exit `evidence-added`
    [queue-resolution] .../blocking-reconcile-stale-task-...md: deleted unresolved queue item: action identity or response changed after it was claimed
--- exit `evidence-removed`
    [queue-resolution] .../blocking-reconcile-stale-task-...md: deleted unresolved queue item: missing non-queue **Resolution evidence:** file path
--- exit `status-reset`
    [queue-resolution] .../blocking-reconcile-stale-task-...md: live queue action was rewritten: committed in-repair lifecycle claim regressed to open
```

## Bug 2 before the fix — a retry that outlives its finding and blocks every merge

```
$ git stash push -q automation/reconcile/reconcile.py
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_every_emitted_check_id_is_registered automation.tests.test_reconcile_queue.ReconcileQueueTests.test_stale_task_retry_is_collected_once_its_finding_clears
FF
======================================================================
FAIL: test_every_emitted_check_id_is_registered (automation.tests.test_reconcile_queue.ReconcileQueueTests)
An unregistered id strands its retry and then blocks every merge.
----------------------------------------------------------------------
AssertionError: Items in the second set but not the first:
'stale-task' : every emitted check id must be a key in CHECKS so its retry can be certified as cleared and garbage-collected

======================================================================
FAIL: test_stale_task_retry_is_collected_once_its_finding_clears (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The accidental garbage-collection escape that outlived its finding.
----------------------------------------------------------------------
AssertionError: Tuples differ: (0, 1) != (0, 0)

First differing element 1:
1
0

----------------------------------------------------------------------
Ran 2 tests in 0.010s

FAILED (failures=2)
```

`(0, 0)` is `file_retries([])` reporting that nothing was collected after the finding was
fixed: the retry survived. The consequence, under the arguments PR CI runs
(`--check --at-transition merge --branch task/<id>`, `.github/workflows/harness.yml:53`),
with the active task scoped to a task the retry has nothing to do with:

```
$ git stash push -q automation/reconcile/reconcile.py
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_collected_stale_task_retry_no_longer_blocks_every_merge
AssertionError: Lists differ: [] != [<reconcile_queue.Finding object at 0x107b49510>]
- []
+ [<reconcile_queue.Finding object at 0x107b49510>] : ['unresolved blocking action reached transition:merge']

----------------------------------------------------------------------
Ran 1 test in 0.011s

FAILED (failures=1)
```

## Every new test, before the fix

Nine of the thirteen new tests fail without the fix. The remaining four assert invariants
that must hold both before and after — evidence is still mandatory at deletion, a claim
receipt is still not transferable, and refiling still refuses an untrusted lookalike.

```
$ git stash push -q automation/reconcile/reconcile.py
$ python3 -m unittest <the thirteen new tests>
ERROR: test_registry_aliases_do_not_double_report_a_finding (...)
ERROR: test_queue_resolution_retry_is_never_garbage_collected (...)
AttributeError: module 'reconcile_queue' has no attribute 'generated_retry_collectable'
ERROR: test_generated_retry_predeclares_evidence_without_overwriting_it (...)
AttributeError: module 'reconcile_queue' has no attribute 'RETRY_EVIDENCE_PLACEHOLDER'
FAIL: test_claimed_agent_retry_may_establish_its_resolution_evidence (...)
FAIL: test_live_agent_request_may_establish_its_resolution_evidence (...)
FAIL: test_human_claim_still_freezes_its_resolution_evidence (...)
FAIL: test_every_emitted_check_id_is_registered (...)
FAIL: test_stale_task_retry_is_collected_once_its_finding_clears (...)
FAIL: test_refiling_a_deleted_retry_keeps_its_rejection_notes (...)
Ran 12 tests in 1.122s
FAILED (failures=6, errors=3)
```

(The twelve above, plus `test_collected_stale_task_retry_no_longer_blocks_every_merge`
shown in its own block, are the thirteen.)

## After the fix — full repository suite

```
$ python3 automation/run_tests.py
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
test elapsed: 28.97s
```

```
$ python3 -m unittest automation.tests.test_reconcile_queue
----------------------------------------------------------------------
Ran 314 tests in 64.743s

OK
```

No pre-existing test needed changing. The receipt-transferability tests that guard the
invariant this fix had to preserve —
`test_new_identical_action_cannot_borrow_another_claim_receipt`,
`test_merge_cannot_borrow_claim_from_other_parent_slug`,
`test_claim_receipt_survives_later_timing_escalation`,
`test_agent_claim_receipt_survives_later_slug_rename`,
`test_human_claim_receipt_survives_later_slug_rename`, and
`test_slug_rename_claim_lineage_fails_closed_for_duplicate_actions` — all pass unchanged.

## After the fix — reconciler on this repository

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
exit=0
```

`--file-retries` is not wired into the hook or CI, so it was exercised by hand on this
repository to confirm it is safe to run: with no findings it files nothing and collects
nothing, and leaves the working tree clean apart from the two source files this task
changed.

```
$ python3 automation/reconcile/reconcile.py --check --file-retries
retries: 0 filed/refreshed, 0 cleared
reconcile: 0 finding(s)
exit=0
$ git status --short
M  automation/reconcile/reconcile.py
M  automation/tests/test_reconcile_queue.py
```
