# Handover — Repair external action projection panel findings

**Session:** 2026-07-23 10:13–10:14 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Closed inline-code action-label collisions in both pull-request and handover projections.
- Broadened ordinary request detection and made rendered HTML action attributes visible.
- Added generic external-action/prose inputs and wired current pull-request assignment state.

## How it works now

One shared visible-token normalizer preserves code contents and ignores only structural
link destinations. Provider adapters may pass any number of external-action state and
additional-prose environment inputs; the core gate interprets no provider policy.
Strict handover entries reject raw HTML from their original source.

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

Checking the semantic handover section could not see raw HTML that the semantic parser
correctly blanks. Strict validation now inspects the matching raw section only for the
presence of HTML and otherwise keeps structural decisions on semantic Markdown.

## Next steps

None.

## Deep links

- Task folder: [first-class message queue](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/task.md) · Worklog: [session record](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: not yet created
- Commits: none — changes remain uncommitted in the shared worktree
