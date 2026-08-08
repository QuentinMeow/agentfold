# Stop completed review verdicts from looking like human asks

**Claimed-by:** claude
**Filed:** 2026-08-04, by codex, from task `2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check`
**Parent:** 2026-08-03-plan-multi-worktree-safety-remediation
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-track-github-review-verdict-action-classification.md`; `message-queue/needs-agent/requests/non-blocking-triage-github-issue-80-review-verdict-action-classification.md`

## Goal

Make the canonical revision-bound core-review receipt usable without weakening human-action
projection. Today `automation/check_core_scope.py` requires a line shaped like
`core-fit / reviewer: approve — finding`, while `task-action-origin` classifies that same
completed verdict as a new human approval request. The repair must neutralize only the
structured verdict token and continue scanning the reviewer identity and finding text for
real human asks.

## Acceptance criteria

- [x] A newly introduced canonical `approve` or `block` review receipt is not reported as
      an unqueued human action. One shape is still reported, named in `design.md` under
      Known residue: a receipt whose *reviewer identity* carries raw HTML, which the
      rendered view strips, so the gate cannot place the token and blanks nothing. It
      fails closed — the commit is refused, nothing hidden — and markup in a finding, the
      case that actually came up, is now neutralized correctly.
- [x] A real human request embedded in the review finding is still reported.
- [x] Malformed near-misses receive no exemption from ordinary human-action detection.
- [x] The existing core-review parser continues accepting valid revision-bound receipts.
- [x] Focused tests, the full repository suite, core scope, and the reconciler pass with
      real output recorded in `verification.md`.

## Links

- Parent remediation plan: task `2026-08-03-plan-multi-worktree-safety-remediation`
- Reproduction: task `2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check`
