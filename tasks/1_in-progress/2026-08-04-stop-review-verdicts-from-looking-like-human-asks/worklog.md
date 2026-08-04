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

## 2026-08-04 — authorization boundary (codex planner)

- Three candidate implementations stayed unpublished after adversarial review found
  basename, section-boundary, and CommonMark-container gaps. Exact evidence remains on the
  task branch through commit `3de329d8b34bb9bb8afcd325b75b1c47612e7997`.
- Replanned to a closed contiguous receipt grammar that needs no general Markdown outline
  parser. The workspace safety reviewer requires fresh owner authorization before that
  security-sensitive parser and template change.
- Filed the authorization question in
  `message-queue/needs-human/decisions/non-blocking-authorize-the-closed-review-receipt-parser.md`
  and paused without bypassing the review or task-action gates.

## 2026-08-04 — owner authorization folded (codex planner)

- The owner selected Option A and authorized the closed contiguous review-receipt parser
  and template design. The answer was transcribed while the canonical item was waiting,
  then claimed in a separate folding commit.
- Recorded the durable decision in
  `memory/decisions/2026-08-04-review-receipt-parser-authorization.md` and released the
  completed human action from this task.
- The authorization does not approve a pull request or replace independent review; the
  implementation still owes focused and full verification plus a fresh adversarial panel.
