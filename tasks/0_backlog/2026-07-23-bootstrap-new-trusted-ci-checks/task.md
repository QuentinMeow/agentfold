# Bootstrap new trusted CI checks without candidate-code execution

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-23, by codex, from failing checks on PR #7
**Parent:** 2026-07-23-first-class-message-queue
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-bootstrap-new-trusted-ci-checks.md`

## Goal

Define a safe first-activation path for trusted-base workflow checks whose checker does
not yet exist on the target branch. Do not solve bootstrap by executing unreviewed
candidate code in a trusted context.

> **Rescoped 2026-08-02 by a backlog disposition audit.** Three of the five original
> criteria are discharged and are kept below, ticked, with the evidence that discharged
> them; only the activation protocol survives as work. The original goal also asked for
> hermetic link validation, and that half shipped separately — it is struck from the goal
> above and recorded as criterion 3. Every claim in this note was re-verified from the
> repository rather than carried over; the commands are in the disposition entry of
> `worklog.md`.

## What still has to be built

Nothing in this repository yet answers the bootstrap question. `automation/` and
`.github/workflows/harness.yml` contain no first-activation protocol, and a grep for
`activation protocol` across `automation`, `docs`, `handbook`, `roadmap`, `memory` and
`tasks` matches only this file. So the problem is unsolved — but it is also not yet
concrete: it recurs the next time a *new* trusted-base check is introduced, and until
that second check exists, any protocol written here would be designed against an
imagined caller rather than a real one. Prefer to claim this task when a new trusted
check is actually being added, and design the protocol around that check.

## Acceptance criteria

- [ ] A regression reproduces a trusted-base workflow invoking a checker that exists
      only on the candidate branch.
- [ ] The activation protocol either supplies trusted checker code independently or
      stages enforcement without overstating first-PR assurance.
- [x] A regression proves that developer-local absolute paths produce the same
      link-check result locally and in CI.
      *Shipped by task `2026-07-30-flag-machine-specific-paths-in-link-check` (PR #27,
      merged 2026-07-30, now in `tasks/4_done/`). A backticked absolute path is reported
      as machine-specific instead of being probed against the host filesystem, and
      `test_backticked_absolute_path_is_machine_specific_not_a_link` in
      `automation/tests/test_reconcile_queue.py` asserts the verdict for two paths that
      exist on some machines and not others, so existence is never the question asked.*
- [x] PR #7's two recorded failing checks have an explicit disposition and rerun
      evidence.
      *Premise dead. PR #7 merged on 2026-07-24 as `2372e48`, an ancestor of `main`, and
      `roadmap/current-state.md` records it admitted. There is no candidate left for
      those two runs to gate, so no rerun can be taken and none is owed. What was
      genuinely skipped at that merge — no final independent adversarial panel verdict was
      ever taken on PR #7 — is already recorded in `roadmap/current-state.md` rather than
      implied here.*
- [x] Implementation begins only after the parent change's first human review.
      *Gate satisfied, not work. The parent's first human review is
      `message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md`,
      filed from task `2026-07-23-first-class-message-queue`; it carries a committed
      response, `**Review outcome:** approved`, and its disposition is
      `memory/decisions/2026-07-23-detector-failure-review-disposition.md`. Whoever claims
      this task may start.*

## Links

- Parent task: `2026-07-23-first-class-message-queue`
- The trusted-base workflow this concerns: `.github/workflows/harness.yml`
- The link-check half that shipped: task `2026-07-30-flag-machine-specific-paths-in-link-check`
- Failing workflow:
  https://github.com/QuentinMeow/agentfold/actions/runs/30070821441
- Failing publication run:
  https://github.com/QuentinMeow/agentfold/actions/runs/30070769357
