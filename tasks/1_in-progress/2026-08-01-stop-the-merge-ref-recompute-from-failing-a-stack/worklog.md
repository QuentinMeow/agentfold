# Worklog — Stop the merge-ref recompute race from failing every stacked pull request

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — stop-the-merge-ref-recompute-from-failing-a-stack (claude)

- Claimed the task and moved it to `1_in-progress`; resolved and deleted
  `message-queue/needs-agent/requests/non-blocking-pick-up-stop-the-merge-ref-recompute-from-failing-a-stack.md`
  in the same coordination commit.
- Claimed from an isolated detached worktree rather than the shared `main` checkout,
  which had another agent's uncommitted edits in it at the time.
- Confirmed the defect by reading the two projection jobs side by side.
  `authoritative-external-action-projection` had already been repaired for the same class
  of problem and binds its candidate through the merge commit's own parents;
  `review-state-action-projection` still asserted bare equality with `github.sha`. Reused
  that binding rather than inventing a second mechanism.
- Rejected the shape the phrase "recompute race" invites — retry until the two values
  agree. After a recompute they never agree, because `github.sha` names a merge onto a base
  the pull request no longer has; that loop would spend its bound and fail anyway. Recorded
  it as the rejected option in `design.md`.
- The `MergeRefFixture` harness already in
  `automation/tests/test_github_action_projection_workflow.py` runs a step's literal `run:`
  block against a local bare repository, so the new tests exercise the real shell rather
  than a paraphrase of it. Added three: the recompute is admitted, every genuine mismatch
  still fails, and the bound is a counted loop with fail-closed bounds.
- Proved the guard bites by mutation instead of assertion: deleting the head comparison
  from a copy of the workflow turns the genuine-mismatch test red. The transcript is in
  `verification.md`.
- Two stale numbers found in the task record and left for their owners: the premise cites
  a decision queue item that was answered and deleted (its outcome is
  `memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md`,
  and another agent is repairing the citation), and the acceptance criterion asks for
  `11/11` test files when the suite now has 12.
- Filed nothing in `message-queue/`: the task's `Queue actions` is `none` and this change
  raises no question for the owner.
