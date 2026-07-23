# Handover — repair review-state replay

**Session:** 2026-07-23 14:45–15:20 PDT, codex
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Expanded indirect-request detection to cover evaluative courtesy phrasing.
- Closed the push-after-review bypass by replaying current formal reviews and
  unresolved diff threads on direct review events and every pull-request update.
- Added provider-neutral, versioned external-source bindings so agents can transcribe
  human review prose without modifying it; one source may own several queue actions.
- Kept the GitHub adapter thin, read-only, and independent of local CLI authentication.

## How it works now

An actionable review source must contain canonical queue links or have actor-correct
live queue items with its exact versioned `External source`. Those items remain live
until the provider resolves the thread or supersedes/dismisses the effective review;
source edits get a new identity and resurface.

## Decisions made for you

Source-bound items do not use historical tombstones; the active provider snapshot and
live queue agree until provider resolution, as recorded in
[the task design](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/design.md).

## Needs your attention

- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

Checking only the event that introduced a review action allowed a later unrelated push
to hide the failure. Replaying raw Markdown alone was also rejected because an agent
cannot edit a human review into repository-specific queue syntax.

## Next steps

None.

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: pending
- Commits: none — unstaged repair
