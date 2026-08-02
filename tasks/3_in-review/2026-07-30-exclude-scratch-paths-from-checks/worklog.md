# Worklog — exclude scratch paths from the reconciler's filesystem walks

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — file, claim, and fix (claude)

- Filed the task in `0_backlog` with its canonical pickup request, then claimed it in
  this session (no other agent was contending for it).
- Reproduced: a copy of the root `AGENTS.md` under `tmp/` (untracked, git-ignored) trips
  `[agents-budget]` on `--check`; also reproduced with a plain over-budget file nested
  under `tmp/scratch-clone/` to match the "stray clone" report.
- Traced the mechanism to four filesystem-walking sites that scan the working tree for
  untracked content (to warn before `git add`), none of which consulted `.gitignore`:
  `live_markdown_files`, `live_queue_items`, `live_handover_paths`, and
  `check_task_structure`'s inline `tasks/` walk. `check_links` already worked around one
  instance with its own `LINK_SKIP_DIRS` special case; `check_agents_budget` had none.
  Three other filesystem-walking fallbacks (`live_task_directories`,
  `live_conversation_directories`, `memory_entries`) only run when `.git` is entirely
  absent, so they were not in scope.
- Added `path_is_git_ignored`, backed by one cached `git ls-files --others --ignored
  --exclude-standard --directory -z` call per reconciler invocation (mirrors the
  existing index/HEAD snapshot cache), and applied it at the untracked half of each of
  the four sites. Removed the now-redundant "tmp" entry from `check_links`'s
  `LINK_SKIP_DIRS`, since it duplicated the fix one layer up and inconsistently
  exempted a force-added tracked `tmp/` file that `check_agents_budget` would already
  check.
- Added a regression test pairing an ignored scratch file (no finding) with a tracked
  file at a path that also matches an ignore rule (still a finding), using real Git
  (the in-process fixture writer declines any worktree carrying a `.gitignore`).
- Surprise: creating the task directly in `1_in-progress` (as first drafted) tripped the
  reconciler's own `task-admission` check ("new task was created directly in
  1_in-progress"). Restructured into two commits — file in `0_backlog` with its pickup
  request, then claim into `1_in-progress` — to satisfy the real lifecycle topology
  the reconciler enforces.
