# Contributing

AgentFold dogfoods itself: contributions follow the same workflow the repo teaches.

## Ground rules

- **One focused change per PR.** Branch `task/<task-id>` for tracked work, or
  `<type>/<slug>` (`feature|fix|docs|chore`) for small untracked fixes.
- **Commit messages**: imperative subject ≤ 72 chars saying *what*; body saying *why*;
  include the task id when one exists. Full conventions: `handbook/git-workflow.md`.
- **Schemas live in `templates/`** — a PR that changes a file format changes the
  template, the reconciler check, and migrates every existing item, all in the same
  PR (other docs link to the template, never restate it).
- **Instruction-bearing files get human review.** PRs touching any `AGENTS.md`,
  `skills/`, `templates/`, `automation/`, or `message-queue/` are reviewed by a
  maintainer before any agent acts on them
  (`handbook/principles/provenance-over-position.md`).
- **Core changes prove they belong here.** Core diffs use a task that completes
  `templates/task/design.md`; hooks and CI enforce that receipt. Independent core-fit
  review is available through `automation/check_core_scope.py --require-review` and is
  manual by default until guard modes are configurable. The small untracked-fix branch
  convention applies outside core only; personal setup and single-agent/provider/product
  integrations stay external.
- **Keep contracts short.** The reconciler enforces line budgets on every `AGENTS.md`.
  Before adding a line ask: would removing this cause mistakes? If not, cut it.

## Before opening a PR

```bash
python3 automation/reconcile/reconcile.py --check   # must pass with zero findings
python3 automation/run_tests.py                     # repository test files stay green
```

Both also run in CI and as the pre-commit hook (`automation/install.py` installs it).

## Proposing design changes

File a decision in `message-queue/needs-human/decisions/` (copy
`templates/queue/decision.md`) or open a GitHub issue. Accepted decisions become ADRs
in `memory/decisions/` — never rewrite an existing ADR; supersede it with a new one.
