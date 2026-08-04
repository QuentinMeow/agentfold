# Worklog — stop completed review verdicts from looking like human asks

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-04 — reproduction and claim (codex planner)

- Reproduced the contradiction on `main`: the exact receipt line required by
  `check_core_scope.py --require-review` is returned as one actionable unit by
  `task_action_unit_counts()` and then refused by `task-action-origin`.
- Stopped the stale-base publication instead of weakening or bypassing either gate.
- Filed GitHub issue #80 as a projection, claimed this prerequisite as its own core task,
  and assigned implementation to a Sol high worker under the planner's review.
- Independent design and test-inventory agents agreed on the narrow boundary: neutralize
  only the exact structural verdict token and continue scanning reviewer and finding text.

## 2026-08-04 — implement receipt-aware classification (codex sol-high implementer)

- Moved the canonical core-fit verdict grammar into the shared Markdown semantics module;
  the core-scope validator and task human-action detector now consume the same named
  reviewer, verdict, and finding groups.
- Limited the classification exception to `verification.md` and to the matched structural
  `approve` or `block` token. Reviewer identities and finding tails still pass through the
  ordinary detector; malformed lines and identical prose in other task artifacts receive
  no special treatment.
- Added unit coverage for valid approve/block receipts, hostile reviewer/finding prose,
  questions, TODOs, and malformed near-misses, plus a staged task-admission regression.
- Focused and full repository suites passed. Independent revision-bound review,
  publication, issue closure, and resuming the parent stale-base repair remain for the
  coordinating session as requested.
