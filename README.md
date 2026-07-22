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
2. **Files as messages.** All coordination goes through `message-queue/` — one file per
   message, named and routed by **who acts next**. Chat is ephemeral; files are the
   record.
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
├── README.md            # you are here (humans only; agents read AGENTS.md)
├── handbook/            # why & how: principles, modes, git workflow, naming, adoption
├── message-queue/       # all async communication, one file per message
│   ├── needs-human/     #   your move:
│   │   ├── decisions/   #     choices only you may make (each has a default path)
│   │   ├── clarifications/ #  questions that will matter soon; agents proceeding meanwhile
│   │   └── reviews/     #     optional human-eyes items; safe to ignore
│   └── needs-agent/     #   an agent's move:
│       ├── requests/    #     your free-form drop box ("hey, could you…")
│       └── retries/     #     repair work auto-filed by the reconciler / failed jobs
├── tasks/               # work items; the folder a task sits in IS its status
│   ├── 0_backlog/  1_in-progress/  2_blocked/  3_in-review/  4_done/
│   └── …/<task>/        # task.md, design.md, plan.md, worklog.md, verification.md
├── history/             # one folder per conversation, each with a short handover.md
├── memory/              # long-term memory: facts/, decisions/ (ADRs), lessons/, known-issues/
├── roadmap/             # desired-state.md vs current-state.md — the gap is the backlog
├── skills/              # portable skills (ask-me-anything, session-handover, …)
├── automation/          # git hooks, the reconciler, the installer
├── templates/           # single source of truth for every file schema above
└── services/            # the example product code — one folder per service
```

## Quickstart

```bash
git clone <this-repo> && cd agentfold
python3 automation/install.py        # git hooks + agent-adapter symlinks (idempotent)
python3 automation/reconcile/reconcile.py --check   # should pass on a fresh clone
```

Then open the repo in any coding agent and say hello — the agent boots from `AGENTS.md`.
Ask it anything about the design: the `skills/ask-me-anything/` skill routes questions
to the right document. To adopt AgentFold in your own project (new or existing), follow
`handbook/adoption-guide.md`.

## How much human do you want in the loop?

| Mode | Agent decides | Agent files & proceeds | Agent stops and asks |
|------|--------------|------------------------|----------------------|
| `autonomous` | everything | FYI reviews only | never — you review if you feel like it |
| `async` (default) | everything reversible | expensive-to-reverse decisions, on a stated default path | only when a decision file says `Blocking: yes` |
| `pair` | nothing significant | — | before every meaningful step |

The active mode is one line in `AGENTS.md`. Details, and the exact list of what counts
as "expensive to reverse": `handbook/collaboration-modes.md`.

## What's enforced vs. what's suggested

| Guarantee | Enforced by |
|-----------|-------------|
| Every queue item, task, memory entry matches its schema | `reconcile.py` (pre-commit hook + CI) |
| Every conversation leaves a `handover.md` | reconciler → auto-filed retry item |
| Links in docs point to files that exist | reconciler link check |
| Contracts stay short (line budgets on AGENTS.md, SKILL.md, this README) | reconciler budget check |
| Memory expires and gets re-verified or deleted | `Review-by` dates + reconciler + gardener skill |
| Example services stay green | `automation/run_tests.py` in the pre-commit hook + CI |
| Merges get adversarial review (in `autonomous` mode) | `skills/adversarial-review/` protocol, majority verdict |

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
