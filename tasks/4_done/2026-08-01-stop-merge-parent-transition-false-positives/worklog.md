# Worklog — stop reading a merge parent edge as a lifecycle transition

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-01 — stop-merge-parent-transition-false-positives (claude)

- Filed and claimed the task off `origin/main` (`8811770`).
- Reproduced the defect before any code change: `origin/main` and
  `origin/task/2026-07-31-finish-the-replacement-ref-boundary` each report 0 findings on
  their own, and merging the two reports the `task-admission` lifecycle jump twice.
- Confirmed the diagnosis against the real object database rather than by inference:
  `84e3524`'s trunk parent `7c2854a` records
  task:2026-07-25-fix-handover-projection-code-span-copy at `1_in-progress`, its branch
  parent `ed3a9ee` records it at `4_done`, and the branch got there through `07de276`
  (`1_in-progress → 3_in-review`) and `6de7954` (`3_in-review → 4_done`). So the history
  is well-formed and the finding is a false positive, not a real violation.
- Wrote `test_task_admission_accepts_a_merge_inheriting_an_advanced_task` first and ran
  it against the unmodified reconciler: it fails with exactly the repository's own
  finding, so it discriminates.
- Added `task_status_at_other_parent` and conditioned only the transition-table finding
  on it. The exact-status match was the one real design decision: reusing the creation
  helper's `task_recorded_at_other_parent` would have been simpler and is wrong, and
  `test_task_admission_still_rejects_a_merge_advance_past_a_sibling` was written to prove
  that. Rewriting the guard to the weaker shape makes that test fail with an empty
  finding list; the inherited
  `test_task_admission_still_rejects_an_illegal_merge_advance` passes under both shapes,
  so it could not have caught the mistake.
- Dead end worth not repeating: `merge -X theirs` is not a neutral probe. Five of the
  seven reproduced findings are `-X theirs` keeping the branch's renamed queue items while
  taking `main`'s task record that links their old paths, and a plain `git merge` refuses
  the same combination outright. Isolating this task's fix needed one identical tree run
  under both reconcilers, not a comparison of two differently-resolved merges.
- The fully resolved probe reaches 0 blocking findings; `verification.md` records which
  part of that is the fix and which part is ordinary merge work the branch owner owns.
