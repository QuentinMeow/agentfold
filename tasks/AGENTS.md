# tasks/ — work items

One folder per task; **the status folder it sits in is its status** — there is no
status field to drift (`handbook/principles/single-source-of-truth.md`).

## Lifecycle

```
0_backlog → 1_in-progress → 3_in-review → 4_done
                  ↕
              2_blocked (only while an unresolved blocking-* action stops it)
```

- Task id = folder name = `YYYY-MM-DD-<kebab-slug>` (date filed). The id never changes;
  status changes are `git mv` between status folders, committed with prefix `harness:`.
- `task.md` declares `**Repository scope:** core`, `service:<name>`, or `records-only`.
  Core changes also complete the receipt in `templates/task/design.md`; the Git boundary
  check enforces that receipt automatically. Independent core-fit review is manually
  invoked until guard modes are configurable; `--require-review` validates its
  revision-bound receipt but does not launch a reviewer. The small untracked-fix branch
  convention applies only outside core until its backlog task defines a safe path.
- Reference tasks by id, never by full path — paths change with status. Find one with
  `ls tasks/*/<task-id>`. The sole exception is a `task-pickup` request: it links the
  backlog path; its verified claim/move is the sole open-status queue deletion.
- `Queue actions` is exactly lowercase `none` or unique backticked canonical queue paths
  separated by `;` or `,`; no prose or duplicate field. Tasks do not originate asks:
  linked queue files own delivery/status and must link back when naming `task:<id>` or
  using the task as pickup context; the reconciler checks both directions.
- Every unclaimed backlog task links a non-blocking agent request with
  `Request kind: task-pickup`. Claiming resolves and deletes it in the claim commit.
- **Claim before working**: in one coordination commit, set `**Claimed-by:**`, move the
  task from backlog to in-progress, and resolve its pickup request; push, then start.
  One agent per task; a rejected push means someone beat you — pick another.
- One git branch per task: `task/<task-id>` (`handbook/git-workflow.md`).
- `2_blocked` requires a live `blocking-*` human or agent item in `Queue actions`, with
  that item reciprocally naming `task:<id>` in `Blocks now`. `1_in-progress` is valid
  only after a committed one-line `open` → `in-repair` agent claim, or an answered
  `waiting` → `folding` human-action claim. Waiting/open blockers require `2_blocked`.
- A task cannot cross `transition:start`, `transition:review`, or
  `transition:complete` while a linked `future-blocking-*` item remains; its boundary
  names `task:<id>`. Git/provider admission supplies external boundaries such as merge.
  A non-task branch uses changed task records and commit `task: <id>` tags to infer scope;
  without either it checks only global boundaries.
- `4_done` requires `verification.md` with real command output — the reconciler checks
  it exists; the adversarial-review gate (mode-dependent) checks it's honest.
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

A task too big to plan in ~10 steps gets split: child tasks link the parent in
`**Parent:**`; the parent tracks only coordination.
