# Handover — derived-assurance review

**Session:** 2026-07-24 00:12–01:38 PDT, codex
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Folded the owner's conceptual approval into a durable decision: repositories
  configure guard bindings, while AgentFold derives evidence-backed assurance per
  obligation and scope.
- Reworked the guardrail design, task, and roadmap; controlled egress is reference-only
  and has no implementation path without a separate explicit approval.
- Fixed a queue-lifecycle deadlock so structured successor fields do not make a resolved
  predecessor look like a live generic link.
- Retracted stale design reviews before changing their target, then republished all five
  against digest `344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f`.
- Pushed the clean branch through `ef0e520`; every pre-commit repository suite passed,
  including all 262 queue tests.

## How it works now

Guard modes configure individual obligation/scope/detector/trigger bindings. Reports
derive current coverage, health, and enforcement from observed evidence; they are not
selectable labels, and uninvoked manual guards contribute no current evidence. The
exact revised design still needs confirmation before the remaining questions proceed.

## Decisions made for you

Assurance is derived rather than configured; controlled egress is unapproved scope:
[decision](../../../memory/decisions/2026-07-23-assurance-profile-review-disposition.md).

## Needs your attention

- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

`git commit --only` creates a temporary index that this repository's snapshot-sensitive
tests cannot inspect; it produced synthetic `git cat-file` failures. Use a normal index
with only the intended paths staged. Do not treat the conceptual approval as approval
of revised bytes; the revision-bound queue item remains waiting.

## Next steps

- [Continue the queue-owned human review one question at a time, fold each response durably, then finalize PR #7's exact review artifact and independent panel before merge.](../../../message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md)

## Deep links

- Task folder: [task](../../../tasks/3_in-review/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/3_in-review/2026-07-23-first-class-message-queue/worklog.md) · Verification: [verification](../../../tasks/3_in-review/2026-07-23-first-class-message-queue/verification.md)
- Commits: `4f83e28` through `ef0e520` · PR: https://github.com/QuentinMeow/agentfold/pull/7
