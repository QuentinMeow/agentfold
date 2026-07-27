# Handover — coordinate configurable test gates

**Session:** 2026-07-27 06:19–07:09 PDT, codex
**Task:** 2026-07-27-configure-test-gates-and-time-budgets
**Mode:** async
**Queue projection:** v1

## What happened

- Reconstructed the live branch and pull-request stack; draft PR 16 is the direct code base.
- Preserved the original dirty `main` checkout by validating coordination records in isolated
  worktrees, then published them directly to `main` after the owner chose Option A.
- Collected independent design and implementation reviews. They kept the two-lane direction
  but required precise manual-versus-hard behavior, critical bindings, whole-gate timing,
  exact tested views, Python 3.7 compatibility, and nonblocking performance filing.
- Folded the owner's authorization into this record and atomically claimed the child task.

## How it works now

The child task is claimed and ready for implementation. Its branch must be based on PR 16's
head and target `task/2026-07-26-accelerate-development-feedback`; the unpublished queue-repair
and human-action branches are separate and must not enter this stack.

## Decisions made for you

The owner authorized record-only live coordination commits directly to `main`, matching
`handbook/git-workflow.md`. The implementation contract is bounded to test-gate `manual` and
`hard` behavior and does not preempt the blocked universal guard-mode task.

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

An isolated Git index was insufficient because the reconciler intentionally scans candidate
files in the working tree as well as the index. Clean temporary worktrees were required.

## Next steps

None.

## Deep links

- Task folder: [configurable test gates](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/) · Worklog: [coordination record](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/worklog.md) · Verification: not created yet
- Commits: `762c9cf`, `90acda5`, `a0358f3`, `5388e45`, and this resolving claim commit
