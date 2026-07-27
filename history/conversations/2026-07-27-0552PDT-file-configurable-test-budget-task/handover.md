# Handover — file the configurable test-budget task

**Session:** 2026-07-27 05:52–05:58 PDT, codex
**Task:** 2026-07-27-configure-test-gates-and-time-budgets
**Mode:** async
**Queue projection:** v1

## What happened

- Filed a focused backlog task that makes the routine harness target 60 seconds by default and
  puts routine and final timing targets in one repository-local configuration file.
- Added a decided design comparing three test-sequencing options. It recommends a budgeted
  routine lane plus complete verification that is manual or automatic only at a final boundary.
- Added an eight-step implementation plan and a pickup request so another agent can claim the
  work without relying on this chat.
- Kept credentials, PII, authorization, destructive operations, publication, deployment, and
  other configured one-way-door scopes outside the reversible deferral rule.

## How it works now

This session filed design and coordination records only; the test runner and hooks have not
changed. The task is unclaimed in the backlog. Its acceptance criteria require end-to-end timing,
honest deferred-coverage reporting, exact-evidence reuse, and automatic deduplicated task filing
whenever a configured gate exceeds its target.

## Decisions made for you

Use the budgeted routine lane and configurable final lane described in [the task design](../../../tasks/0_backlog/2026-07-27-configure-test-gates-and-time-budgets/design.md); keep the existing complete-every-commit sequence and CI-only testing as rejected alternatives.

## Needs your attention

- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

The existing continuation task was too broad to serve as the implementation brief: it combines
the feedback budget with queue-repair follow-up and a repository-wide multi-agent investigation.
This task is a focused child instead of rewriting that already staged record.

## Next steps

- [Claim the linked backlog task, then implement its configuration, routine/final gates, timing evidence, and deterministic performance-task filing as one bounded workstream.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-configure-test-gates-and-time-budgets.md)

## Deep links

- Task folder: [configurable test gates](../../../tasks/0_backlog/2026-07-27-configure-test-gates-and-time-budgets/) · Worklog: [filing record](../../../tasks/0_backlog/2026-07-27-configure-test-gates-and-time-budgets/worklog.md) · Verification: not created because no implementation or test result was claimed
- Commits: none; the new records are present in the working tree and are not staged
