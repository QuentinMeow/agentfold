# Handover — stacked PR publication

**Session:** 2026-07-24 10:41–11:28 PDT, codex
**Task:** `2026-07-23-first-class-message-queue`; `2026-07-24-isolate-test-git-environment`; `2026-07-24-layered-development-workspace`
**Mode:** async
**Queue projection:** v1

## What happened

- Reconstructed the live task and queue state from `origin/main` as 12 separate
  lifecycle commits; nothing was pushed directly to the shared branch.
- Preserved two rejected local coordination histories and the original mixed workspace
  source instead of rewriting or deleting them.
- Repaired the layered-workspace preflight blockers in immutable candidate `dcbb2fc`:
  per-worktree metadata overlap, inline Git-config parsing, exact include sections, and
  publication authority bound to the complete evidence envelope.
- Ran all 39 focused inspector tests and all 10 repository test files successfully;
  the reconciler and diff hygiene checks passed.
- Filed the explicit direct-main authorization decision that now blocks publication of
  the stacked PRs.

## How it works now

Branch `codex/coordination-publication-v2` carries the clean 12-commit lifecycle
sequence through `cfe198d` plus this handover tail, and contains only live
coordination. PR #7 and the isolation task are in review with artifact-pending merge
actions; the layered task remains in progress until the repaired candidate receives a
fresh exact-revision panel. No new PR was opened and no implementation was pushed to
`main`.

## Decisions made for you

- Deferred six layered follow-up task bundles behind one live publication action; the
  exact 18 coordination files remain preserved at immutable source `9d7bb1d`.
- Required explicit owner authority before any direct shared-main push; no fallback
  coordination PR was invented.

## Needs your attention

- [Approve or decline pushing the coordination-only commit sequence directly to origin/main before Codex publishes the three dependent pull requests.](../../../message-queue/needs-human/decisions/blocking-approve-direct-main-coordination-push.md) — Why-you-might-care: The repository requires task claims, queue lifecycle, owner decisions, and handovers on main immediately, while the instruction to create sequential PRs did not explicitly authorize a shared-branch push. || If-you-do-nothing: The implementation branches and repairs remain preserved, but Codex does not publish the stack with stale canonical task and queue state.
- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- Do not replay the three task states in one aggregate commit: PR #7's joined-history
  checks reject skipped admission, claim, response, and folding edges.
- Do not copy complete task evidence onto pre-merge `main`: branch-only paths make the
  canonical link check fail.
- Do not keep the legacy direct-push decision live when PR #7 joins: it must be
  answered, claimed, folded to an ADR and roadmap update, then deleted first.

## Next steps

- [Take over branch task/2026-07-24-isolate-test-git-environment, complete its TDD fix, and prove that hook-launched tests cannot mutate the invoking repository's config, refs, or worktree indexes.](../../../message-queue/needs-agent/requests/blocking-finish-test-runner-git-environment-isolation.md)
- [Continue the queue-owned human review, fold the response durably, then finalize PR #7's independent panel and exact merge receipt.](../../../message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md)
- [After the layered-workspace parent PR is admitted, publish the six preserved follow-up backlog tasks, pickup requests, and dependency actions through the live main coordination lane, then resolve this action.](../../../message-queue/needs-agent/requests/future-blocking-publish-layered-workspace-follow-ups.md)

## Deep links

- Task folders: [message queue](../../../tasks/3_in-review/2026-07-23-first-class-message-queue/) · [isolation](../../../tasks/3_in-review/2026-07-24-isolate-test-git-environment/) · [layered workspace](../../../tasks/1_in-progress/2026-07-24-layered-development-workspace/)
- Commits: `ecce610..cfe198d` plus this handover tail; repaired implementation candidate `dcbb2fc`
