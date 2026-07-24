# Handover — consolidate unmerged work

**Session:** 2026-07-24 13:55–14:20 PDT, codex
**Task:** none — branch consolidation and exact-tip cleanup
**Mode:** async
**Queue projection:** v1

## What happened

- Created `codex/consolidate-unmerged-work-2026-07-24` from refreshed
  `origin/main` at `2372e48`.
- Joined the later PR #8 and PR #10 merge descendants at `7fa18ca`, plus the standalone
  stacked-publication handover at `d920bd4`, without rewriting either history.
- Filed task `2026-07-24-reconcile-post-merge-stack-state` for stale queue, task,
  verification, roadmap, and branch state rather than inferring review answers.
- Removed five exact-tip-main-reachable local branches and two clean temporary
  worktrees. No surviving remote branch tip was reachable from `origin/main`.
- Preserved rejected PR #5 and older publication/source branches. They are audit or
  superseded history, and their exact tips have not merged to main.

## How it works now

The consolidation branch contains all current main-bound implementation from PRs #8
and #10 on top of the latest main, plus the previously standalone publication
handover. It does not import stale lifecycle snapshots or the Codex-specific PR #5
implementation; their branches remain available for audit until a later disposition.

## Decisions made for you

- PR #5 remains rejected core-scope audit history, matching its two explicit GitHub
  closure comments and clean replacement PR #6.
- A branch was cleaned only when its exact tip was an ancestor of refreshed
  `origin/main`; patch equivalence or inclusion only on the consolidation branch did
  not qualify.

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

- The cleanup helper classified two main-reachable PR #7 preparation branches by their
  moved remote upstreams instead of deleting them. Exact ancestry was rechecked and
  they were removed with safe `git branch -d`.
- Older isolation, layered-workspace, detector-review, and queue-hardening branches
  contain stale or alternative lifecycle snapshots. Their current implementation is
  represented by the joined PR stack, so merging those trees would regress canonical
  queue and task state.

## Next steps

- [Claim the post-merge stack reconciliation task, align its durable queue and task state with exact GitHub evidence, and clean source branches only after their tips reach main.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-reconcile-post-merge-stack-state.md)

## Deep links

- Task folder: [post-merge reconciliation](../../../tasks/0_backlog/2026-07-24-reconcile-post-merge-stack-state/) · Worklog: not created until claim · Verification: not created until review
- Commits: `0d660c1`, `39e279b`, `92e843f`
