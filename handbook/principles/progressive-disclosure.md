# Progressive disclosure

Nobody — human or agent — reads long documents. Every contract has a short core that is
always loaded and deep references that are opened only when a task points there. Assume
the human reads one screen and the agent's context window is rented by the token.

## Rules

- **Short core, linked depth.** The root `AGENTS.md` fits in ~130 lines; each section
  links to the full document it summarizes. Leaf `AGENTS.md` files are pointers plus
  local rules only. Line budgets are enforced by the reconciler.
- **Task-conditioned pointers.** Deep references are reached via "before doing X, read
  Y" lines — never "read everything in docs/ first".
- **Always link the source.** Any summary, handover, or decision file links to the
  original it summarizes. The reader who wants depth clicks; the reader who doesn't,
  doesn't pay for it.
- **Write for the non-expert.** A decision file explains its own context from scratch —
  what the choice is, what each option means, a concrete example consequence of picking
  each (format: `../decision-guide.md`). Never assume the human remembers last week or
  knows the domain.
- **Repeat the ask.** Humans skim. An unanswered decision is re-surfaced at the end of
  every session's reply — one line each, with links — until answered. Polite repetition
  beats silent staleness.

## Why

The failure mode of documentation is not absence but unread abundance. Short cores get
read; linked depth gets read exactly when needed; everything else is context-window
rent and human fatigue. Curation is a feature the budget check enforces.
