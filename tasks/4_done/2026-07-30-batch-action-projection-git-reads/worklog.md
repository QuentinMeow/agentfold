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
- Implemented as a per-run snapshot rather than a process-global one, so no run answers
  from a view the repository has moved past. The four entry points open one reentrant
  scope; outside every scope the old read-per-lookup behaviour stands.
- The gate went from 84 Git processes and 0.707s to 2 and 0.028s on this repository, with
  byte-identical output across 17 probes.
- The complete suite did not get faster. Interleaved rounds put the two sides inside each
  other's noise, because this module is not the critical path once the suite is sharded.
  Recorded as such instead of quoting the single flattering run.
- One deliberate behaviour change: an empty path prefix now raises `ValueError` instead of
  a `RuntimeError` from Git. No caller passes one.
- Trap worth not repeating: a probe that chained `git stash pop` behind `&&` after a
  command that could fail left the working tree stashed when the probe raised. A second
  worktree at the comparison revision is the safe way to measure two revisions at once.
