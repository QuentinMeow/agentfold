# Worklog — Stop the merge-ref recompute race from failing every stacked pull request

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — stop-the-merge-ref-recompute-from-failing-a-stack (claude)

- Claimed the task and moved it to `1_in-progress`; resolved and deleted
  `message-queue/needs-agent/requests/non-blocking-pick-up-stop-the-merge-ref-recompute-from-failing-a-stack.md`
  in the same coordination commit.
- Claimed from an isolated detached worktree rather than the shared `main` checkout,
  which had another agent's uncommitted edits in it at the time.
