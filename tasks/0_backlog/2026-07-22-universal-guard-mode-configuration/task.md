# Add one universal mode configuration for guardrails

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-22, by codex, from the owner's review of the critical-agent-guardrails proposal
**Parent:** 2026-07-22-design-critical-agent-guardrails
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-universal-guard-mode-configuration.md`; `message-queue/needs-agent/requests/future-blocking-revise-assurance-profile-scope-and-egress.md`; `message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md`; `message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md`; `message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md`; `message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md`

## Goal

Implement the human-approved template-first control surface for AgentFold guardrails.
Every automatic or costly guard must use the same `hard`, `soft`, `off`, or `manual`
mode vocabulary, so repositories can choose friction without editing guard code or
pretending disabled controls provide assurance. Capability sandboxing is not part of
this task.

## Acceptance criteria

- [ ] A canonical template defines one versioned guard-id-to-mode configuration, and
      the active repository config links to that template instead of inventing another
      schema.
- [ ] Shared runner semantics are tested: `hard` blocks, `soft` reports and exits
      successfully, `off` does not run, and `manual` runs only on explicit invocation.
- [ ] Existing automatic guard entry points are inventoried and either consume the
      universal mode or are explicitly documented as external provider policy.
- [ ] Independent-agent review is `manual` in the starter configuration and can be
      selected explicitly for high-consequence work.
- [ ] Output distinguishes disabled, not-triggered, clean, finding, incomplete, and
      error states so a weaker mode cannot masquerade as stronger assurance.
- [ ] No filesystem/network sandbox or agent-specific integration is introduced.

## Links

- Decision: `memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md`
- Design: `docs/designs/risk-tiered-agent-guardrails.md`
- Related severity work: task `2026-07-22-severity-tiers-for-reconciler-findings`
