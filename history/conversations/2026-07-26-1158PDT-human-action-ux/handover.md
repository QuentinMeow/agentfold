# Handover — human-action UX stopping boundary

**Session:** 2026-07-26 11:58 PDT–2026-07-27 05:31 PDT, codex
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1
**Queue action-entry schema:** v3

## What happened

- Researched human–AI decision support and adopted one action-first interface: explicit previous/current/change state, symmetric outcomes and consequences, evidence and uncertainty before the recommendation, an exact silence result, plain answers, references last, and collapsed tracking.
- Reworked the three human-action templates, guidance, handover projection, six waiting reviews, and versioned enforcement. Candidate `589aafea2ec4cc7d1cda6c4f9ee4bbb50cfc5381` passed the exact commit gate with all 472 queue tests and all 11 repository test files.
- Independent reviews found real defects in headline polarity, evidence wording, immutable handover copies and renames, and rendered Markdown identity across emphasis, links, entities, Unicode, tables, raw HTML, comments, autolinks, and strikethrough. Every confirmed defect became a regression test.
- Stopped at the owner's requested clean boundary after the latest verified repair. The candidate is not merge-ready: the fresh three-reviewer first wave and two-reviewer second wave have not assessed `589aafe`.

## How it works now

Human actions lead with the task and practical stakes; machine records are last and collapsed. The repository rejects ambiguous state, asymmetric outcomes, unsupported recommendations, unsafe Markdown, broken references, altered live identity, and incorrect handover projections. The artifact-pending re-review still requests no human response until the final five-review panel publishes one exact target.

## Decisions made for you

- Use a self-contained action-first human interface and keep the queue lifecycle machine-verifiable: [decision](../../../memory/decisions/2026-07-26-human-actions-are-action-first.md).
- Treat rendered GitHub-flavored Markdown identity as security-sensitive projection data, with official cmark-gfm differentials and fail-closed external-link ownership: [task design](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/design.md).

## Needs your attention

- [Review whether self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding; then approve, request changes, or reject.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) This prevents the agent that produced a risky change from using its own note as permission to bypass the security gate. If you do not respond, unrelated work may continue but guardrail implementation cannot start and this authority split remains only a proposal.
- [Review the already-merged layered workspace design and read-only inspector, then accept it, request a named repair, or require rollback before task completion.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) This establishes how public, private, restricted, raw, and temporary content may be separated without pretending that ordinary Git layout choices enforce confidentiality. If you do not respond, the code remains on `main` without inferred human approval and the layered-workspace task remains in review.
- [Review whether the revised design clearly separates configured guard settings from the assurance supported by evidence, explains the limits of manual evidence and coverage, and states that controlling where data may be sent is outside this review and design scope; then approve, request changes, or reject.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) This keeps reported assurance tied to observed protection instead of allowing an agent to select or claim a reassuring label. If you do not respond, unrelated work may continue but guardrail implementation cannot start and the revised explanation is not accepted.
- [Review whether the incident-recovery boundary and sequence are complete; then approve, request changes by naming any missing recovery obligation, or reject.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) This prevents deleting one Git file from being mistaken for complete recovery after credentials or private data may already exist in remote copies and logs. If you do not respond, unrelated work may continue but guardrail implementation cannot start and the recovery sequence remains only a proposal.
- [Review the already-merged exact Git range, then accept it, request a named repair, or require rollback before task completion.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) This boundary protects every hook-launched repository test from accidentally redirecting Git operations into the checkout that invoked the test runner. If you do not respond, the code remains on `main` without inferred human approval and the isolation review remains unresolved.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) This review checks whether readers can distinguish a guard being available in a template from that guard being enabled and producing evidence. If you do not respond, the existing decision remains authoritative, the expanded explanation stays in place, and implementation may proceed under the decided four-mode policy.

## Dead ends

- Approximate Markdown regexes repeatedly produced visible-identity collisions. The durable direction is official cmark-gfm-compatible parsing plus generated differentials, not another narrow exception.
- The artifact-pending human re-review cannot be rewritten merely as a progress report because its live identity is immutable. Publish its v2 waiting form only with the final exact panel-approved target.

## Next steps

- [Research, design, implement, and verify an action-first format that makes every human-attention file self-contained, distinguishes current from proposed behavior, presents clear choices with rationale and consequences, and gives an evidence-backed agent recommendation.](../../../message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md)

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/task.md) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: [verification](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/verification.md)
- Commit: `589aafea2ec4cc7d1cda6c4f9ee4bbb50cfc5381`
