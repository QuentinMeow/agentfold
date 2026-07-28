# Handover — manual test-gate replan

**Session:** 2026-07-27 17:00–17:20 PDT, codex
**Task:** 2026-07-27-configure-test-gates-and-time-budgets
**Mode:** async
**Queue projection:** v1
**Queue action-entry schema:** v2

## What happened

- The owner's earlier Option A coordination response is already resolved on `main`.
- Two P1 findings make the automatic hard-gate state in `e70d1e1` unsafe: candidate code has an early process-termination path, and the publisher has no independent completion proof.
- Test-only migration snapshot `21d5a24` received two independent approvals; it changes no production policy.
- Records, follow-up tasks, and the plain yes/no replan request were committed in `13a60b8`.
- No push or merge happened. The configured production policy and GitHub workflow remain unchanged.

## How it works now

The complete final test remains manual rather than automatic merge enforcement. The task stays in progress while the manual-only replan is unanswered. A controlled external test oracle and a separately controlled publisher are recorded as follow-up work.

## Decisions made for you

- The current automatic publisher is not an activation candidate; the P1 findings are recorded in the task evidence.
- The existing hard-gate activation decision remains unchanged; the new clarification is the separate request for the current replan.

## Needs your attention

- [Confirm that automatic enforcement may cover only same-repository `task/**` pull requests and that those source branches will prohibit force pushes, deletion, and bypasses.](../../../message-queue/needs-human/clarifications/future-blocking-confirm-hard-gate-source-branch-protection.md) — Why-you-might-care: Without protected source history, an old successful result could be replaced or misapplied after a branch rewrite; fork pull requests do not share this controlled boundary. || If-you-do-nothing: Keep the complete final test manual and do not activate or describe the GitHub hard gate as enforced.
- [Answer yes or no: may this task switch the starter final mode from hard to manual, remove the unsafe automatic publisher, keep hard syntax reserved and fail-closed, and move real automatic enforcement to the two follow-up tasks?](../../../message-queue/needs-human/clarifications/future-blocking-confirm-manual-only-test-gate-replan.md) — Why-you-might-care: The current runner can report success after candidate code exits its own interpreter early, so its result cannot safely authorize an automatic merge. || If-you-do-nothing: The task remains in progress, final verification stays manual in practice, the automatic publisher is not activated, and no hard-enforcement claim is made.
- [Decide whether GitHub should automatically block a merge until the complete tests pass. Choose Option A to turn that protection on, or Option B to keep the final test as a manual check.](../../../message-queue/needs-human/decisions/future-blocking-activate-github-hard-test-gate.md) — Why-you-might-care: Option A prevents a pull request from merging into `main` when the complete tests are missing, failing, or no longer match the code to be merged. Option B relies on a maintainer to run and check those tests. || If-you-do-nothing: Keep the complete final test manual. Do not say that GitHub enforces it automatically.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

The same-interpreter automatic design in `e70d1e1` is unsafe: a candidate can exit before the trusted assertions finish. Production policy remains unchanged while the yes/no clarification is unanswered.

## Next steps

- [Claim the external test-oracle task, create its plan and worklog, and remove this pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-control-external-test-oracle-and-stage-migration.md)
- [After the external test-oracle task is done, claim the OIDC App publisher task, create its plan and worklog, and remove this pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-publish-hard-gate-through-external-oidc-app.md)
- [Claim the time-budget investigation, preserve its generated evidence, and remove this pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-investigate-routine-test-budget-0d79a10895.md)

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/worklog.md) · Verification: [verification](../../../tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/verification.md)
- Commits: `21d5a24` · `13a60b8`
