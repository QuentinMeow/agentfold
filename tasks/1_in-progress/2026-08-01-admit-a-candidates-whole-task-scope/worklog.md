# Worklog — let a candidate carry more than one task

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-01 — admit-a-candidates-whole-task-scope (claude)

- Filed and claimed the task off the harness/2026-07-31-fold-answered-queue-review branch,
  whose own pull request (#45) is one of the six blocked by it.
- Reproduced both halves of the contradiction locally before changing anything. Both
  transcripts are in `verification.md`.
- The reported scopes in the task brief were partial. Pull request 41 maps to five tasks,
  not two, and pull request 48 to five, not two. The real sets are in `design.md`.
- Pull request 46 turned out not to be a gate problem at all: its branch is named
  task/2026-07-31-redo-stranded-review-disposition and that task's record exists in no
  commit on any branch. The repaired gate still refuses it, with a message that says so.
- The first version of the boundary repair skipped **every** action the range filed and
  broke a pre-existing test, `test_git_range_approval_satisfies_merge_only_for_queue_only_tail`.
  That test was right: an action carrying a committed human response is the boundary's
  receipt, and its freshness is exactly what the boundary validates. The rule was narrowed
  to unanswered actions and a test named for that distinction was added.
- The branch was created before the task slug was chosen, so it started as
  task/2026-08-01-repair-contradictory-task-scope-gates. The core-scope gate caught the
  mismatch against the task folder immediately; the branch was renamed.
- `automation/AGENTS.md` sits exactly on its 60-line budget, so the two bullets that gained
  clauses were rewrapped to pay for them rather than any other bullet being cut.
- Deliberately not fixed, and written down in `design.md`: a `task:<id>` merge boundary
  still activates for a non-task branch that merely edits `<id>`'s record. That is
  over-broad but repairable; the filing case had no legal exit at all, which is why it was
  the one repaired here.
