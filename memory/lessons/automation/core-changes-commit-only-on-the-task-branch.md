# Land core changes from a helper worktree as patches on the task branch

**Description:** The core-scope gate accepts core changes only on a `task/<id>` branch with a valid design receipt, so a helper worktree on any other branch cannot commit them; hand its work back as patches and commit in the task worktree
**Area:** automation
**Last-confirmed:** 2026-09-04
**Review-by:** 2027-03-03

## Failure

On 2026-09-04 two writer agents worked in child worktrees on `agents/<run>/<unit>` branches, as
the orchestration skill lays them out. Their commits of `automation/reconcile/reconcile.py`,
`templates/`, and contract files were refused by the pre-commit hook with "core changes require a
`task/<task-id>` branch and matching task folder", and a second attempt on the right branch was
refused because the task's `design.md` core-fit receipt was not yet valid.

## Root cause

`automation/check_core_scope.py --staged` derives the task from the branch name alone, and it
validates the task's `design.md` receipt before any core path may be committed. A child branch
has neither.

## Rule

Let helper worktrees produce `git diff` patches (records-only commits may be cherry-picked), and
commit core changes in the task worktree on `task/<id>` after the task's `design.md` carries a
complete receipt. Regenerate `memory/index.md` only after staging a new memory file, because the
reconciler reads the staged snapshot.
