# Handover — recover stranded merged PRs

**Session:** 2026-07-24 23:05–23:06 PDT, codex
**Task:** 2026-07-24-layered-development-workspace
**Mode:** async
**Queue projection:** v1

## What happened

- Audited every GitHub pull request and confirmed PRs #8 and #10 merged into PR #7's
  task branch after PR #7 had already merged, so neither later change reached main.
- Advanced main by one portability-only coordination commit that removes a
  machine-specific interpreter link.
- Rebuilt PR #8 as draft PR #11 from current main, preserving the independently
  approved test-runner isolation while repairing its review and projection evidence.
- Rebuilt PR #10 as stacked draft PR #12, excluded 18 premature follow-up coordination
  files, repaired a linked-worktree detection gap, and obtained unanimous independent
  approval of the exact implementation candidate.

## How it works now

PR #11 is the first merge layer and remains closed until the owner reviews its exact
range. PR #12 follows it; after #11 merges, #12 must be retargeted to main, bound to
that stable base, and reviewed before merge. The six deferred follow-up tasks are
published only after #12 is admitted.

## Decisions made for you

None.

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

- The original combined branch tip was not reused because it contained an independently
  blocked implementation and premature follow-up coordination.
- Running main's old test runner in one disposable worktree redirected Git metadata and
  damaged only that local test worktree; shared identity/configuration was restored,
  and the remote was unaffected.

## Next steps

- [After the layered-workspace parent PR is admitted, publish the six preserved follow-up backlog tasks, pickup requests, and dependency actions through the live main coordination lane, then resolve this action.](../../../message-queue/needs-agent/requests/future-blocking-publish-layered-workspace-follow-ups.md)

## Deep links

- Task folder: [layered workspace](../../../tasks/3_in-review/2026-07-24-layered-development-workspace/) · Worklog: [worklog](../../../tasks/3_in-review/2026-07-24-layered-development-workspace/worklog.md) · Verification: [verification](../../../tasks/3_in-review/2026-07-24-layered-development-workspace/verification.md)
- Commits: `25d0325...fd2374d` (PR #11 candidate); `c154d87...8ca62bc` (PR #12 candidate)
