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

## 2026-08-04 — repair blocked path and receipt-region scope (codex sol-high implementer)

- The adversarial panel reviewed exact revision `85a044e67c725cf03d918432514c76ba1655c984`
  and returned 0 approve, 3 block. All three reviewers found the same admission gap:
  basename-only path matching and whole-file line normalization could hide approval-like
  prose in nested or case-variant files and outside the formal receipt region.
- Replaced the line-only sharing boundary with one formal parser for the real Review
  verdicts section, its one valid full-commit field, and only verdicts after that field.
  The detector separately requires the exact lowercase task-root verification path.
- Added regressions for nested and case-variant paths, lines outside or before the bound
  region, duplicate or missing sections and fields, malformed lines, and hostile findings.
- Re-ran the full repository suite to capture its terminal result honestly: all 15 test
  files passed in 68.19 seconds. The blocked panel is evidence about the prior revision,
  not an invocation of the repaired revision's independent core-fit review.

## 2026-08-04 — repair heading-aware receipt boundaries (codex sol-high implementer)

- The second adversarial panel reviewed exact revision
  `12a1f320a9916dd2223a6fe81fd5464ddc611aae` and returned 2 approve, 1 block. The
  blocker was valid: the H2 extractor crossed ATX H1 and CommonMark setext H1/H2
  boundaries, so a later approval-like line could inherit the receipt exception.
- Kept the exact Review verdicts H2 opening grammar and made the shared extractor end at
  the next real ATX H1/H2 or setext H1/H2. A setext heading's content line is excluded;
  H3 detail remains inside the review section.
- Added action-detector and core-scope regressions for ATX H1, ATX H2, both setext
  underline forms, a revision-like setext heading, and an H3 canary.
- Focused tests, all three owning modules, and the full repository suite passed; the full
  lane ended with all 15 test files passing in 68.07 seconds.
