# Handover — clean merged branches

**Session:** 2026-07-25 06:10–06:20 PDT, Codex
**Task:** none — repository maintenance
**Mode:** async
**Queue projection:** v1

## What happened

- Refreshed and pruned `origin`; `origin/main` is
  `c9f5244759dec308b49cdfb8d5a440a247431a5e`.
- Inspected every local branch, remote branch, and linked worktree against the
  refreshed `main`, including patch-equivalence and pull-request state.
- Removed the three local branches whose commits are ancestors of `main`:
  `codex/portable-queue-worklog-link-v2`,
  `task/2026-07-24-isolate-test-git-environment`, and
  `task/2026-07-24-layered-development-workspace`.
- Removed those branches' three worktrees. The only dirty one contained one file
  whose bytes exactly matched `origin/main`.
- Preserved the stale former local `main` as
  `codex/archived-stale-main-b359633` because it has one branch-only commit and an
  untracked human-action file; the primary workspace now uses a fresh `main`
  tracking `origin/main`.

## How it works now

The primary workspace is on the refreshed `main`. Fetching pruned the two merged
task branches already deleted on GitHub; no surviving remote branch was removed
because each still contains branch-only changes. Ten worktrees remain because their
branches or uncommitted files are not fully contained in `main`.

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

The first cleanup preview resolved the base as the stale local `main` because another
worktree still held that branch. Renaming the stale branch preserved its unmerged data
and allowed the primary workspace to recreate `main` from `origin/main`.

## Next steps

None.

## Deep links

- Task folder: none · Worklog: none · Verification: this handover
- Commits: `c9f5244759dec308b49cdfb8d5a440a247431a5e`
