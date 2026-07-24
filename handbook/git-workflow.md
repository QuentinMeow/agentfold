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
contract, while `tasks/1_in-progress/<id>/task.md` is live coordination. This split keeps
the action bus real-time while behavioral and descriptive changes stay reviewable.

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
- A PR description may summarize actions only by linking their live canonical queue
  items. Its declared “What to review” section is checked at the provider boundary:
  one top-level entry and one queue link per action, including every live human path
  in the task's `Queue actions`. A `task/<id>` branch declares its task and is checked
  against changed task records and `task:` commit tokens between the trusted base and
  immutable candidate; another branch is bound from that same evidence. Missing,
  conflicting, or ambiguous scope fails closed. External assignments retain direction:
  a human reviewer or assignee requires a distinct task-owned `needs-human/` link,
  while an assigned agent or bot requires a distinct task-owned `needs-agent/` link.
  Each linked item must copy the adapter's opaque provider/role/identity binding, so
  an unrelated task action cannot satisfy an assignment. Use the exact
  `No queued action requested.`
  acknowledgement only when neither task scope nor assignment exposes an action.
- A provider title is change-summary metadata, so a conventional title such as
  `Fix the login race` is not itself an ask. Questions, TODOs, explicit obligations,
  authority commands such as `Review this change`, and requests in a title or body
  still require queue projection. Editing provider prose never creates or resolves an
  ask.
- GitHub issue bodies accept either queue actor because the linked path says who acts
  next. Assignment adapters map GitHub `User` accounts and teams to `needs-human`, map
  `Bot` accounts to `needs-agent`, and fail closed on unknown account types or missing
  identities. Every non-empty issue or PR conversation comment is a structurally
  forced `needs-agent` triage source; author type does not change who triages next.
  Its body is never English-classified. An edit versions the identity, deletion removes
  it, and closing the issue/PR is its terminal provider boundary. Current open-PR
  comments replay on every candidate update; issue and closed-PR events capture the
  latest trusted default-branch commit so a new binding can satisfy a rerun without
  editing the author's words. These inbound sources are unscoped: they carry only
  their own triage and cannot stand in for a task's complete action set. Current formal
  reviews and unresolved diff threads also enforce `needs-agent/` actions.
  Every non-empty effective formal review creates an agent-triage source instead of
  asking a prose heuristic whether the human meant work; its queue item may be
  non-blocking. `CHANGES_REQUESTED` is forced even with an empty body, directly from
  either review connection, and unresolved threads remain forced action state.
  Provider-authored prose may carry canonical links directly; otherwise an agent
  transcribes it into one or more live items with the adapter's exact versioned
  `External source` binding. Editing the source creates a new identity. A bound item
  stays live until the effective review is superseded/dismissed or the thread resolves.
  `pull_request_target`, issue, and issue-comment checks run trusted default/base
  workflow code and replay current review and conversation state on every PR target
  update. The candidate-context job also replays both states on direct review events
  and every PR update, so pushing an unrelated commit cannot clear an unqueued request.
  It uses only the ephemeral workflow token, never a developer's local CLI login.
  Direct review events have no target-context variant, so a separately controlled
  provider gate is still required before claiming resistance to hostile workflow
  tampering between target updates.
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
  and dependent artifact-pending re-review; `rejected` and `abandoned` end the action.
  Verified pickup/retry exceptions stay atomic. Git history can recover accidents, not
  replace live delivery state.
