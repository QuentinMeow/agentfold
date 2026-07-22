# Handover — protect core portability

**Session:** 2026-07-22 11:47–13:00 PDT, codex
**Task:** 2026-07-22-protect-core-portability
**Mode:** async

## What happened

- Closed the incident-specific draft PR and replaced it with a clean branch based
  directly on the guardrails-design branch; no Codex/GitHub-auth setup is present.
- Added a vendor-neutral core-admission receipt and Git gate covering agent, provider,
  adopted-repository, user-global-state, and thin-adapter boundaries.
- Converted adversarial findings into 41 focused canaries, then recorded independent
  approvals for architecture, flexibility, and correctness.
- Opened draft PR #6 with five review hotspots visible at the top; both CI runs pass,
  and closed PR #5 links forward to it without losing the rejected-design history.

## How it works now

Core-changing task branches declare repository scope, complete a substitution receipt,
and need an independent approve majority before review. The deterministic gate checks
the selected Git tree and obvious repository-boundary violations; semantic reviewers
still decide whether the rationale is true, so future smarter agents are not forced
through a vendor-specific implementation path.

## Decisions made for you

- The owner's correction is recorded as the core-substitutability boundary in
  [`memory/decisions/2026-07-22-agentfold-core-requires-substitutability.md`](../../../memory/decisions/2026-07-22-agentfold-core-requires-substitutability.md): persistence does not imply AgentFold ownership, and personal/provider setup stays external.

## Needs your attention

- [Risk-tiered agent guardrails](../../../message-queue/needs-human/reviews/risk-tiered-agent-guardrails.md) — review the proposed PII/security boundary, acknowledgement gates, and docs routing contracts. If you do nothing, it remains a proposal and no new security enforcement begins.
- [Provenance principle wording](../../../message-queue/needs-human/reviews/provenance-principle-wording.md) — decide whether the listed instruction-bearing paths and mandatory human review are the right trust boundary. If you do nothing, the principle stands as written and its mechanical enforcement remains backlog work.

## Dead ends

- Provider names and a root-Markdown catch-all were rejected: both overfit the incident
  and constrained ordinary product docs. Exact instruction conventions plus a plain
  adapter registry preserve the boundary without pretending filenames prove semantics.
- Layered regex removal was rejected after adversarial probes found ordering and Unicode
  line-boundary gaps. A source-order CommonMark block-state parser replaced it.

## Next steps

Review draft PR #6 using its five-item checklist, then merge it only after stacked PR #4
is accepted. Keep the personal Codex safeguard in user-global configuration or a
separate personal plugin/config repository, never in AgentFold core.

## Deep links

- Task folder: [`tasks/3_in-review/2026-07-22-protect-core-portability/`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/) · Worklog: [`worklog.md`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/worklog.md) · Verification: [`verification.md`](../../../tasks/3_in-review/2026-07-22-protect-core-portability/verification.md)
- Pull request: https://github.com/QuentinMeow/agentfold/pull/6 · Commits: `4876bfd..7085e55` plus this publication handover commit
