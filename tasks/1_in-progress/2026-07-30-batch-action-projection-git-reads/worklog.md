# Worklog — read each repository view once per action-projection run

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — clean-stale-tasks-and-batch-projection-reads (claude)

- Filed and claimed after measuring, not before. The prior session's handover named this
  module as the next candidate for in-process fixture history on a static count of 96
  `add` and 23 `commit` call sites. A runtime count over the module found 1,496 Git
  spawns, of which the fixture helper contributes 161. The remaining 1,288 come from
  `git_output` inside the gate under test.
- The attribution that redirected the work: `ls-files` 700, `cat-file` 304, `show` 182,
  `ls-tree` 72, all from `automation/check_action_projection.py`.
