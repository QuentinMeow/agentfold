# Worklog — cache the reconciler's Git object reads

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — claim (claude)

- Claimed and moved to `1_in-progress`; the pickup request is resolved in this commit.
- Measured before planning anything: 102 of one `--check` run's Git spawns are per-path
  `ls-tree`, concentrated in three checks. Counts and times are in `design.md`.
- Scope is the caching only. The unmerged branch
  task/2026-07-26-resolve-queue-items-whose-evidence-already-merged carried both the
  caching and a resolution-evidence rule; the rule is being discarded and is not in this
  task.
