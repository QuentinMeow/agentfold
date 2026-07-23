# Handover — Harden projection grammar for provider comments

**Session:** 2026-07-23 10:36–10:59 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Recognized explicit maintainer obligations and short feedback invitations as actions.
- Stopped treating query-token question marks as questions.
- Added a rendered-prose action API and an opt-in non-action provider-comment boundary.
- Added explicit human, agent, and mixed queue-actor projection modes.
- Added focused regressions; all 63 action-projection tests pass.

## How it works now

The deterministic grammar distinguishes question punctuation from query tokens such
as `?foo`, detects visible raw-HTML asks without trusting HTML as structure, and keeps
ordinary system descriptions non-actionable. Provider adapters may opt into missing
sections for ordinary prose; any body, title, or assignment action signal still fails
until it is represented by a canonical queue-linked action section. Pull-request
summaries default to human actions; inbound reviews select agent actions, while mixed
issue/conversation surfaces let each canonical path declare who acts next.

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

A blanket check for the `?` character also treats query syntax as a human question.
The gate now counts only question punctuation and has a direct regression for `?foo`.

## Next steps

None.

## Deep links

- Task folder: [first-class message queue](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/task.md) · Worklog: [session record](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: not yet created
- Commits: none — changes remain uncommitted in the shared worktree
