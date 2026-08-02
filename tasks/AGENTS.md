# tasks/ — work items

**Task admission schema:** v1
One folder per task; **the status folder it sits in is its status** — there is no
status field to drift (`handbook/principles/single-source-of-truth.md`).

## Lifecycle

```
0_backlog ↔ 1_in-progress ↔ 3_in-review → 4_done
                  ↕
              2_blocked (only while an unresolved blocking-* agent action stops it)
```

- Task id = folder name = `YYYY-MM-DD-<kebab-slug>` (date filed). The id never changes;
  status changes are `git mv` between status folders, committed with prefix `harness:`.
- `task.md` declares `**Repository scope:** core`, `service:<name>`, or `records-only`.
  Core changes also complete the receipt in `templates/task/design.md`; the Git boundary
  check enforces that receipt automatically. Independent core-fit review is invoked by
  hand: `automation/check_core_scope.py --require-review` validates its revision-bound
  receipt but launches no reviewer. The small untracked-fix branch
  convention applies only outside core until its backlog task defines a safe path.
- Reference tasks by id, never by full path — paths change with status. Find one with
  `ls tasks/*/<task-id>`. The sole exception is a `task-pickup` request: it links the
  backlog path; its verified claim/move is the sole open-status queue deletion.
- `Queue actions` is exactly lowercase `none` or unique backticked canonical queue paths
  separated by `;` or `,`; no prose or duplicate field. Tasks never originate pending
  human or durable cross-session agent asks: task-local assignments use exact task-owned
  action links. Queue files own delivery/status and reciprocal task context.
- Every unclaimed backlog task links a non-blocking `Request kind: task-pickup`;
  claiming resolves and deletes it in the claim commit.
- **Claim before working**: in one coordination commit, set `**Claimed-by:**`, move the task
  from backlog to in-progress, add the `plan.md` and `worklog.md` that status folder requires,
  and resolve its pickup request; push, then start. One agent per task, one branch per task
  (`task/<task-id>`, `handbook/git-workflow.md`); a rejected push means someone beat you.
- `2_blocked` requires a live `blocking-*` **agent** item in `Queue actions` naming
  `task:<id>` in `Blocks now`; no human action justifies it. Only a task such an item names
  owes a claim: it may sit in `1_in-progress` only while that item carries a committed
  one-line `open` → `in-repair` claim, and an open blocker otherwise requires `2_blocked`.
- Every post-adoption Git edge rechecks task structure. `transition:start` from `0_backlog`
  is the only human boundary a task can cross: its review binds a stable local artifact and
  stays live in the crossing commit, cleanup needs the task past that receipt, and returning
  to `0_backlog` unstarts it. Non-task branches infer scope from changed task records or `task: <id>` commit tags.
- `4_done` requires real `verification.md` output and no live `blocking-*`/`future-blocking-*`
  **agent** action; a live human question stays listed and outlives the task, because done
  means the agent owes nothing — never that the human is satisfied.
- Done tasks are pruned by the memory gardener after ~90 days: durable learnings are
  promoted into `memory/`, then the folder is deleted (git history archives it).

## Files inside a task (schemas in `templates/task/`)

| File | Required | Purpose |
|------|----------|---------|
| `task.md` | always | what & why, acceptance criteria, mode override, claim |
| `plan.md` | from `1_in-progress` | small verifiable steps, checked off as done |
| `design.md` | when choices were made | options considered, chosen approach, one-way doors filed |
| `worklog.md` | always by first session | append-only; each session adds what happened |
| `verification.md` | for `3_in-review`/`4_done` | commands actually run + real output |

A task too big for ~10 steps is split; children link `**Parent:**`, which tracks coordination.
