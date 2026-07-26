# Worklog — stop reading a merge parent edge as a lifecycle step

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-25 — fix-merge-parent-task-topology (claude)

- Reproduced the finding on the pull request 13 merge range and confirmed each step of the
  mechanism: two parents, the second cut at 17c1e16 before the task was filed, no task
  record in its tree, and a passing edge from the other parent.
- Claimed the task on `main` and removed its completed pickup request in the same
  coordination commit.
- Chose the surgical shape: condition only the creation finding on a sibling-parent
  lookup. The rejected alternative was to union the `before` side across a merge's
  parents, which turns the duplicate-incarnation guard into a silent skip whenever two
  parents disagree about a task's status, so an illegal merge result would go unreported.
  `design.md` records both, and one of the new tests pins that exact hazard.
- Found that `--range` cannot be re-run in place after the repair, because it binds to the
  captured head and rejects a dirty tree. Verified the real range instead through two
  synthetic base-plus-head merge candidates — the shape a provider merge ref has and the
  one `validate_range_candidate` accepts — differing only in whether the repair is
  present: 1 finding without it, 0 with it.
- Recorded every new test's pre-repair verdict by reverting only `reconcile.py`; three of
  the six discriminate and three are regression guards.
- The pull request remains the last step.
