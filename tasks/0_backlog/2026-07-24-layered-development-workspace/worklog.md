# Worklog — layered development workspace

## 2026-07-24 — layered-workspace-research-handoff (codex)

- Read the queue, relevant handovers, roadmap, current task branch, and live GitHub
  state; PR #7 remains in review and must not merge before its queue-owned reviews.
- Delegated independent research on workspace composition and privacy/developer UX.
  Both reviews rejected ignores, hooks, linked worktrees, symlinks, LFS, and a private
  branch as confidentiality boundaries.
- Recorded the owner's platform answer: macOS and Linux are the baseline; Windows is
  included only when cheap and non-distorting.
- A linked-worktree pre-commit test exposed a separate Git-environment isolation bug.
  The repository was restored exactly, and the repair is filed independently so the
  workspace task does not hide an urgent safety prerequisite.
- Filed the task pickup and full requirements for another agent; no architecture or
  first-slice implementation was committed in this session.
