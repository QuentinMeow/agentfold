# Handover — repair queue lifecycle round two

**Session:** 2026-07-23 07:30–08:48 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Added auditable unanswered-review retraction and separate republication.
- Split requested changes from terminal rejection/abandonment with legacy compatibility.
- Added explicit displaced-tip continuity for force pushes and provider adapter coverage.
- Made whole queue-service removal conditional on preserving every live action.
- Added regressions; the complete queue suite passes 159 tests.

## How it works now

An unanswered bound review can return to pending, but publication and response remain
separate edges and the first response freezes the binding. Force-ref adapters identify
the displaced old tip explicitly; divergent continuity preserves its live actions,
while ordinary PR divergence keeps normal range semantics. Queue removal is modular
only when its removal edge contains no live action.

## Decisions made for you

The refined lifecycle, outcome, continuity, and modular-removal semantics are recorded
in the [task design](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/design.md).

## Needs your attention

[Assurance-profile ceilings](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) asks whether four deployment profiles make claims no stronger than their enforcement boundaries. Guard-mode implementation stops at its start transition if this remains unanswered; unrelated work and the documentation proposal may continue.

[Detector failure state](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) asks whether scanner failure stays distinct from clean results and findings, with mode controlling only transition behavior. Guard-mode implementation stops at its start transition if unanswered; the current proposal remains documentation.

[First-class message queue](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) asks for judgment of queue-owned actions, filename timing, and enforcement after an exact artifact is published. Implementation and review may continue, but this task cannot merge while the review remains unresolved.

[Acknowledgement versus exception authority](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) asks whether agent-authored acknowledgement may record judgment but never authorize a confirmed critical finding. Guard-mode implementation stops at its start transition if unanswered; unrelated work may continue.

[Sensitive-data recovery](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) asks whether incident recovery is correctly separated from prevention and pre-authorized exceptions. Guard-mode implementation stops at its start transition if unanswered; the proposed recovery sequence remains documentation.

[Template-first explanation](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) asks whether the design clearly explains the already-decided opt-in template policy. It never blocks implementation; if unanswered, the existing ADR and current explanation remain in force.

## Dead ends

- Inferring force push from any divergent `--range` was rejected because ordinary PR
  base/head histories diverge too; providers now name the displaced tip explicitly.
- Treating old-tip continuity as an ordinary resolution edge was rejected because a
  history rewrite is not the required evidence-producing deletion commit.

## Next steps

None.

## Deep links

- Task folder: [first-class message queue](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md)
- Commits: none — changes remain uncommitted for the parent session
