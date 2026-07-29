# Handover — configurable test-gates deadline repair

**Session:** 2026-07-28, continuation ending 23:15 PDT, codex
**Task:** 2026-07-27-configure-test-gates-and-time-budgets
**Mode:** async
**Queue projection:** v1

## What happened

- Kept the approved final mode manual-only and rewrote the task and testing guide in plain English.
- Integrated the absolute-deadline worker design and generation bridge. Historical staged candidate `44963ec4…` passed the full final gate in 552.679782 seconds, but the following routine hook ignored its valid full receipt and failed at 60.26752 seconds.
- Repaired both root causes: exact complete evidence is checked before narrower routine work, and execution, cleanup, validation, and terminal delivery now have separate deadlines. The immutable claim is sent before bounded timing-task filing and evidence projection.
- Independent focused verification passed 34 deadline-protocol tests, 103 gate tests with one existing skip, 28 configuration tests, 6 generation tests, compilation, both diff checks, and reconciliation with zero findings. A focused adversarial rereview approved the repair.
- Stopped before the expensive final step. `HEAD` remains `a89eccc`; the repair, records, this handover, and two automation lessons are uncommitted. The staged candidate excludes the two still-unstaged timing journals.

## How it works now

For an unchanged candidate, complete final evidence is reusable in the routine lane after exact validation of the receipt, report, marker, policy, environment, manifest, and plan. When that evidence is absent, reversible work ends early enough for cleanup, identity validation, and a truthful deferred claim before the supervisor deadline; critical or uncertain work still blocks. This remains cooperative manual evidence, not authorization to publish or deploy.

## Decisions made for you

Final verification remains manual-only; the controlling rationale is in [design.md](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/design.md).

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

- The earlier critical-path prewarm regression did not cover reversible selected work; it hid the cache-lookup bug.
- A half-second shared reserve, and then advisory cutoffs without bounded validation or socket delivery, still allowed the supervisor to miss the claim.
- A five-second wall-clock fixture was too small and flaky; deterministic boundary tests plus a ten-second integration proved the intended path.
- One test run appeared to stop without a summary because the command transport ended near 30 seconds; a persistent session proved all 103 tests passed.
- The historical `44963ec4…` receipt covers older bytes and is ineligible for this staged candidate; no hook bypass was used.

## Next steps

- [Repair all six unanimous-panel findings and rerun the revision-bound merge review.](../../../message-queue/needs-agent/retries/blocking-repair-unanimous-test-gate-merge-review.md)

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/worklog.md) · Verification: [verification](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/verification.md)
- Commits: `fcc8d8d`, `8e4afdd`, `3a342013`, `19ca430`, `a89eccc`; deadline repair and handover remain uncommitted
