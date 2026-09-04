# AgentFold

**Bring your agents into the fold.** Folders as services · files as messages · systems over
instructions.

AgentFold is a working example of an **agent-native repository** — a repo structured so
that a team of AI coding agents (Claude Code, Cursor, Codex, or anything that reads
[AGENTS.md](https://agents.md/)) can work in it like a team of engineers: independently,
in parallel, across sessions, with a human involved exactly as much as they want to be.

It is not a framework and has no runtime dependency. It is a folder structure, a set of
file schemas, and a small enforcement layer you can copy into any project.

## The idea

Ant colonies don't coordinate by talking to each other. Each ant leaves traces in the
environment, and other ants act on the traces they find. This is called **stigmergy**,
and it is exactly how AI agents with no shared memory and no live connection can still
work as a team: the repository *is* the shared environment, and every message, task,
decision, and lesson is a file another agent (or you) will find.

Four rules make that work:

1. **Folder as a service.** Every folder is independent, and its `AGENTS.md` is its API.
   Subfolders are endpoints. A folder that needs another service links to it — never
   reaches into it. Agents working in different folders don't collide.
2. **Files as messages.** Every pending human or cross-session agent action goes through
   `message-queue/` — one file per action, routed by who acts next and prefixed by when
   it blocks. Chat and PRs surface links; files survive.
3. **Systems over instructions.** Agents forget. Instructions are wishes; hooks, tests,
   and the reconciler are guarantees. Every invariant that matters is checked
   mechanically, and violations become repair tasks the next agent picks up —
   the repo converges to a consistent state even when any single agent is unreliable.
4. **A human dial, not a human bottleneck.** Three collaboration modes — `autonomous`,
   `async`, `pair` — define exactly when an agent decides alone, files a decision and
   proceeds on a default path, or stops and asks.

## The tour

Every name is chosen so you can guess the contents without opening the folder.

```
agentfold/
├── AGENTS.md            # root agent contract — the API of the whole repo
├── README.md            # you are here — the human doc; agent contract is AGENTS.md
├── handbook/            # why & how: principles, modes, git workflow, naming, adoption
├── docs/                # durable system designs and research-backed proposals
├── message-queue/       # canonical pending actions; filenames say when they block
│   ├── needs-human/     #   your move:
│   │   ├── decisions/   #     choices only you may make
│   │   ├── clarifications/ #  corrections or intent the agent needs
│   │   └── reviews/     #     judgment over a named diff, artifact, or claim
│   └── needs-agent/     #   an agent's move:
│       ├── requests/    #     durable work assigned to another session
│       └── retries/     #     repair work from a reconciler finding or a failed job
├── tasks/               # work items; the folder a task sits in IS its status
│   ├── 0_backlog/  1_in-progress/  2_blocked/  3_in-review/  4_done/
│   └── …/<task>/        # task.md, requirements.md, design.md, plan.md, worklog.md, verification.md
├── history/             # one folder per conversation, each with a short handover.md
├── memory/              # long-term memory: facts/, decisions/ (ADRs), lessons/, known-issues/
├── roadmap/             # desired-state.md vs current-state.md — the gap is the backlog
├── skills/              # portable skills (explain-to-human, session-handover, …)
├── automation/          # git hooks, the reconciler, the installer
├── templates/           # single source of truth for every file schema above
└── services/            # the example product code — one folder per service
```

## Quickstart

```bash
git clone <this-repo> && cd agentfold
python3 automation/install.py        # shared hooks + this worktree's adapters (idempotent)
python3 automation/reconcile/reconcile.py --check   # should pass on a fresh clone
```

Then open the repo in any coding agent and say hello — the agent boots from `AGENTS.md`.
Ask it anything about the design: the `skills/ask-me-anything/` skill routes questions
to the right document. To adopt AgentFold in your own project (new or existing), follow
`handbook/adoption-guide.md`.

## How much human do you want in the loop?

| Mode | Agent decides | Agent files & proceeds | Agent stops and asks |
|------|--------------|------------------------|----------------------|
| `autonomous` | everything permitted | `non-blocking-*` FYI items | only separately mandated trust gates |
| `async` (default) | everything reversible | `future-blocking-*` actions until their named boundary | `blocking-*`, or an unresolved future boundary |
| `pair` | nothing significant | — | asks before each meaningful step, through a queued item; you merge |

The active mode is one line in `AGENTS.md`. Details, and the exact list of what counts
as "expensive to reverse": `handbook/collaboration-modes.md`.

## What's enforced vs. what's suggested

| Guarantee | Enforced by |
|-----------|-------------|
| Queue names/timing, action links, and queue/task/memory schemas agree | `reconcile.py` (pre-commit hook + CI) |
| Every conversation *folder* contains a `handover.md` | reconciler finding (a session that leaves no folder is invisible to it) |
| Links in docs point to files that exist | reconciler link check — what it exempts, by source and by target, is listed in `handbook/naming-conventions.md` |
| Contracts stay short (line budgets on AGENTS.md, SKILL.md, this README) | reconciler budget check |
| Memory expires and gets re-verified or deleted | `Review-by` dates + reconciler + gardener skill |
| Example services stay green | `automation/run_tests.py` in the pre-commit hook + CI |
| Merges get adversarial review (in `autonomous` mode) | `skills/adversarial-review/` protocol — suggested, not machine-checked |
| Every pull request carries the reader's own to-do list, each item linking a live queue file | `check_action_projection.py` at the provider boundary |
| Anything a human reads is written to one standard | `skills/explain-to-human/` protocol — suggested, not machine-checked |

Everything an agent might forget is either checked mechanically or written down where
the next agent will trip over it. That's the whole trick.

## Design lineage

AgentFold stands on public prior art and records its own decisions as ADRs in
`memory/decisions/`. Notable influences: the [AGENTS.md standard](https://agents.md/),
[obra/superpowers](https://github.com/obra/superpowers) (enforced workflows),
[github/spec-kit](https://github.com/github/spec-kit) (constitution, spec→plan→tasks),
[OpenSpec](https://github.com/Fission-AI/OpenSpec) (desired vs. current state),
[Backlog.md](https://github.com/MrLesk/Backlog.md) (tasks as markdown files),
[Cline Memory Bank](https://docs.cline.bot/best-practices/memory-bank) (file memory),
[compound engineering](https://every.to/guides/compound-engineering) (lessons capture),
and [ACE-FCA](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents)
(review the plan, not the diff).

## License

MIT — see `LICENSE`.
