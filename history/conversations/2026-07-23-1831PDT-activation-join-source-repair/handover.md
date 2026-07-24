# Handover — activation-join and effective-source repair

**Session:** 2026-07-23 18:13–18:31 PDT, codex
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Closed a lifecycle gap for queue actions created and deleted on history parallel to
  queue-v1 activation.
- Unified structural triage for effective formal reviews returned through either
  GitHub review connection.
- Recognized bounded `kindly` action directives while preserving descriptive prose.

## How it works now

A candidate that joins queue-v1 activation with parallel history governs the newly
admitted history, so an unresolved action cannot disappear inside that join. Both
formal-review connections use one validated force policy. Polite action directives
using `kindly` enter the ordinary queue-projection check.

## Decisions made for you

None.

## Needs your attention

- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

Checking only commits descended from activation ignored newly admitted parallel
history. Applying the weaker opinion-connection force rule after source construction
allowed the same provider record to change meaning by connection.

## Next steps

None.

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: pending
- Commits: `3af20145c29cd89eb6500e249335813c8fbbc262` plus uncommitted repair
