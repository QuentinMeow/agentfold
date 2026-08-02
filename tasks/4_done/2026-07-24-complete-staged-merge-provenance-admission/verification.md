# Verification — complete staged-merge provenance admission

**Verified:** 2026-08-02 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

Nothing in this task was implemented by this session. Every line below is a reading or a
re-run of `main`, taken to decide whether the task's criteria were already discharged.

## The implementation is on main

```
$ grep -n "^def newly_added_handovers\|^def handover_current_incarnation_text\|^def check_handover_queue_projection\|^def check_queue_resolution" automation/reconcile/reconcile.py
4609:def check_queue_resolution():
7272:def newly_added_handovers():
7701:def handover_current_incarnation_text(rel):
8080:def check_handover_queue_projection():

$ git log --all --oneline -G"handover_current_incarnation_text" -- automation/reconcile/reconcile.py | tail -1
aca7014 harness: harden queue snapshot boundaries

$ git branch -a --contains aca7014 | head -1
* main
```

## The four named regressions, run

```
$ TMPDIR=<scratch> python3 -m unittest -v \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_merge_rechecks_invalid_side_handover_creation \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_merge_rechecks_invalid_deleted_side_handover_creation \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_range_governs_handover_deleted_and_readded_at_same_path \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_merge_rechecks_duplicate_path_side_handover_creation \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_merge_cannot_restore_stale_parent_over_human_response \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_merge_cannot_delete_concurrent_human_response \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_merge_preserves_second_parent_handover_incarnation
test_staged_merge_rechecks_invalid_side_handover_creation ... ok
test_merge_rechecks_invalid_deleted_side_handover_creation ... ok
test_range_governs_handover_deleted_and_readded_at_same_path ... ok
test_staged_merge_rechecks_duplicate_path_side_handover_creation ... ok
test_staged_merge_cannot_restore_stale_parent_over_human_response ... ok
test_staged_merge_cannot_delete_concurrent_human_response ... ok
test_staged_merge_preserves_second_parent_handover_incarnation ... ok

----------------------------------------------------------------------
Ran 7 tests in 14.183s

OK
```

## What those regressions actually assert

Passing is not the same as covering. `test_staged_merge_rechecks_duplicate_path_side_handover_creation`
asserts a three-way disjunction, and one disjunct ("reuses a path") would fire on the path
collision alone and prove nothing about creation snapshots. A probe re-ran the fixtures
with the findings printed rather than asserted over, so the real messages could be read:

```
$ TMPDIR=<scratch> python3 <scratch>/probe.py     # re-runs each test with the finding list printed
=== test_staged_merge_rechecks_duplicate_path_side_handover_creation
    reuses a path that already has a committed governed v1 handover incarnation at 556391a2e51dbcbdef29e93b8683080251dfc9e8
    new handover is not an exact projection of the live human queue: not live message-queue/needs-human/reviews/future-blocking-review-release.md
=== test_staged_merge_rechecks_invalid_side_handover_creation
    missing exact **Queue projection:** v1 schema marker
    Needs your attention has prose but no canonical needs-human queue link
=== test_staged_merge_cannot_restore_stale_parent_over_human_response
    live queue action was rewritten: human response or its immutable review binding changed after the first concrete response
=== test_staged_merge_cannot_delete_concurrent_human_response
    deleted unresolved queue item: human action was not committed as folding with a concrete response
=== test_merge_rechecks_invalid_deleted_side_handover_creation
    missing exact **Queue projection:** v1 schema marker
    Needs your attention has prose but no canonical needs-human queue link
=== test_range_governs_handover_deleted_and_readded_at_same_path
    missing exact **Queue projection:** v1 schema marker
    Needs your attention has prose but no canonical needs-human queue link
```

The second finding in the duplicate-path case is the one that matters. That queue file
exists on the trunk branch and is present in the merged tree; it is absent only from the
side branch that created the handover. Reporting it "not live" is therefore only reachable
if the side add was validated against the side branch's own queue snapshot rather than the
merge result. That is criterion 1's "queue snapshot at the add commit", proved rather than
inferred.

## The two halves of criterion 4 no named regression reaches

Two of criterion 4's three named tests assert only on the staged merge, and none of them
builds an unrelated history. A probe carried both human-response fixtures one commit
further into a committed range, and built an orphan root imported with
`--allow-unrelated-histories`:

```
$ TMPDIR=<scratch> python3 <scratch>/probe4.py
test_range_parity_stale_parent_over_human_response ... ok
test_range_parity_delete_concurrent_human_response ... ok
test_unrelated_history_root_queue_and_handover ... ok

----------------------------------------------------------------------
Ran 3 tests in 4.970s

OK
RANGE stale-parent-over-human-response: ['live queue action was rewritten: human response or its immutable review binding changed after the first concrete response']
RANGE delete-concurrent-human-response: ['deleted unresolved queue item: human action was not committed as folding with a concrete response']
STAGED unrelated-root queue-resolution: ['deleted unresolved queue item: agent action was not committed as in-repair before deletion']
STAGED unrelated-root handover-projection: ['missing exact **Queue projection:** v1 schema marker', 'Needs your attention has prose but no canonical needs-human queue link']
  (handover was history/conversations/2026-07-23-1200PDT-orphan-root/handover.md )
```

The committed range emits exactly the finding the staged merge emitted, in both
human-response cases — that is the parity the criterion asks for. The unrelated-history
root is admitted through both checks and refused by both.

## The complete queue suite

```
$ TMPDIR=<scratch> python3 -m unittest -b automation.tests.test_reconcile_queue
----------------------------------------------------------------------
Ran 438 tests in 307.038s

OK
exit=0
```

## The repository runner

```
$ python3 automation/run_tests.py
test lane: full
test reason: full suite requested
...
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 12/12 files passed
test elapsed: 121.11s
python3 automation/run_tests.py  227.20s user 247.02s system 389% cpu 2:01.62 total
```

## The reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
python3 automation/reconcile/reconcile.py --check  11.01s user 6.76s system 57% cpu 31.136 total
exit=0
```

## Criterion to evidence

| Criterion | Discharged by | Note |
|---|---|---|
| 1. Staged merges and committed ranges validate every governed handover add edge against that add commit's exact handover, queue, and schema snapshot | Handover snapshot: `test_staged_merge_rechecks_invalid_side_handover_creation` (staged), `test_staged_merge_preserves_second_parent_handover_incarnation` (staged **and** `left...merged` range, asserting `handover_current_incarnation_text` equals the second parent's original bytes). Queue snapshot: the "not live" finding printed above. Schema snapshot: `test_root_range_preserves_handover_created_before_schema_activation` and `test_root_range_governs_handover_restored_after_schema_activation` | The single named test covers only the staged handover half; the criterion is discharged by the family, not by that test alone |
| 2. A handover added and deleted before the candidate tip cannot bypass projection admission | `test_merge_rechecks_invalid_deleted_side_handover_creation` | Asserts the same subject and message in the staged merge and in the `left...merged` range. Covers the criterion exactly |
| 3. Independent same-path, same-bytes handover creations cannot hide an invalid parent history or create an ambiguous immutable incarnation | `test_staged_merge_rechecks_duplicate_path_side_handover_creation` for the hidden invalid history, `test_range_rejects_valid_v1_handover_readded_at_same_path` and `test_staged_rejects_valid_v1_handover_readded_at_same_path` for the ambiguous incarnation, `test_range_governs_handover_deleted_and_readded_at_same_path` and `test_staged_merge_rechecks_side_handover_reincarnation` for delete-and-readd | The named duplicate-path test produces both findings, not just the path collision |
| 4. Unrelated-history roots and exact-parent queue resolutions retain staged/range parity without dropping post-fork human responses | Exact-parent parity: `test_merge_candidate_rejects_dropped_first_parent_action` and `test_merge_candidate_rejects_dropped_second_parent_action`, each asserting one identical finding staged and in range. Post-fork human responses: `test_staged_merge_cannot_restore_stale_parent_over_human_response` and `test_staged_merge_cannot_delete_concurrent_human_response`, plus the range probe above. Unrelated-history root: the probe above | **Behaviour discharged; coverage partial.** See the gap below |
| 5. Focused regressions, the complete queue suite, the repository runner, and the reconciler all pass with their real output recorded | Every block above | 7 focused, 438 queue, 12/12 files, 0 blocking findings |

## The one gap this audit found

Criterion 4's behaviour holds — the probe proves it — but two sub-cases have no committed
regression pinning them:

- committed-range parity for the two post-fork human-response fixtures (both named tests
  stop at the staged merge), and
- any unrelated-history root in the queue-resolution or handover-projection suites. The
  only `--allow-unrelated-histories` fixture in `automation/tests/test_reconcile_queue.py`
  is `test_task_action_origin_rechecks_imported_orphan_root`, which exercises a different
  check.

A refactor could break either without a test noticing. That is filed as task
`2026-08-02-pin-the-unproven-merge-provenance-cases` rather than left inside this record,
because a closed task's verification file is not where a live coverage hole should live.

## Review verdicts (when a review was explicitly run)

No review panel was run. This is a records-only disposition of a task whose implementation
was already merged and independently reviewed on its own branch; nothing in this session
changed behaviour, and the `## Core fit` receipt is unneeded because no core path changed.
