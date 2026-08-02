# Worklog — record that a format migration is one-way

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — backlog disposition audit (claude)

Claimed in order to fold it into its parent and close it. Both halves of the fold
condition were checked before anything was moved.

- This task's own `## Goal` ends: "This task is only worth doing if that migration
  proceeds. If the eight legacy items age out and no live item is ever rewritten, close it
  as not-needed with that reason recorded." So the author already decided the disposition;
  the only open question was whether it should be closed empty or folded.
- The parent, `2026-08-01-countersign-the-live-human-item-migration`, really does bind the
  requirement: its acceptance criteria contained the line "`design.md` accounts for the
  one-way property recorded in task
  `2026-08-01-record-that-a-format-migration-is-one-way`". That was the condition for
  folding rather than reporting a mismatch, and it held.
- The parent is unclaimed in `0_backlog` and the migration has not begun, so the trigger
  condition ("only worth doing if that migration proceeds") is unmet today and closing is
  the author's own instruction rather than this session's judgement.

What was carried across, so nothing is lost:

- The symmetry argument in full — that a live-item rewrite mechanism admits exactly one
  edge, that reverting it is a second rewrite on an edge whose parent already has the
  marker active, that `queue_mutation_problem` therefore refuses it as "action identity
  changed while the queue item remained live", and that this is a property to design
  around rather than a rule to loosen — is now a section of the parent's `task.md`,
  headed "The migration is one-way, and the recovery path has to be chosen here".
- This task's four substantive acceptance criteria did not evaporate. The `git revert`
  reproduction, the choice between a countersigned reversal edge and a supersede-based
  recovery path, the reasoning for rejecting the other, and the end-to-end fixture are now
  the body of the parent criterion that replaced the link. The parent already required a
  `design.md`, a `verification.md` with real output, and a core-fit receipt, so no
  separate criterion of this task's needed carrying.

Closing this removes a link hop without removing an obligation: whoever performs the
migration now reads the constraint in the same file as the work it constrains.
