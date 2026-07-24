# Handover — repair agent obligation and task projection

**Session:** 2026-07-23 13:12–13:12 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Added provider-neutral recognition for direct agent, assistant, bot, and worker
  obligations while preserving negated, historical, system, and capability prose.
- Added indirect solicitation recognition for present curiosity, interest, or
  wondering about a recipient's thinking, approach, feedback, input, or opinion.
- Closed task `Queue actions` values to exact canonical tokens and separators through
  one parser shared by provider projection and reconciliation.
- Added focused projection and task-structure regressions; an independent bounded
  retest passed all 22 cases.
- Passed all 83 projection tests, eight provider-adapter tests, 209 queue/history
  tests, Python compilation, and the Git whitespace check.

## How it works now

Direct modal work assigned to a generic automation role is action prose, while a
capability statement such as being able to inspect changes remains descriptive.
Present first-person curiosity becomes action prose only with a recipient-directed
thought or response target.

A task's `Queue actions` field contains exactly lowercase `none` or unique backticked
canonical queue paths separated by semicolons or commas. Both task-scoped provider
checks and repository reconciliation consume the same closed parser.

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

Broad mention-based classification was unnecessary. The direct-obligation grammar
keeps automation-role capability and historical descriptions outside the action set.
Extracting paths from arbitrary task prose was also discarded because projection
fields need a complete-value grammar.

## Next steps

None.

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: pending
- Commits: none — unstaged repair
