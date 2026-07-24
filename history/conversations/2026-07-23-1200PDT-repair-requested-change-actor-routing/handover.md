# Handover — repair requested-change actor routing

**Session:** 2026-07-23 12:00–12:40 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Made requested review changes create a claimable agent repair instead of routing the
  next move only to a human review.
- Re-review is mandatory and artifact-pending; repair completion cannot count as
  acceptance of a revision the human did not approve.
- Bound both successors to the old review's context and timing, with reciprocal
  lineage and durable repair evidence.
- Added bypass and contract regressions; all 208 queue/history tests passed.
- Preserved the prior decided ADR unchanged and recorded the correction in a new ADR.

## How it works now

Deleting a `changes-requested` review introduces an open agent repair and a distinct
human re-review awaiting that repair's artifact. The repair is the only live owner of
the requested work; the dependent review preserves the original boundary until a later
terminal disposition.

## Decisions made for you

- Required the actor-correct two-action continuation described in
  [the superseding ADR](../../../memory/decisions/2026-07-23-requested-review-changes-route-through-agent-repair.md).

## Needs your attention

- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

An optional re-review was rejected because it could let a completed repair erase the
unaccepted review boundary. Copying the repair into the follow-up review was also
rejected because it would create two live owners for one action.

## Next steps

None.

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: pending
- Commits: none — unstaged repair
