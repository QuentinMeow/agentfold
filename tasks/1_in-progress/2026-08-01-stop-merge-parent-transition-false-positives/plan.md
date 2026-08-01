# Plan — stop reading a merge parent edge as a lifecycle transition

- [x] 1. Claim the task, move it to `1_in-progress`, and resolve its pickup request in one
      coordination commit.
- [x] 2. Record the pre-fix reproduction in `verification.md`: the merge probe transcript,
      the parent trees that prove the two governed edges exist on the incoming lineage,
      and which of the probe's findings belong to `task-admission` rather than to the
      crude `-X theirs` resolution.
- [x] 3. Add `task_status_at_other_parent` beside `task_recorded_at_other_parent` in
      `automation/reconcile/reconcile.py`, built on the same `candidate_parent_oids`
      helper so the index candidate and a commit candidate resolve identically.
- [x] 4. Condition only the transition-table finding in `task_topology_problems` on that
      lookup, leaving `before`, `after`, the rename set, the duplicate guard, the deletion
      rule, the creation rule, and the `adopting` escape untouched.
- [x] 5. Add `test_task_admission_accepts_a_merge_inheriting_an_advanced_task` over a real
      two-parent merge, and record its pre-fix verdict.
- [x] 6. Add `test_task_admission_still_rejects_an_illegal_merge_advance_past_a_sibling`,
      where a sibling parent *does* record the task but at a different status, and prove
      it fails against the weaker "recorded at other parent" shape.
- [x] 7. Re-run the merge probe with the fix applied and record its real output.
- [x] 8. Record a full `--check`, the whole test suite, and every discriminating verdict in
      `verification.md`; write `design.md` with its `## Core fit` receipt; move to
      `3_in-review`.
