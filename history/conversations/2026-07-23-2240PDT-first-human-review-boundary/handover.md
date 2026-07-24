# Handover — first human-review boundary

**Session:** 2026-07-23 19:16–22:40 PDT, codex
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Verified that the final heads of merged PRs #4 and #6 remain ancestors of the latest
  origin/main, which is unchanged at `acc23b6289f5ca66744718af379aba0468be93e2`.
- Finished the already reproduced queue-lifecycle and task-topology repairs and added a
  regression for future resolution-evidence paths.
- Stopped implementation expansion at the owner's requested first human-review
  boundary; one narrowly scoped follow-up now lives in backlog with its own agent queue
  message.
- Moved the current task to review with full-run verification evidence; its human
  judgments remain six separate, context-rich queue items.

## How it works now

Every durable human or cross-session agent action is owned by one timing-prefixed queue
file. Exact action links are projected onto other surfaces. Cleanup of reviews, task
lifecycle, provider-source release, and task action origin are enforced from Git/filesystem
evidence, while first-adoption scanning and history-scan performance remain deferred.

## Decisions made for you

The change was frozen at the first human-review boundary. The only deferred
implementation is task `2026-07-23-post-review-task-admission-hardening`.

## Needs your attention

- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

Treating PR prose as an independent action channel lost context and queue ownership.
Continuing automated hardening before human review also made the review surface too
large, so the remaining adoption/performance work was deferred instead.

## Next steps

- [After the parent change's first human review is recorded, claim the deferred task-admission hardening task and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-post-review-task-admission-hardening.md)

## Deep links

- Task folder: [task](../../../tasks/3_in-review/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/3_in-review/2026-07-23-first-class-message-queue/worklog.md) · Verification: [verification](../../../tasks/3_in-review/2026-07-23-first-class-message-queue/verification.md)
- Commits: acc23b6 through the publication branch tip
