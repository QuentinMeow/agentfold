# Worklog — Codify queue-message disposability and README depth rules

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-22 — doc-depth-invariants (claude, chat session)

- Filed and claimed from a chat request; audited the existing design first: the
  self-contained/disposable properties were already stated, the regenerable-projection
  framing and the README depth rule were not written anywhere, and the reconciler
  budgeted `AGENTS.md`/`SKILL.md` but not the README.
- Decided against a new `references/` folder — `handbook/` already plays that role and
  `handbook/naming-conventions.md` bans generic buckets (see `design.md`).
- Landed on the task branch (task/2026-07-22-doc-depth-invariants), merged to main after
  reconciler + tests passed; budget check demonstrated live in `verification.md`.
- ADRs recorded at claim time (same commit as the task filing); roadmap enforcement
  line updated to mention the README budget.
