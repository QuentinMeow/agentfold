# Worklog — make the reconciler report its own failures honestly

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — report-check-failures-honestly (claude)

- Reproduced all four audit defects before changing anything; every transcript in
  `verification.md` is a real run, including the ones that crash.
- Measured the lockout before designing the tier policy, per
  `memory/lessons/` habit of counting first: with no repository change this tree starts
  failing on 2026-08-15 (`stale-task`), 2026-08-25 (`stale-queue`), and 2027-01-23, when
  the ten memory entries sharing `Review-by: 2027-01-22` expire together. The audit
  predicted 2026-08-09 for `stale-task`; the real date differs because `days_old` reads
  filesystem mtime, which is exactly the non-determinism the backlog task calls out.
- Attempted to claim task 2026-07-22-severity-tiers-for-reconciler-findings for the
  severity split, as the brief directed. The claim is blocked by the harness itself:
  deleting its pickup request breaks `link-check` in a live queue item that names that
  path, and repairing that reference breaks `queue-resolution`. Both reproduced and
  recorded; filed as a non-blocking repair request; the severity work ships here and
  that task keeps its unfinished determinism scope. Details in `design.md`.
- Audited all three sibling worktree-gate sites named in the brief. All three
  reproduced, all three fixed, each covered by a test.
- Work happened in an isolated git worktree, so the coordination commits that
  `handbook/git-workflow.md` places directly on `main` are on the task branch instead.
