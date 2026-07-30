# Handover — clean local branches

**Session:** 2026-07-29 18:12–18:13 PDT, Codex
**Task:** none — repository maintenance
**Mode:** async
**Queue projection:** v1

## What happened

- Refreshed and pruned `origin`; current `origin/main` is `bf6f72679d21f8ff0861fc61d184981ffba091a4`.
- Inspected every local branch against current main, GitHub pull-request state, linked worktrees,
  duplicate refs, and stash-backed recovery points.
- Deleted seven merged or obsolete local branches and removed the two clean worktrees that held
  merged coordination and PR 16 branches.
- Preserved the dirty active configurable-test-gates branch, four unproven local-only histories,
  every stash, and every dirty detached worktree.
- Left the dirty local `main` checkout untouched; it remains 19 commits behind `origin/main`.

## How it works now

Six local branches remain: `main`, the active configurable-test-gates branch, and four local-only
histories that are not safely proven obsolete. Remote-tracking refs now contain only
`origin/main`. The two deleted migration-pivot branch tips remain recoverable through
`stash@{4}` and its index parent, and one deleted safety alias remains reachable through the
retained identical safety branch.

## Decisions made for you

Used conservative cleanup: delete only ancestry-proven merged branches or refs with explicit
replacement/recovery evidence; retain ambiguous unique histories.

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

The cleanup helper could not delete the merged PR 16 branch because local `main` is intentionally
behind and dirty. After separately proving that branch is an ancestor of `origin/main` and
removing its clean worktree, its exact local ref was deleted directly with the other proven
obsolete refs. Local `main` was not pulled or reset.

## Next steps

None.

## Deep links

- Task folder: none · Worklog: none · Verification: this handover
- Commits: `bf6f72679d21f8ff0861fc61d184981ffba091a4`
