# Handover — repair provider action cardinality

**Session:** 2026-07-23 11:31–12:03 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Preserved the number of externally assigned actions through the projection boundary.
- Added present human-dependent boundary prose and base-form work commands to action detection.
- Kept third-person, noun-like, historical, and explicitly negated descriptions non-actionable.
- Distinguished declarative supporting-link references from imperative or trailing actions.
- Prevented a noun-summary clause from hiding a conjoined command in prose or a link label.
- Added focused unit and command-line regressions for all three panel findings.
- Passed 72 projection tests, seven GitHub adapter tests, Python compilation, and the Git whitespace check.

## How it works now

External JSON arrays contribute one action per material top-level entry; material
objects and scalars contribute one, and repeated inputs add together. The declared
section must link at least that many distinct live canonical queue items. Optional prose
also catches command-shaped work and present human-dependent release boundaries without
classifying ordinary summary language as an action. A verb-like supporting-link title
is a reference only after a declarative reference field, only when the link closes
that line, and only for an ambiguous noun title. Questions, TODOs, clear commands,
imperative cues, trailing work, and summary clauses followed by a command remain
actions.

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

Treating every line-leading work word as a command was rejected because words such as
“audit,” “review,” and “release” also introduce ordinary noun summaries. The command
grammar now distinguishes short imperatives from noun phrases that continue into a
declarative summary predicate.

## Next steps

None.

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: pending
- Commits: none — unstaged repair
