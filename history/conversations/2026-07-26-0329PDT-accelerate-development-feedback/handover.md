# Handover — development feedback speedup

**Session:** 2026-07-26 03:29–03:45 PDT, codex
**Task:** 2026-07-26-accelerate-development-feedback
**Mode:** async
**Queue projection:** v1

## What happened

- Added a conservative staged-path test lane for the two example quote services.
- Kept the complete isolated repository suite as the default and as the fallback for
  every uncertain or cross-cutting change.
- Updated pre-commit to request the fast lane and added deterministic selection and
  timing evidence.
- Added 14 focused cases covering service dependency selection and fail-closed paths;
  the complete 11-file suite passed during commit.

## How it works now

`python3 automation/run_tests.py` still runs every discovered test in the isolated
working-tree projection. Pre-commit invokes `--staged`; a quote CLI change selects the
CLI test, a quote API change selects API plus CLI, and every other case runs the full
suite.
Selection reads the index, but execution uses working-tree bytes rather than a staged
snapshot.

## Decisions made for you

The bounded dependency-map and fail-closed choice is recorded in the task's
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

Suite parallelism and reconciler redesign were intentionally excluded because the
safe staged selector delivered the useful service-edit speedup without changing either
boundary. The automation contract was already at its line budget, so its explanation
was compacted into the existing runner table row.

## Next steps

None.

## Deep links

- Task folder: [`2026-07-26-accelerate-development-feedback`](../../../tasks/1_in-progress/2026-07-26-accelerate-development-feedback/) · Worklog: [`worklog.md`](../../../tasks/1_in-progress/2026-07-26-accelerate-development-feedback/worklog.md) · Verification: [`verification.md`](../../../tasks/1_in-progress/2026-07-26-accelerate-development-feedback/verification.md)
- Commits: `a46c9e8`
