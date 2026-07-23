# Handover — repair history and lifecycle panel findings

**Session:** 2026-07-23 10:10 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Queue and handover schema activation now sees marker changes hidden on merged side branches.
- Independent branch activations form a frontier, so either branch governs only its descendants.
- First human responses remain immutable; counter-questions continue through durable evidence and a superseding item.
- Manual retries now require declared non-queue resolution evidence; generated retries retain finding clearance.
- The complete queue suite passed all 185 tests under Python 3.13.

## How it works now

Marker discovery uses full merge history, while handover incarnation discovery keeps
Git's selected-lineage simplification. A live mutation or handover creation is governed
when any reachable activation is its ancestor. Manual retry deletion still requires a
status-only claim plus a changed file named before repair began.

## Decisions made for you

- Preserved immutable human response evidence and used the clarified-successor protocol for counter-questions; see the task design.
- Preserved merge simplification for handover creation provenance because full history can select an unmerged competing add.

## Needs your attention

- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- Allowing a waiting answer to be rewritten was rejected because Git cannot prove the rewriter was the human.
- Adding full-history to handover creation queries was rejected because a competing branch add can be newer but absent from the selected merge tree.

## Next steps

None.

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/task.md) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: not created while the task remains in progress
- Commits: uncommitted working tree; root agent will integrate this subagent slice
