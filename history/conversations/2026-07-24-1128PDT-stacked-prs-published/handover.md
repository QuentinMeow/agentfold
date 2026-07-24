# Handover — stacked PRs published

**Session:** 2026-07-24 11:28–13:46 PDT, codex
**Task:** `2026-07-23-first-class-message-queue`; `2026-07-24-isolate-test-git-environment`; `2026-07-24-layered-development-workspace`
**Mode:** async
**Queue projection:** v1

## What happened

- Fast-forwarded PR #7 to `d7eefce`, joining the authorized coordination base and
  preserving the staged-merge provenance implementation plus its remaining gap task.
- Published draft PR #8 as the exact three-file test-runner isolation layer and draft
  PR #10 as the layered workspace design, inspector, review, and six follow-up task
  families.
- Preserved the completed layered source at
  `codex/backup-layered-publication-dcbb2fc`; no old implementation branch was
  rewritten or deleted.
- Passed all local commit gates: PR #7 ran 8/8 suites, PR #8 ran 9/9, and PR #10 ran
  10/10; focused queue, runner, and inspector suites and the reconciler also passed.
- Stopped implementation hardening at the owner's request. Current remote failures are
  recorded for later work rather than repaired in this publication session.

## How it works now

The review order is PR #7, then PR #8, then PR #10. PRs #8 and #10 are drafts whose
formal queue reviews stay artifact-pending until the preceding base is admitted.
PR #10 contains the six dependency-gated workspace follow-up tasks, while PR #7
contains the unclaimed staged-merge provenance completion task.

## Decisions made for you

- The owner chose immediate draft publication with explicit gaps over another
  hardening/polish cycle.
- One mistaken non-task-head draft, PR #9, was closed and replaced by PR #10 on the
  canonical layered task branch.

## Needs your attention

- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: The approved answer remains queued for its agent folding commit.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: PR #7 remains unmerged.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: PR #8 and its dependent layer remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This reviews explanation quality, not the already-decided template-first policy. || If-you-do-nothing: The current explanation and ADR remain in force.

## Dead ends

- The GitHub connector could compare and read PRs but returned 403 for creation; the
  authenticated `gh` fallback created the drafts.
- A draft layered PR on a non-task head could not identify one parent task after the
  six follow-up tasks were added. PR #9 was closed and recreated as PR #10 on the
  canonical task branch.
- Current remote checks are not green: PR #7's trusted-base review collector is absent
  from its base and its synthetic range shape is rejected; PR #8's publication branch
  name fails core-scope; PR #10 correctly stops at its unresolved merge review and also
  sees the known developer-local absolute-path link.

## Next steps

- [Continue the queue-owned human review, fold the response durably, then finalize PR #7's independent panel and exact merge receipt.](../../../message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md)
- [Take over branch task/2026-07-24-isolate-test-git-environment, complete its TDD fix, and prove that hook-launched tests cannot mutate the invoking repository's config, refs, or worktree indexes.](../../../message-queue/needs-agent/requests/blocking-finish-test-runner-git-environment-isolation.md)
- [After the layered-workspace parent PR is admitted, publish the six preserved follow-up backlog tasks, pickup requests, and dependency actions through the live main coordination lane, then resolve this action.](../../../message-queue/needs-agent/requests/future-blocking-publish-layered-workspace-follow-ups.md)

## Deep links

- Task folders: [message queue](../../../tasks/3_in-review/2026-07-23-first-class-message-queue/) · [isolation](../../../tasks/3_in-review/2026-07-24-isolate-test-git-environment/) · [layered workspace](../../../tasks/1_in-progress/2026-07-24-layered-development-workspace/)
- Commits: PR #7 `d7eefce`; PR #8 `c544360`; PR #10 `0a48154`
- Pull requests: https://github.com/QuentinMeow/agentfold/pull/7 · https://github.com/QuentinMeow/agentfold/pull/8 · https://github.com/QuentinMeow/agentfold/pull/10
