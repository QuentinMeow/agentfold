# Worklog — Design layered guardrails for critical agent obligations

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-22 — critical-agent-guardrails (codex)

- Completed the queue ritual, mapped the root contracts and existing design-review
  findings, and claimed the task on its required branch.
- Preserved the pre-existing edit to
  message-queue/needs-human/reviews/design-review-direct-fixes.md untouched.
- Ran three independent breadth-first research passes on agent-oriented software design,
  PII/secret defense in depth, and filesystem/Git enforcement, then verified the main
  claims against primary or authoritative sources.
- Added `docs/` and the proposed risk-tiered guardrail design; updated root routing,
  README, ask-me-anything routing, and both roadmap views.
- The first adversarial panel unanimously blocked on concrete receipt, authority,
  redaction, outage, provider-capability, and contextual-replay scenarios. Revised the
  design to separate self-claims from authenticated authority, bind exceptions to sinks
  and repositories, add capability profiles and sink guards, and make carry-forward
  context-aware; the second verdict was unanimously approve.
- Ran the reconciler and service tests successfully, filed the optional human review,
  recorded verification, and completed the session handover.

## 2026-07-22 — publish-guardrails-pr (codex)

- Verified that GitHub CLI authentication is valid outside the restricted execution
  environment; the apparent expiration was a keychain-access false negative, not an
  expired credential or a repository setup problem.
- Preserved the human's `ack` for the earlier design-review wording in commit
  `7fee36b`, then removed the resolved review item from the live queue as its lifecycle
  requires; Git history remains the archive.
- Confirmed the full local commit range, pushed
  task/2026-07-22-design-critical-agent-guardrails, and opened draft PR #4 with an
  explicit review checklist covering the security boundary and assurance claims.
- Verified the PR's remote head, base, file list, and aggregate additions/deletions
  against the pushed branch before the publication handover update.

## 2026-07-22 — fold human design review (codex)

- Preserved and claimed both human review responses before folding them.
- Recorded approval of the provenance principle wording without changing the approved
  principle or its immutable ADR.
- Revised the critical-obligations proposal to defer sandboxing, ship mechanisms as
  templates, use one `hard`/`soft`/`off`/`manual` configuration surface, and
  keep token-expensive independent-agent review manual in the starter template.
- Recorded the durable decision in
  `memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md`
  and removed both resolved review projections after their answers were folded.
