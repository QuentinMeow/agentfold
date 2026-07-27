# Handover — development-cycle acceleration and queue repair

**Session:** 2026-07-26 04:46–11:31 PDT, codex
**Task:** 2026-07-26-resolve-queue-items-whose-evidence-already-merged
**Mode:** async
**Queue projection:** v1

## What happened

- Published draft pull request 16 for a conservative staged service-test lane; known service
  edits now receive recorded feedback in about one to two seconds, while full coverage remains.
- Investigated the repository and chose the stale merged-evidence queue blocker before the
  pull-request event race. Built and repeatedly reviewed that repair, but did not publish it.
- Four review rounds were repaired. A fifth independent panel blocked the current revision on
  five correctness, compatibility, enforcement, and scaling issues now recorded in the task.
- Filed a continuation task that makes 60 seconds the small-change feedback budget and moves
  complete-suite correctness to deliberate local and required remote boundaries.

## How it works now

The test suite is green in its latest recorded final runs, but not fast enough for harness
iteration: the complete run is roughly three to four minutes and the queue file alone has ranged
from about 92 to 312 seconds. Draft pull request 16 fixes only known service scopes. The local
queue-repair branch is unpushed at `b4b75c3`, has handoff-only record edits, and its publication
boundary remains closed by five panel findings and the absence of fresh approval.

## Decisions made for you

The chosen policy gives small changes focused local checks under 60 seconds, retains the complete
suite as required pull-request CI, and pays for one deliberate local full run at the final
boundary. The queue correctness repair remains separate from the single development-speed pull
request.

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

Process-count tests did not prove bounded work: the current lineage walk uses few processes but
materializes the full reachable history. Weakening merge admission was rejected as a solution to
the fresh-pull-request race. Revision `b4b75c3` remains blocked by all three fifth-round reviewers.

## Next steps

- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-continue-development-cycle-acceleration.md)

## Deep links

- Task folder: [queue repair](../../../tasks/1_in-progress/2026-07-26-resolve-queue-items-whose-evidence-already-merged/) · Worklog: [progress and panel findings](../../../tasks/1_in-progress/2026-07-26-resolve-queue-items-whose-evidence-already-merged/worklog.md) · Verification: [real test output and five review rounds](../../../tasks/1_in-progress/2026-07-26-resolve-queue-items-whose-evidence-already-merged/verification.md)
- Commits: local branch `ab5a18e..b4b75c3`; draft development-speed pull request 16
