# Handover — configurable test gates checkpoint

**Session:** 2026-07-27 09:56–10:07 PDT, codex
**Task:** 2026-07-27-configure-test-gates-and-time-budgets
**Mode:** async
**Queue projection:** v1

## What happened

- Preserved the complete pre-approval implementation and blocker records in local checkpoint
  `f2d220b1ae9ddc0f47d54252c4804c356ee780c1` on the task branch.
- Ran the full final gate on the exact staged candidate: all 15 files passed in 218.94 seconds.
- Confirmed the real commit hook reused that exact evidence after Git's index refresh and passed
  the routine lane in 6.93 seconds.
- Kept the branch local and the trusted provider workflow absent while its authorization remains
  unresolved in the live decision item.

## How it works now

The task is durably checkpointed in `2_blocked`, stacked on PR 16's head. Local routine and
final lanes are implemented and verified; provider-hard controller logic is present, but the
candidate-controlled pull-request workflow remains execution evidence rather than enforcement.

## Decisions made for you

- Preserved the pre-approval work locally without pushing or opening a pull request.
- Preserved the earlier handover's immutable creation bytes; this handover records the later
  checkpoint instead of rewriting that snapshot.

## Needs your attention

- [Choose whether to authorize the split trusted pull-request gate or keep final verification manual/external.](../../../message-queue/needs-human/decisions/blocking-approve-split-trusted-pull-request-gate.md) — Why-you-might-care: This decides whether AgentFold may claim a hard pull-request boundary instead of only producing candidate-controlled execution evidence. || If-you-do-nothing: The task remains blocked and no trusted provider workflow is installed.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- Raw index-file bytes cannot identify staged semantics because Git refreshes cache/stat data
  before the hook; the successful real commit confirms semantic identity is the needed boundary.
- The first handover is an immutable pre-checkpoint snapshot and is not a file to revise.

## Next steps

None.

## Deep links

- Task folder: [task](../../../tasks/2_blocked/2026-07-27-configure-test-gates-and-time-budgets/task.md) · Worklog: [worklog](../../../tasks/2_blocked/2026-07-27-configure-test-gates-and-time-budgets/worklog.md) · Verification: [verification](../../../tasks/2_blocked/2026-07-27-configure-test-gates-and-time-budgets/verification.md)
- Commits: `f2d220b1ae9ddc0f47d54252c4804c356ee780c1`
