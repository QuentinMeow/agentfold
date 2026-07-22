# Contributing

AgentFold dogfoods itself: contributions follow the same workflow the repo teaches.

## Ground rules

- **One focused change per PR.** Branch `task/<task-id>` for tracked work, or
  `<type>/<slug>` (`feature|fix|docs|chore`) for small untracked fixes.
- **Commit messages**: imperative subject ≤ 72 chars saying *what*; body saying *why*;
  include the task id when one exists. Full conventions: `handbook/git-workflow.md`.
- **Schemas live in `templates/`** — a PR that changes a file format must change the
  template, the reconciler check, and nothing else (other docs link, never restate).
- **Keep contracts short.** The reconciler enforces line budgets on every `AGENTS.md`.
  Before adding a line ask: would removing this cause mistakes? If not, cut it.

## Before opening a PR

```bash
python3 automation/reconcile/reconcile.py --check   # must pass with zero findings
python3 automation/run_tests.py                     # example services stay green
```

Both also run in CI and as the pre-commit hook (`automation/install.py` installs it).

## Proposing design changes

File a decision in `message-queue/needs-human/decisions/` (copy
`templates/queue/decision.md`) or open a GitHub issue. Accepted decisions become ADRs
in `memory/decisions/` — never rewrite an existing ADR; supersede it with a new one.
