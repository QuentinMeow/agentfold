# Handover — development feedback review repair

**Session:** 2026-07-26 03:53–04:00 PDT, codex
**Task:** 2026-07-26-accelerate-development-feedback
**Mode:** async
**Queue projection:** v1

## What happened

- Repaired an omission where the narrow lane named one test file instead of selecting
  all discovered tests in an affected service.
- Added index fingerprinting around selector reads so concurrent index changes fall
  back to full coverage.
- Added focused regressions for a newly discovered failing service test and for an
  index mutation between Git reads.
- Re-ran the real narrow path with a temporary index; it selected the CLI scope and
  passed in 1.27 seconds.

## How it works now

The dependency map names service scopes. A CLI change selects all discovered CLI tests,
while an API change selects all discovered API and CLI tests. Narrow selection is
accepted only when the exact Git-selected index has the same fingerprint before and
after every selector read; otherwise the full suite runs.

## Decisions made for you

Both independent review findings were accepted and repaired in the task's
[`design.md`](../../../tasks/1_in-progress/2026-07-26-accelerate-development-feedback/design.md).

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

Keeping a fixed test filename per service was rejected because a newly added test file
would not be in the dependency closure. Trusting two separate Git reads without an
index stability check was rejected because they could describe different staged states.

## Next steps

None.

## Deep links

- Task folder: [`2026-07-26-accelerate-development-feedback`](../../../tasks/1_in-progress/2026-07-26-accelerate-development-feedback/) · Worklog: [`worklog.md`](../../../tasks/1_in-progress/2026-07-26-accelerate-development-feedback/worklog.md) · Verification: [`verification.md`](../../../tasks/1_in-progress/2026-07-26-accelerate-development-feedback/verification.md)
- Commits: `a46c9e8`, `3b6d425`, and the pending repair commit
