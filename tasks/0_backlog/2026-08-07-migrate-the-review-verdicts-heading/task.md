# Migrate every verification record to the exact Review verdicts heading

**Claimed-by:** unclaimed
**Filed:** 2026-08-07, by claude, from task `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`
**Parent:** none
**Repository scope:** records-only
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-migrate-the-review-verdicts-heading.md`

## Goal

The review-receipt parser now requires the heading to be exactly `## Review verdicts`,
which `memory/decisions/2026-08-04-review-receipt-parser-authorization.md` authorized and
`automation/review_receipt.py` enforces. Nineteen tracked verification records still carry
the older `## Review verdicts (when a review was explicitly run)` spelling. In eighteen of
them that is the only such heading, so those records can host no receipt at all; the
nineteenth also carries an exact heading, which is the one that counts there. Four of the
nineteen are live tasks with `**Repository scope:** core`, the first records
`--require-review` will be run against, so they hit this first.

Nothing is broken today: every one of those sections says no review was run, and
`--require-review` is invoked by hand. This is a migration, not a repair.

## Acceptance criteria

- [ ] Every tracked verification record uses the exact `## Review verdicts` heading, or
      has the section deleted where no review was run.
- [ ] No record ends up with two exact `## Review verdicts` headings. A repo-wide rename
      would do exactly that to the verification record of task
      `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`, which already carries
      both spellings; its exact one is the sixteenth panel's receipt and would stop being
      readable as one.
- [ ] `python3 automation/check_core_scope.py --require-review` reports no heading problem
      for each of the four live core tasks.
- [ ] The full suite and `python3 automation/reconcile/reconcile.py --check` pass.

## Links

- Parser and grammar: `memory/decisions/2026-08-04-review-receipt-parser-authorization.md`
- Enforced by: `automation/review_receipt.py`, `templates/task/verification.md`
