# Worklog — Correct the contract text that no longer matches the code or itself

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — reconcile-the-contracts-with-the-code (claude)

- Claimed the task, moved it to `1_in-progress`, and deleted its pickup request
  `message-queue/needs-agent/requests/non-blocking-pick-up-reconcile-the-contracts-with-the-code.md`
  in the same coordination commit.
- Work happens on branch `task/2026-08-02-reconcile-the-contracts-with-the-code` in a
  separate worktree; another session is committing to `main` concurrently. That session
  landed an eleven-task status move between the claim's `git add` and its commit, so the
  claim was made as a path-scoped partial commit and its parent is that session's commit.
- Re-verified all fourteen findings against the current branch base before editing anything.
  None was already fixed and none was refuted; two counts in the audit had gone stale
  (fourteen tasks in `1_in-progress` is now four, which strengthens finding 8 rather than
  weakening it) and are restated in `verification.md` rather than repeated.
- Repaired findings 2 and 4–12 and 14 as text; the reasoning for every one is in `design.md`.
- Finding 3 was decided in favour of rewriting the `pair` documentation rather than scoping
  `HUMAN_UNSPELLABLE_TRANSITIONS` by collaboration mode. The deciding argument is that the
  deadlock which forced human gating v1 is a property of binding a Git edge to a human
  answer, not a property of `async`, so Option B would re-admit a known unsatisfiable
  boundary in one mode. The gating ADR needed no edit: its Decision was already mode-blind.
- Finding 13 was routed rather than edited, against the task's suggested repair. Two
  contracts independently forbid editing `handbook/principles/` without a decision, and the
  live retry-loop item is a direct precedent of filing rather than fixing an outright false
  sentence in a principle. Re-verifying it turned up a second instance of the same pattern
  in `handbook/principles/design-for-forgetting.md`, so the filed item asks about the class.
- Finding 14's directory was not empty: five gitignored Python 3.7 `.pyc` files, no source.
  All seven sources are on `archive/2026-07-22-prevent-false-github-reauth`. Removed, along
  with the three dangling adapter symlinks the removal left behind.
- The acceptance criterion that needed a demonstration is in `verification.md`: two live-
  shaped items written from the corrected `templates/README.md` table are accepted, and the
  same two rewritten as the old table described them are refused with the exact finding an
  agent obeying that table would have hit.
