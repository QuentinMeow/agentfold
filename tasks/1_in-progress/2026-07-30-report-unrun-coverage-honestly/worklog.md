# Worklog — parseable reporting for an empty selection

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — fast-local-test-feedback continuation (claude)

- Filed from the salvage review of exp/c-tiered, whose `routine_selection` rule was
  rejected in `memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`.
- The review found that the branch's reporting work was already delivered by the
  input-ownership selector: the runner prints `skipped test files:` with the full list,
  and it is tested. Only the destination of that coverage was missing.
- The review also found a defect on main rather than on the branch: the inert-probe test
  still calls the pre-rename wrapper installer, so `AGENTFOLD_INERT_PROBE=1` raises
  `AttributeError`. It is gated behind an environment variable, which is why the suite
  stayed green and the breakage went unnoticed.
