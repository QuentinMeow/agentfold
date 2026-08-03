# Git workflow

Git is the harness's database, archive, and undo button. These rules exist to make
parallel agents conflict-free, every change traceable to a task, and every mistake
cheap to roll back.

## Two kinds of writes

| | Live coordination writes | Reviewed system writes |
|---|---|---|
| What | queue-item state; concrete task claims/status; new handovers; owner answers/decisions | contracts, templates, automation, skills, lessons, and state/docs tied to implementation |
| Where | directly on `main` | branch `task/<task-id>` |
| Commit size | tiny, single-purpose, immediate | logical milestones |
| Why | other agents must see queue/task state **now**, not after a merge | code needs review before it's truth |

Coordination commits use the prefix `harness:` (e.g. `harness: file decision on quote
storage`). A directory does not choose the lane: `tasks/AGENTS.md` is a reviewed system
contract, while `tasks/1_in-progress/<id>/task.md` is live coordination. One task folder
splits the same way. `task.md`'s claim and status, and the `plan.md` and `worklog.md` its
claim commit has to create because the reconciler requires both from `1_in-progress`, are
coordination and go straight to `main`. The rest of the folder — `design.md`,
`verification.md`, later `plan.md` and `worklog.md` edits, and any rewrite of the task's
own goal or criteria — are reviewed writes on the task branch. This split keeps
the action bus real-time while behavioral and descriptive changes stay reviewable.

## Conflict avoidance (by construction, not by care)

- **One item, one file** — concurrent agents create files, never edit shared ones.
- **One agent per task** — claim in one coordination commit: set `**Claimed-by:**`, move
  backlog to in-progress, add `plan.md` and `worklog.md`, and resolve its pickup request;
  if the push is rejected, another agent won, so pick another task.
- **One worktree per agent** — parallel agents use `git worktree add ../<task-id>
  task/<task-id>`, never share a checkout.
- **Service boundaries** — a task branch touches one service; cross-service work is
  split into linked tasks. When two branches need the same file, stack them rather than
  running them independently (see "Publishing" below). Screen a landing set for cross-leg
  collisions before merging any of it: `automation/integrate.py` pins the set, reports the
  colliding pairs, and replays the merges through the reconciler and the tests, so a
  failure belonging to no single branch is found before it lands rather than after.

## Commits

- Imperative subject ≤ 72 chars saying *what*; body saying *why*; task id included on
  every commit belonging to a task (`task: 2026-07-22-add-quote-cache`).
- Commit at verifiable milestones: the claim (which already carries the first `plan.md`
  and `worklog.md`), each test-green step, verification recorded. Small commits are the
  rollback granularity — a giant commit is a giant revert.
- Never commit through a failing pre-commit hook. A `--no-verify` bypass must be
  reported in the handover with a reason.

## Publishing: one pull request per task, and when it stacks

Finishing a task means publishing it. The end-of-session ritual in the root `AGENTS.md`
pushes the task branch and opens its pull request; a finished branch that was never pushed
is work nobody can see.

Where the branch starts is decided by dependency, never by the order you happened to work in:

| Situation | Branch from | Pull request base |
|---|---|---|
| the task needs nothing that is not already on `main` | `main` | `main` |
| the task needs a file or behaviour that exists only on another unmerged branch | that branch | that branch's pull request |

Two independent branches editing the same file is a planning bug. A *stack*, where each
layer contains the one below, is the normal way to sequence dependent work on one file —
but only when the dependency is real. Doing B after A is not a dependency.

A stacked pull request says so in the first thing in its body: which layer it is, what its
base branch is, and that the stack lands bottom-up (`templates/pull-request.md`). Without
that note a reviewer reads the wrong diff and reviews work that is already approved below.

Prefer shallow stacks. Every extra layer is another base ref that must not be deleted while
a child is open, and the rule below explains what that costs when it goes wrong.

## Merging and review

- `main` is always green: reconciler clean, tests passing.
- Merge task branches via PR/merge-commit (not squash — task commits are the audit
  trail; not rebase-onto-main of shared branches — pushed history is never rewritten).
  Restacking your own unmerged layer onto a newly merged parent with `--force-with-lease`
  is expected, and the adapter passes `--displaced-tip` for it.
- **Never delete a branch that is another open PR's base.** Before merging any PR whose
  head branch is a base elsewhere, run
  `gh pr list --state open --json number,baseRefName,headRefName` and retarget every child
  (`gh pr edit <child> --base main`), then re-query and assert `baseRefName == "main"` —
  the exit code is not the assertion. Merge the parent only then, delete no branch during
  a landing window, and re-run the query immediately before each deletion afterwards.
  Deleting a base ref closes the child PR in the same second, and a closed PR whose base
  was deleted cannot be reopened; this cost 41 minutes and two rebuilt PRs on 2026-08-01.
  Prefer shallow stacks whose members all target `main`: there is then no base ref to destroy.
- Filing an action is not crossing its boundary. A merge boundary skips an unanswered
  action the range itself filed — otherwise the reciprocal task link the reconciler
  requires would strand every `transition:*` action the moment it was written — and it
  is reported at every later boundary it reaches. An answered one is never skipped.
- A human answer never gates a merge. A `needs-human/` review is `non-blocking-*` unless it
  gates the start of a task still in `0_backlog` or one act with no undo
  (`message-queue/AGENTS.md`); it is filed, merged, and answered later, and its PR body
  lists it without waiting for it. A `transition:start` review binds a stable local
  artifact, and its fresh approval is the transition receipt in the crossing commit.
  Merging a change whose review has not come back is the accepted price of an `async`
  repository: the undo is `git revert -m 1`, and the start gate is what stops any *task*
  that depends on the unanswered judgment from beginning on top of it.
- A PR body's shape is a schema like any other: copy `templates/pull-request.md`, and write
  the prose in each slot as `skills/explain-to-human/scenarios/pull-request.md` describes.
  Neither is restated here; this section owns only what the boundary check requires.
- A PR description may summarize actions only by linking their live canonical queue
  items. Its declared “What to review” section is checked at the provider boundary:
  one top-level entry and one queue link per action, including every live human path in
  the `Queue actions` of every task in scope. Scope is the set of tasks the candidate
  carries, read from changed task records and `task:` commit tokens between the trusted
  base and immutable candidate; several is ordinary, because a reciprocal queue link, a
  filed follow-up, and a claimed child each edit a second task record. A `task/<id>`
  branch declares one member of that set and fails closed when the candidate carries no
  evidence of it. Missing scope fails closed. External assignments retain direction:
  a human reviewer or assignee requires a distinct task-owned `needs-human/` link,
  while an assigned agent or bot requires a distinct task-owned `needs-agent/` link.
  Each linked item must copy the adapter's opaque provider/stable-artifact/role/
  actor-kind/principal binding, so another artifact cannot reuse it. Use the exact
  `No queued action requested.`
  acknowledgement only when neither task scope nor assignment exposes an action.
- A pull-request title is change-summary metadata, so a conventional title such as
  `Fix the login race` is not itself an ask. Questions, TODOs, explicit obligations,
  authority commands such as `Review this change`, and requests in its title or body
  still require queue projection.
- What a GitHub adapter forces into the queue from issues, comments, formal reviews, and
  diff threads, and the limits of that assurance, is `handbook/github-projection.md`.
- Review gate by mode (`collaboration-modes.md`): `autonomous` → adversarial panel
  majority; `async` → tests + reconciler, panel for one-way doors; `pair` → the human.

## Rolling back

- A bad merge: `git revert -m 1 <merge-commit>` — never delete history.
- A bad coordination commit: `git revert <sha>`; if the file was deleted queue state,
  restore with `git checkout <sha>^ -- <path>`.
- A misfiled queue item is moved with every live link updated. A stale item is
  re-surfaced, reclassified, or explicitly resolved. Delete only after a one-line claim
  and changed durable evidence. Approved reviews revalidate their target;
  `changes-requested` (and legacy `not-approved`) leaves a same-boundary agent repair
  and dependent artifact-pending re-review. `rejected`/`abandoned` cleanup also proves
  the task, local target, or reviewed Git candidate was withdrawn.
  Verified pickup/retry exceptions stay atomic. Git history can recover accidents, not
  replace live delivery state.
