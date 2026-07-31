# Worklog — make the reconciler report its own failures honestly

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — report-check-failures-honestly (claude)

- Claimed the task and its child 2026-07-22-severity-tiers-for-reconciler-findings in
  the same session, on branch task/2026-07-30-report-check-failures-honestly. Both
  tasks share one branch on purpose: the severity split and the crash-exit fix rewrite
  the same exit-code path in `reconcile()`, so splitting them across branches would
  guarantee a conflict rather than avoid one.
- Work happened in an isolated git worktree, so the coordination commits that
  `handbook/git-workflow.md` places directly on `main` are on the task branch instead.
