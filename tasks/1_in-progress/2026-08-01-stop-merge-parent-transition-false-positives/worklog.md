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
