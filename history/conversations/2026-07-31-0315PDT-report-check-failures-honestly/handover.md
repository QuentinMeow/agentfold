# Handover — report-check-failures-honestly

**Session:** 2026-07-31 01:20–03:15 PDT, local time, claude (worktree agent-a08cc597c4b8c87c6)
**Task:** 2026-07-30-report-check-failures-honestly
**Mode:** async
**Queue projection:** v1

## What happened

- Fixed four reproduced defects in `automation/reconcile/reconcile.py`. Every one was
  reproduced on the unmodified tree first, and the real before-and-after output is in
  the task's `verification.md`.
- An unreadable file used to print a Python traceback and exit 1 — the same code the
  reconciler uses for "the repository has findings" — and, because the finding list was
  built in one eager pass, it threw away every finding already found. Findings now
  stream as they are produced, and any failure exits 2 with one line naming the file or
  the check that could not run.
- Freshness checking no longer crashes on a task id whose calendar date is impossible,
  and four checks that gated on the worktree while reading the Git index now gate on the
  commit candidate, so deleting a file no longer hides a staged violation.
- Findings now carry a severity. Age-driven findings report visibly but never fail the
  gate, so the repository no longer turns red on 2026-08-15, 2026-08-25 and 2027-01-23
  with no change to any file.
- Attempting to claim the existing severity-tiers backlog task is blocked by the harness
  itself; both halves of the conflict are reproduced, and the repair is queued.

## How it works now

`reconcile.py --check` prints each finding as it is found. A finding is blocking unless
its check id is in `ADVISORY_CHECKS` (`memory-expiry`, `roadmap-fresh`, `stale-queue`,
`stale-task`), in which case it prints with an `(advisory)` marker and is counted
separately; only blocking findings exit 1. `--fail-on-advisory` opts a maintenance run
into failing on them, and nothing on the commit or merge path passes it. Any exception
inside a check exits 2 with one clear line, so a crash can never be mistaken for a
finding — and never mistaken for success either.

## Decisions made for you

- Advisory findings do not fail CI either, not just local commits — reasoning in
  `tasks/1_in-progress/2026-07-30-report-check-failures-honestly/design.md`. Failing CI
  on them moves the calendar lockout to the place that blocks every agent at once.
- `stale-task` became its own registered check rather than being renamed, because retry
  garbage collection only clears findings whose check id is in the registry — so every
  `stale-task` repair item ever filed was previously immortal.

## Needs your attention

- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- Claiming task 2026-07-22-severity-tiers-for-reconciler-findings the way
  `tasks/AGENTS.md` requires does not work today, and retrying it will not help. The
  claim must delete the task's pickup request; a live queue item names that path in
  backticks, so the claim commit fails `link-check`; and repairing that reference fails
  `queue-resolution`, because a request's body outside its lifecycle fields is its
  action identity. Both findings are reproduced verbatim in the task's
  `verification.md`, and the repair is queued below.
- Tiering the retry-filing prefix was not attempted here. `retry_text` and
  `retry_destination` belong to task 2026-07-22-retry-filing-automation-and-waivers, so
  advisory findings still file blocking repair items; the retries README now says so.

## Next steps

- [Give the claim ritual a path that keeps both invariants — for example, teach the link check that a resolved pickup request is a lifecycle path like Resolution evidence, or forbid queue items from naming another item's pickup path — then claim task 2026-07-22-severity-tiers-for-reconciler-findings.](../../../message-queue/needs-agent/requests/non-blocking-unblock-claiming-a-linked-pickup-task.md)

## Deep links

- Task folder: `tasks/1_in-progress/2026-07-30-report-check-failures-honestly/` · Worklog: `tasks/1_in-progress/2026-07-30-report-check-failures-honestly/worklog.md` · Verification: `tasks/1_in-progress/2026-07-30-report-check-failures-honestly/verification.md`
- Commits: `56d4d49..HEAD` on branch task/2026-07-30-report-check-failures-honestly
