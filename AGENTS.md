# Agent Contract — AgentFold

This repo is a working example of an **agent-native repository**: every folder is an
independent service whose `AGENTS.md` is its API, coordination happens through files
instead of live conversation, and quality is enforced by systems (hooks, tests, the
reconciler) rather than by hoping agents follow instructions. This file is the root
contract every agent reads before acting, and it is self-contained — acting correctly
never requires the README. `README.md` is the human landing page: agents write it and
may skim it for the big picture, but it never carries agent instructions (and no human
usage guides live here). The README stays a short pitch + map: technical depth lives
in `handbook/` and is linked, never restated (the reconciler budgets the README's
lines like any contract).

**Collaboration mode:** `async` — see `handbook/collaboration-modes.md` for what each
mode permits. A task file may override the mode for that task only.

## Boot sequence

1. Read this file.
2. Run the **message-queue ritual** (below). Top-level sessions only — subagents skip it.
3. Read the `AGENTS.md` of every folder you are about to work in. The closest
   `AGENTS.md` up the tree from a file wins; leaf files add to this contract and never
   contradict it — a conflict is a bug in the leaf.
4. Skim `memory/index.md`; open only entries relevant to your task. If
   `memory/lessons/<area>/` exists for the area you are working in, read it first.
5. If your work changes overall architecture, read `roadmap/current-state.md` and
   `roadmap/desired-state.md`.

## Repo map

| Path | What it is |
|------|------------|
| `handbook/` | Design principles, collaboration modes, git workflow, naming rules, adoption guide |
| `message-queue/` | All async human↔agent and agent↔agent messages; split by **who acts next** (`needs-human/`, `needs-agent/`) |
| `tasks/` | Work items; a task's status **is** the folder it sits in (`0_backlog` … `4_done`) |
| `history/` | One folder per conversation/session; each must contain a `handover.md` |
| `memory/` | Long-term project memory: `facts/`, `decisions/` (ADRs), `lessons/`, `known-issues/`; `index.md` is generated |
| `roadmap/` | `desired-state.md` vs `current-state.md` — the gap between them is the backlog's source |
| `skills/` | Canonical portable skills (`SKILL.md` each); agent-specific dirs are symlinks made by the installer |
| `automation/` | Things that run: git hooks, the reconciler, the installer |
| `templates/` | **Single source of truth for every file schema** — copy one to create any item |
| `services/` | The example product code: one folder per service, each with its own `AGENTS.md` |

## Message-queue ritual (start of every top-level session)

Filenames first — open only what is relevant. Full lifecycle: `message-queue/AGENTS.md`.

1. `ls message-queue/needs-agent/requests/` — act on each, or convert it to a task, then
   delete the file in the same commit.
2. `ls message-queue/needs-agent/retries/` — repair work filed by the reconciler or a
   failed job. Handle items touching your session's area; never delete one without
   fixing or explicitly rejecting it in the file.
3. Scan `message-queue/needs-human/decisions/` for filled `**Your answer:**` lines.
   Claim first (commit a one-line `**Status:** folding` edit), fold the answer into the
   affected docs, record an ADR in `memory/decisions/`, delete the queue file.
   An answer heard in chat is written into the queue file in the same turn — chat is
   the only channel with no file trace.
4. End every reply to the human with one entry per open `needs-human/` item you filed
   or noticed — a clickable link to the item plus enough context to act from the reply
   alone, never a bare name (format: the "Needs your attention" section of
   `templates/handover.md`). Chat is the human's only push channel.

## Task lifecycle

Create tasks from `templates/task/`; the folder name is `YYYY-MM-DD-<kebab-slug>` and its
status is the status folder it sits in. Claim a task by setting `**Claimed-by:**` in
`task.md` and committing before you start. One agent per task; one task branch per task
(`task/<task-id>` — see `handbook/git-workflow.md`). Full rules: `tasks/AGENTS.md`.

## End-of-session ritual

Before ending any session that did work: write `history/conversations/<timestamp>-<slug>/handover.md`
from `templates/handover.md`, update the task's `worklog.md`, file any pending questions
into `message-queue/`, and update `roadmap/current-state.md` if reality changed.
The `skills/session-handover/` skill walks through this.

## Guardrails (hard invariants)

- **Single source of truth**: every fact lives in exactly one file; other places link to
  it. Never restate a schema — link to its template.
- **Nothing blocks silently**: hitting a human-owned decision in `async` mode means
  filing it in `message-queue/needs-human/decisions/` with options, consequences, and a
  default path — then continuing on the default path unless the file says `**Blocking:** yes`.
- **Never fabricate** test results, benchmark numbers, or completion claims.
  `verification.md` contains only commands actually run and their real output.
- **Append, don't clobber**: re-read any two-way file (queue items, worklogs, decision
  blocks) immediately before writing; merge, never overwrite another writer's text.
  Never edit or delete text the human wrote.
- **Records are immutable**: a decided ADR is never rewritten — a reversal is a new file
  linking the old one.
- **Scratch discipline**: throwaway files go under git-ignored `tmp/`, never the repo root.
- **The reconciler is the referee**: `automation/reconcile/reconcile.py --check` must
  pass before any commit (the pre-commit hook runs it). Don't bypass with `--no-verify`;
  fix the finding or file it.

## Router

- Working under `message-queue/`? Read `message-queue/AGENTS.md` first.
- Working under `tasks/`? Read `tasks/AGENTS.md` first.
- Working under `memory/`? Read `memory/AGENTS.md` first.
- Working under `history/`? Read `history/AGENTS.md` first.
- Working under `skills/`? Read `skills/AGENTS.md` first.
- Working under `automation/`? Read `automation/AGENTS.md` first.
- Working under `services/<name>/`? Read `services/AGENTS.md`, then the service's own `AGENTS.md`.
- Writing any new file? Check `templates/` for its schema and `handbook/naming-conventions.md` for its name.
