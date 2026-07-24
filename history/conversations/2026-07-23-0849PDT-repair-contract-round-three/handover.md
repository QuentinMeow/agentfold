# Handover — repair contract round three

**Session:** 2026-07-23 08:49–09:36 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Made approval terminal for review successors, matching rejection and abandonment.
- Made new handover entries deterministic creation-snapshot projections.
- Allowed in-progress tasks only for blockers with committed active repair claims.
- Added staged, range, synthetic-merge, downgrade, borrowing, and claim regressions.

## How it works now

Human handover entries copy three queue fields in a fixed format; agent entries are
Action-labeled links only. Both history schema markers are sticky after activation,
while pre-marker records and whole-service removal retain compatibility. A blocking
task resumes only after the responsible agent's claim is committed.

## Decisions made for you

The round-three hardening is recorded in the
[task design](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/design.md).

## Needs your attention

- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- Free-form “declarative” handover context could still hide an arbitrary agent action,
  so human context now copies queue-owned fields and agent entries contain no prose.
- Weakening or removing either history schema marker was rejected because it would
  disable the check after adoption; only removing the complete service no-ops.

## Next steps

None.

## Deep links

- Task folder: [first-class message queue](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: not yet filed while the task remains in progress
- Commits: none — the parent session will stage and commit the complete candidate
