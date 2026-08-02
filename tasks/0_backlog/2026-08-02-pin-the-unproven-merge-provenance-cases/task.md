# Pin the two merge-provenance cases whose behaviour is right but untested

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-08-02, by claude, from the closing audit of task `2026-07-24-complete-staged-merge-provenance-admission`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-pin-the-unproven-merge-provenance-cases.md`

## Goal

Two behaviours of the reconciler's merge-provenance admission are correct today and are
not held there by any test. A refactor could break either and the suite would stay green.

The audit that closed `2026-07-24-complete-staged-merge-provenance-admission` built both
cases as throwaway probes and recorded their real output in that task's `verification.md`.
A probe in a closed task's verification file is a photograph of one afternoon, not a
guarantee. Turn each into a committed regression in
`automation/tests/test_reconcile_queue.py`.

## The two cases

**Committed-range parity for a post-fork human response.**
`test_staged_merge_cannot_restore_stale_parent_over_human_response` and
`test_staged_merge_cannot_delete_concurrent_human_response` both stop at the staged merge.
Their sibling cases in the same file — `test_merge_candidate_rejects_dropped_first_parent_action`
and `test_merge_candidate_rejects_dropped_second_parent_action` — commit the merge and
re-run `check_queue_resolution` under a `base...head` `CHANGE_RANGE`, asserting the
identical finding. The two human-response tests need the same second half. The audit's
probe confirmed the findings match: restoring a stale parent over a committed response
reports `live queue action was rewritten: human response or its immutable review binding
changed after the first concrete response`, and deleting a concurrently answered item
reports `deleted unresolved queue item: human action was not committed as folding with a
concrete response`.

**An unrelated-history root.** No fixture in the queue-resolution or handover-projection
suites builds one. The file's only `--allow-unrelated-histories` merge is in
`test_task_action_origin_rechecks_imported_orphan_root`, which exercises a different check.
`parent_merge_base` in `automation/reconcile/reconcile.py` returns `None` for unrelated
parents, and `parent_supplies_absent_path` then refuses to treat absence as provenance —
neither function has a direct test. The audit's probe imported an orphan root carrying an
unclaimed deletion and an unmarked handover, and both checks refused it.

## Acceptance criteria

- [ ] `test_staged_merge_cannot_restore_stale_parent_over_human_response` commits its merge
      and asserts the same finding under a committed `base...head` range, in the shape the
      dropped-parent-action tests already use.
- [ ] `test_staged_merge_cannot_delete_concurrent_human_response` does the same.
- [ ] One new regression merges an orphan root with `--allow-unrelated-histories` and
      asserts `check_queue_resolution` refuses an unclaimed deletion imported from it.
- [ ] One new regression does the same for `check_handover_queue_projection` and an
      invalid handover created on that root.
- [ ] Each assertion names the finding it expects rather than a disjunction of substrings.
      A disjunction whose weakest branch fires on an unrelated condition is what made the
      original audit have to print findings to know what was covered.
- [ ] Each new regression fails when the behaviour it pins is removed, demonstrated by
      recording the failure output before the assertion is finalised.
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 findings and
      `python3 automation/run_tests.py` passes every file, with both real outputs in
      `verification.md`.
- [ ] `design.md` carries a complete `## Core fit` receipt if any core path changes. Adding
      tests alone may not require one; say which and why.

## Links

- The audit that found the gap, with the probe output: task `2026-07-24-complete-staged-merge-provenance-admission`
- The file the regressions belong in: `automation/tests/test_reconcile_queue.py`
- The functions with no direct test: `automation/reconcile/reconcile.py`
