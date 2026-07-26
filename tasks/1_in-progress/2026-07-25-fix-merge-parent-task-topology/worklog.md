# Worklog — stop reading a merge parent edge as a lifecycle step

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-25 — fix-merge-parent-task-topology (claude)

- Reproduced the finding on the pull request 13 merge range and confirmed each step of the
  mechanism: two parents, the second cut at 17c1e16 before the task was filed, no task
  record in its tree, and a passing edge from the other parent.
- Claimed the task on `main` and removed its completed pickup request in the same
  coordination commit.
