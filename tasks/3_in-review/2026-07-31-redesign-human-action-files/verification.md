# Verification — Redesign every file that asks a human for attention

**Verified:** 2026-08-01 by claude

Only commands actually run and their real output. Every elision is marked
`[elided: …]` on its own line and says what was removed; nothing below is
reconstructed, predicted, or paraphrased output. Baseline for every comparison is
`025de49`, the tip of branch harness/2026-07-31-fold-answered-queue-review.

Everything here was run against the branch as it stands after its implementation and
follow-up-task commits, with only this file and the three other task records still
uncommitted. Nothing in this file was produced by a scratch copy of the repository.

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## Repository tests

```
$ python3 automation/run_tests.py
[elided: the run's per-lane preamble — worker/shard counts and the self-test and probe lanes]
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
test elapsed: 52.25s
```

The queue module on its own, for the test count:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
[elided: the progress dots and the `reconcile: 0 finding(s)` lines fixtures print]
Ran 326 tests in 86.639s

OK
```

302 of those existed at the baseline. The two the reviewed spec predicted would fail —
`test_queue_v1_requires_concrete_human_projection_context` and
`test_human_items_require_context_differences_examples_and_response` — were updated to
assert the new field name and the new heading, which is what those two assertions are
about; both pass.

## No live human item changed

This is the property the adversarial review returned DO NOT SHIP over, so it is proved
by the diff rather than argued.

```
$ git diff 025de49 HEAD -- message-queue/needs-human/
```

The command printed nothing: no file under `message-queue/needs-human/` differs from the
baseline in any byte, including the leaf `README.md`. The complete change against the
baseline is:

```
$ git diff --name-status 025de49 HEAD
M	automation/reconcile/reconcile.py
M	automation/tests/test_reconcile_queue.py
M	handbook/human-action-guide.md
M	history/AGENTS.md
M	message-queue/AGENTS.md
M	message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md
A	message-queue/needs-agent/requests/non-blocking-pick-up-countersign-the-live-human-item-migration.md
A	message-queue/needs-agent/requests/non-blocking-pick-up-derive-the-reviewed-revision-field.md
A	message-queue/needs-agent/requests/non-blocking-pick-up-record-that-a-format-migration-is-one-way.md
A	message-queue/needs-agent/requests/non-blocking-pick-up-stop-reading-none-as-an-unanswered-field.md
A	tasks/0_backlog/2026-08-01-countersign-the-live-human-item-migration/task.md
A	tasks/0_backlog/2026-08-01-derive-the-reviewed-revision-field/task.md
A	tasks/0_backlog/2026-08-01-record-that-a-format-migration-is-one-way/task.md
A	tasks/0_backlog/2026-08-01-stop-reading-none-as-an-unanswered-field/task.md
A	tasks/1_in-progress/2026-07-31-redesign-human-action-files/design.md
A	tasks/1_in-progress/2026-07-31-redesign-human-action-files/plan.md
A	tasks/1_in-progress/2026-07-31-redesign-human-action-files/task.md
A	tasks/1_in-progress/2026-07-31-redesign-human-action-files/worklog.md
M	templates/handover.md
M	templates/queue/clarification.md
M	templates/queue/decision.md
M	templates/queue/review.md
```

The one modified queue item is the redesign request this task claimed, whose `Status`
moved `open` → `in-repair` in the claim commit. The four added ones are the pickup
requests for the four deferred tasks. This run of `--name-status` does not list
`verification.md` because the file being read is the one still uncommitted while these
commands ran; it lands in the next commit.

The answered item's blob is unchanged, which is the strongest available statement that
the owner's committed answer was not touched:

```
$ git ls-tree HEAD -- message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md
100644 blob 0392d6ed28206b912cfb2cc97a733ed62b3f4048	message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md
```

## `queue_mutation_problem` carries no presentation carve-out

Every symbol the carve-out was built from is gone from the repository:

```
$ grep -rn "candidate_parent_revisions\|PRESENTATION_FROZEN\|human_attention_presentation_migration\|test_presentation_migration" automation/
$ echo "grep exit: $?"
grep exit: 1
```

What remains under that name is comment prose only:

```
$ grep -n "presentation" automation/reconcile/reconcile.py
179:# compared against; the prose standing beside it is presentation, not dependency.
194:# record, and reformatting one to match a later presentation would rewrite it.
2334:    # There is no presentation carve-out. A live item's visible text is its
4585:    presentation rules stop applying to them and they keep the schema they were
```

And the behaviour is pinned by a test that reformats a committed live item with the
format marker active and without it, and requires the same refusal both times.

## Regression tests, run by name

```
$ python3 -m unittest -v \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_reformatting_a_live_item_is_refused_with_or_without_the_marker \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_attention_marker_is_sticky_after_activation \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_attention_leaves_an_unanswered_legacy_item_alone \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_legacy_review_successor_is_still_compared_on_its_timing_prose \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_modern_review_successor_is_compared_on_the_boundary_token \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_answering_a_migrated_item_keeps_its_own_schema
test_reformatting_a_live_item_is_refused_with_or_without_the_marker (automation.tests.test_reconcile_queue.ReconcileQueueTests)
There is no presentation carve-out in `queue_mutation_problem`. ... ok
test_human_attention_marker_is_sticky_after_activation (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The marker cannot be toggled off and back on around one candidate. ... ok
test_human_attention_leaves_an_unanswered_legacy_item_alone (automation.tests.test_reconcile_queue.ReconcileQueueTests)
A live ask written before the format is governed by its own schema. ... ok
test_legacy_review_successor_is_still_compared_on_its_timing_prose (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The marker alone must not stop comparing a field the item still has. ... ok
test_modern_review_successor_is_compared_on_the_boundary_token (automation.tests.test_reconcile_queue.ReconcileQueueTests)
A review written under the format has no timing prose left to match. ... ok
test_answering_a_migrated_item_keeps_its_own_schema (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The answer must not demand the pre-rename timing field back. ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.726s

OK
```

## Negative control for the successor-timing scoping

A test that passes against both the fixed and the broken code proves nothing, so the
scoping fix was checked against its own regression. `automation/reconcile/reconcile.py`
was edited in place to compare `BOUNDARY_TIMING_FIELDS` for every human review — the
behaviour the adversarial review flagged — the one test was run, and the file was
restored. The script is `/tmp`-local scratch, not a repository artifact; the substitution
it makes is the single line quoted in the command below.

```
$ python3 <scratch script: swaps `compared_timing_fields = queue_timing_fields_for("needs-human", text)`
           for `compared_timing_fields = BOUNDARY_TIMING_FIELDS`, runs one test, restores the file>
F
======================================================================
FAIL: test_legacy_review_successor_is_still_compared_on_its_timing_prose (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The marker alone must not stop comparing a field the item still has.
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 13521, in test_legacy_review_successor_is_still_compared_on_its_timing_prose
    ), messages)
AssertionError: False is not true : []

----------------------------------------------------------------------
Ran 1 test in 0.195s

FAILED (failures=1)
restored: True
```

`[elided: the absolute path prefix of the traceback's file, replaced by `...`]`

Without the fix the changed `Until then` is not compared at all and the resolution is
accepted; with it, the finding is `review successor changes **Until then:**`.

## The placeholder hole, measured rather than asserted

Filed as task `2026-08-01-stop-reading-none-as-an-unanswered-field`. It was checked
directly rather than taken on trust, because the task claims a real human answer reads as
no answer:

```
$ python3 -c "
import sys; sys.path.insert(0, 'automation/reconcile')
import reconcile
for value in ('none', 'n/a', 'tbd', 'unknown', '______', 'looks right, continue'):
    print(repr(value), '->', reconcile.has_concrete_value(value))
"
'none' -> False
'n/a' -> False
'tbd' -> False
'unknown' -> False
'______' -> False
'looks right, continue' -> True
```

## The contract still fits its budget

```
$ wc -l message-queue/AGENTS.md
      60 message-queue/AGENTS.md
```

## What was not verified here

- **The exploit that cut the carve-out was not reproduced by me.** It was reported by an
  independent adversarial review of the previous branch tip `ef4958b`: with all seventeen
  frozen fields byte-identical, both path-frozen fields identical, both projected
  sentences whitespace-normalised prefixes of their committed values, and
  `reconcile.py --check` reporting `0 finding(s)`, a migration still changed the H1
  question, inverted `What this does not decide`, deleted a choice, flipped the
  recommendation and raised the stated confidence. I did not re-run it, because the
  response was to delete the mechanism rather than to measure it further; the deletion is
  proved above. It is recorded as a report, not as my own measurement.
- **No full future lifecycle was simulated in the new format** — publish → answer → claim
  → delete-with-receipt across multiple commits. `test_answering_a_migrated_item_keeps_
  its_own_schema` covers the answered steady state and the two successor tests cover the
  changes-requested resolution edge, but nothing walks the whole sequence. No live item
  uses the new format, so nothing in the repository depends on this today; the first item
  written in it will be the first real exercise.
- **`Confidence` and `Strongest case against this` cannot be machine-checked for
  honesty.** The reconciler confirms the grammar and non-emptiness. A weak agent can still
  produce calibrated-looking mush, and review is the only control. This is stated so it is
  not discovered later.
- **The 700-word budget was calibrated on a file that no longer exists in the branch.**
  The seven migrated files that measured 496–673 words were restored to their baseline
  bytes, so the ceiling is now carried only by the templates and by
  `test_human_attention_rejects_exceeding_the_word_budget`. Whether 700 is the right
  number will first be tested by a real item written in the format.
- **The branch history was rebuilt rather than reverted, and that is not a claim a
  command here proves.** A revert commit is itself a live-item rewrite on the staged
  edge: with the migration commit still in history and the files restored on top, the
  reconciler reported seven `queue-resolution` findings of the form "live queue action was
  rewritten". Only history in which the migration commit never existed is clean, so the
  branch was rebuilt from its claim commit `062ad01`, which is preserved unchanged along
  with `a7e9541`. The abandoned tip `ef4958b` is still reachable by object id.

## Merging onto main at `d1feea8` (2026-08-01)

The task work was merged onto main with main as the first parent, at
`d1feea863843e350a6efd95e67107c9252346f3c`. Six files conflicted; the substantive one
joined this task's action-entry schema v3 with main's new liveness schema. Both are live
in the merged tree and the whole suite covers both. On the merge commit
`b61e5df254422acd73db37529d58d3ef0f5000ae`:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

```
$ python3 automation/check_core_scope.py --range "d1feea863843e350a6efd95e67107c9252346f3c...b61e5df254422acd73db37529d58d3ef0f5000ae" --branch task/2026-07-31-redesign-human-action-files
core-scope: pass (9 core path(s), task 2026-07-31-redesign-human-action-files; independent review manual; not invoked)
```

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-07-31-redesign-human-action-files --range "d1feea863843e350a6efd95e67107c9252346f3c...b61e5df254422acd73db37529d58d3ef0f5000ae"
reconcile: 0 blocking finding(s)
```

```
$ python3 automation/run_tests.py
[... per-shard lane/selection output elided ...]
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.01s
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
test elapsed: 77.00s
```

The merge also went through the installed pre-commit hook, so `--staged` core scope, the
reconciler and the staged test lane passed on it before it existed. The commit that adds
this section touches only this file and the worklog.

One test changed for expectation rather than behaviour.
`test_entry_schema_rank_is_monotone` asserted the ordering through `entry_schema_rank`, a
ranking helper this task added; main's parameterised namespace already ranks by tuple
position through `entry_version_at_least`, so the duplicate helper was dropped and the
test — now `test_entry_schema_order_is_monotone` — asserts the same ordering, `v3`
included, through the surviving one.

## Review verdicts (when a review was explicitly run)

Not applicable. Independent core-fit review is manual and was not invoked
(`core-scope: pass (9 core path(s), task 2026-07-31-redesign-human-action-files;
independent review manual; not invoked)`). The promised human re-review is
`message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md`, which
stays `awaiting-artifact` until this work reaches its merge boundary.
