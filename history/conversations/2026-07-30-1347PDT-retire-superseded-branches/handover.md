# Handover — retire superseded branches

**Session:** 2026-07-30 13:47–13:52 PDT, Claude
**Task:** none — repository maintenance
**Mode:** async
**Queue projection:** v1

## What happened

- Confirmed `exp/c-tiered` no longer exists: it was already deleted on 2026-07-30 after
  `tasks/4_done/2026-07-29-defer-full-suite-to-push-boundary/design.md` inventoried every part
  of the experiment against where it went.
- Checked all five remaining local branches against `main`; none is merged, so nothing was
  removable on merge status alone.
- Deleted `codex/pre-audit-linkage-e52cd9e` (was `e52cd9e`). All three of its commits have
  patch identifiers identical to three commits on
  `task/2026-07-26-resolve-queue-items-whose-evidence-already-merged`, and it holds no file
  that branch lacks.
- Deleted `codex/prestack-config-test-gates-safety` (was `78a5ba2`). Its content is superseded
  by `task/2026-07-27-configure-test-gates-and-time-budgets`; its single unique file was a
  human decision item that the task branch retired on 2026-07-28.
- Kept all three `task/` branches: each carries unmerged work for a task that is still open.

## How it works now

Four local branches remain: `main` (level with `origin/main` at `6cd2de9`) and the three
`task/` branches whose tasks sit in `1_in-progress` or `3_in-review`. The reconciler reports
zero findings, and no tracked file changed, so this session produced no commit beyond this
handover. Ten linked worktrees under `/private/tmp` remain; five of them hold uncommitted
changes and none was touched.

## Decisions made for you

Deleted a branch only when its content was provably reproduced on a live task branch —
identical patch identifiers plus no unique file. Every branch with unproven unique history was
kept. No archive tag was created, because neither branch held content that exists nowhere else.

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

Two commits on `codex/prestack-config-test-gates-safety` had no patch-identifier twin on the
task branch, which first looked like unique work worth keeping. Comparing file trees instead of
patches showed the task branch had simply reworked them further, and that the only genuinely
absent file was an already-retired queue item. Patch-identifier equality alone stays too strict
a signal once a branch has been reworked rather than rebased.

## Next steps

None.

## Deep links

- Task folder: none · Worklog: none · Verification: this handover
- Commits: none — two local refs deleted, `e52cd9e` and `78a5ba2`, both reachable from the task
  branches that superseded them
