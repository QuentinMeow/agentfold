# Core portability uses deterministic admission and manually selected semantic review

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** human (guardrail design review)
**Description:** Core substitution evidence remains automatic; independent-agent review is manual, explicit, and revision-bound
**Review-by:** 2027-02-15
**Supersedes:** `memory/decisions/2026-07-22-agentfold-core-requires-substitutability.md`

## Context

The superseded core-portability decision correctly kept personal, provider-specific,
and user-global setup outside AgentFold. Its consequence required an independent verdict
for every core task. The owner's later guardrail review rejected always-on expensive
agent review and selected one future `hard`/`soft`/`off`/`manual` configuration surface.
That general decision is recorded in
`memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md`.

## Decision

Core changes still carry structured agent, provider, and adopted-repository substitution
evidence. Git hooks and CI validate that evidence and reject obvious user-global access
automatically.

Independent-agent semantic review is manual by default. A human or selected future guard
profile invokes the reviewer only when its cost is justified. The repository command
`automation/check_core_scope.py --require-review` validates the resulting receipt; it
does not launch an agent. A valid receipt names an immutable reviewed commit, contains an
approve majority from claimed reviewer labels other than the task claimant, and becomes
stale after any later core change. Normal automatic output says explicitly that manual
review was not invoked.

Reviewer labels in repository text are auditable claims, not authenticated identities.
High-assurance identity and provider-backed approval remain future guardrail layers; the
manual panel or human operator is responsible for actual independence today.

## Alternatives considered

- Keep review mandatory in CI — rejected because it spends tokens on every core change
  and contradicts the owner's universal-mode decision.
- Remove semantic review — rejected because explicit use remains valuable for
  high-consequence boundary changes.
- Let any historical verdict satisfy the flag — rejected because later core edits can
  invalidate the judgment while preserving the text.
- Infer reviewer aliases from shared words — rejected because distinct agents and people
  often share runtime, domain, session, or surname tokens.

## Consequences

Deterministic core admission stays active by default. Manual review has an honest,
content-bound audit trail and can be selected without becoming an always-on workflow.
The backlog task `2026-07-22-universal-guard-mode-configuration` will replace the
temporary flag with the shared four-mode runner; it must preserve revision binding and
explicit skipped-state output.
