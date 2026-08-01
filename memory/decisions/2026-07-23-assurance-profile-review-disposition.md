# Assurance is derived from configured guards and observed evidence

**Status:** decided
**Date:** 2026-07-24
**Decided-by:** human (2026-07-24 review; requested-change response preserved in commit 92bdafa)
**Description:** Repositories configure individual guard bindings; AgentFold derives assurance per obligation and scope from observed coverage, health, and enforcement rather than selectable profile labels
**Review-by:** 2027-02-04
**Amends:** `memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md` — “assurance profiles” as a describable artifact; the four-mode guard surface stands

## Context

The guardrail proposal used “assurance profile” both as a security-claim ceiling and as
language that looked like a selectable feature configuration. During review, the owner
asked whether one feature could enable several profiles, whether token-expensive
feedback could be manual, and whether an agent would simply claim a profile after
installing instructions and tests. The owner also directed that controlled egress stay
reference-only unless a separate proposal receives explicit human approval.

The reviewed proposal remains at
`docs/designs/risk-tiered-agent-guardrails.md`. Its requested revision is owned by
`message-queue/needs-agent/requests/future-blocking-revise-assurance-profile-scope-and-egress.md`.

## Decision

Adopters configure individual guard bindings, not assurance labels. A binding identifies
an obligation, declared content scope, detector, lifecycle trigger or enforcement
boundary, and one `hard`, `soft`, `manual`, or `off` mode. Several bindings may apply
to one change, and the same detector may provide early local feedback and separately
enforced remote evidence.

AgentFold derives a current assurance report for each obligation and declared scope from
content-bound run evidence, detector coverage and health, and independently observed
enforcement configuration. The agent may inventory controls and explain the report, but
cannot strengthen it by writing a label. Reports state surfaces, inputs, skips,
unsupported cases, limitations, and eval evidence; they use no synthetic coverage
percentage unless a real evaluation supports that number.

An uninvoked `manual` guard contributes no current evidence. Once invoked, it contributes
only evidence bound to that exact subject and does not become an always-on gate.
Deterministic tests and broader semantic review remain distinct evidence sources with
different coverage and failure modes.

Controlled egress is not approved implementation scope. It may remain one reference-only
future possibility, but AgentFold adds no controlled-egress configuration, template,
adapter, task, or implementation without a separate proposal and explicit human
approval.

## Alternatives considered

- Let a feature select one or more named profiles — rejected because a label can
  overstate missing coverage or authority and can let an agent appear to downgrade a
  critical obligation.
- Use one repository-wide assurance scalar — rejected because different obligations in
  one change can have different detectors, scopes, and enforcement boundaries.
- Convert detector output into a generic coverage percentage — rejected because test
  counts do not measure unknown contextual misses without a defined evaluation.
- Implement controlled egress as the strongest built-in level — rejected as unnecessary
  scope and contrary to the owner's explicit approval boundary.

## Consequences

The guardrail design and implementation task must use guard bindings, observed
capabilities, and derived per-obligation reports. Named local, merge, and repository
boundaries may describe evidence, but they are not toggles or self-declared achievement.
The exact revised design still requires a revision-bound follow-up review before the
universal guard-mode task may start.
