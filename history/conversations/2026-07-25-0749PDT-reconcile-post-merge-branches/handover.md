# Handover — reconcile post-merge branches

**Session:** 2026-07-25 07:49–08:20 PDT, codex
**Task:** 2026-07-25-reconcile-post-merge-branch-state
**Mode:** async
**Queue projection:** v1

## What happened

- Published the 18 layered-workspace follow-up records preserved at immutable source
  `9d7bb1d`; six backlog tasks now have queue-owned pickups and dependency actions.
- Bound the admitted PR #7 and PR #12 artifacts to their still-unanswered human review
  records without treating GitHub merges as review answers.
- Removed nine obsolete worktrees, all 56 non-main local branches, and six obsolete
  remote branches; retained the rejected PR #5 remote as audit history.
- Verified all 10 repository test files and the reconciler, then completed the
  records-only reconciliation task.

## How it works now

The primary checkout is the only worktree and local branch, on current main. The only
non-main remote branch is the intentionally retained PR #5 audit branch. The layered
manifest task is visible in backlog with an unresolved parent-completion dependency at
its start boundary.

## Decisions made for you

None. Provider admission supplied no human disposition; existing intent remains.

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

- Merging or cherry-picking the old backup branches was rejected because their
  implementation is superseded and their useful coordination records are now on main.
- Provider admission supplied merge evidence; no explicit human review response
  exists.

## Next steps

- [After `2026-07-24-layered-development-workspace` is reviewed, verified, and done, verify its completion evidence and remove this dependency action and its reciprocal task link before claiming the manifest task.](../../../message-queue/needs-agent/requests/future-blocking-complete-parent-before-workspace-manifest.md)

## Deep links

- Task folder: [task](../../../tasks/4_done/2026-07-25-reconcile-post-merge-branch-state/task.md) · Worklog: [worklog](../../../tasks/4_done/2026-07-25-reconcile-post-merge-branch-state/worklog.md) · Verification: [verification](../../../tasks/4_done/2026-07-25-reconcile-post-merge-branch-state/verification.md)
- Commits: `fdcac42`, `900aed7`, `f4de917`, `5ecd540`, `d97ffb4`, `109c9d5`, and this handover's creation commit.
