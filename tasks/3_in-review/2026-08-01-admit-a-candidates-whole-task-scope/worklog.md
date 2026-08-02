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

## 2026-08-01 — integration pass, rebase onto main (claude)

- This branch was based on harness/2026-07-31-fold-answered-queue-review, which is itself
  one of the pull requests this change unblocks. That is a cycle: the fix cannot reach the
  branches that need it while it sits on one of them. Checked whether the dependency was
  real by diffing file sets — the four commits of the base branch and the seven of this one
  share no file except `roadmap/current-state.md` — and then by rebasing onto
  `88117705c64caa7fe691e485937bc6ceece069f5`. No code dependency exists, so the branch now
  sits directly on `main` and can land first and alone.
- Two conflicts, both against `main` rather than the old base, plus one record repair the
  new base forced. All three, and the re-run of every gate on the new base, are section 7
  of `verification.md`.
- The record repair is worth naming: the session handover's `Needs your attention` section
  projected the live human queue of the old base, which is not the live human queue of
  `main`. It was rewritten inside the commit that creates the handover, not in a later one,
  because modifying a handover after its creating commit is itself a reconciler finding.
