# Git workflow

Git is the harness's database, archive, and undo button. These rules exist to make
parallel agents conflict-free, every change traceable to a task, and every mistake
cheap to roll back.

## Two kinds of writes

| | Coordination writes | Code writes |
|---|---|---|
| What | `message-queue/`, `tasks/`, `history/`, `memory/`, `roadmap/` | `services/`, `skills/`, `automation/`, `handbook/` |
| Where | directly on `main` | branch `task/<task-id>` |
| Commit size | tiny, single-purpose, immediate | logical milestones |
| Why | other agents must see queue/task state **now**, not after a merge | code needs review before it's truth |

Coordination commits use the prefix `harness:` (e.g. `harness: file decision on quote
storage`). This split is what keeps the message queue real-time while code stays gated.

## Conflict avoidance (by construction, not by care)

- **One item, one file** — concurrent agents create files, never edit shared ones.
- **One agent per task** — claim in one coordination commit: set `**Claimed-by:**`, move
  backlog to in-progress, and resolve its pickup request; if the push is rejected,
  another agent won, so pick another task.
- **One worktree per agent** — parallel agents use `git worktree add ../<task-id>
  task/<task-id>`, never share a checkout.
- **Service boundaries** — a task branch touches one service; cross-service work is
  split into linked tasks. Two branches editing the same file is a planning bug.

## Commits

- Imperative subject ≤ 72 chars saying *what*; body saying *why*; task id included on
  every commit belonging to a task (`task: 2026-07-22-add-quote-cache`).
- Commit at verifiable milestones: claim, plan written, each test-green step,
  verification recorded. Small commits are the rollback granularity — a giant commit
  is a giant revert.
- Never commit through a failing pre-commit hook. A `--no-verify` bypass must be
  reported in the handover with a reason.

## Merging and review

- `main` is always green: reconciler clean, tests passing.
- Merge task branches via PR/merge-commit (not squash — task commits are the audit
  trail; not rebase-onto-main of shared branches — pushed history is never rewritten).
- A PR description may summarize human actions only by linking their live canonical
  `message-queue/needs-human/` items; editing PR prose never creates or resolves an ask.
- Review gate by mode (`collaboration-modes.md`): `autonomous` → adversarial panel
  majority; `async` → tests + reconciler, panel for one-way doors; `pair` → the human.

## Rolling back

- A bad merge: `git revert -m 1 <merge-commit>` — never delete history.
- A bad coordination commit: `git revert <sha>`; if the file was deleted queue state,
  restore with `git checkout <sha>^ -- <path>`.
- A misfiled queue item is moved with every live link updated. A stale item is
  re-surfaced, reclassified, or explicitly resolved; delete it only after folding a
  response or recording why the action is duplicate or moot. Git history can recover
  an accidental deletion, but is not a substitute for live delivery state.
