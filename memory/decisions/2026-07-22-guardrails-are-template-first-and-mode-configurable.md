# Guardrails are template-first and mode-configurable

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** human (review response preserved in commit 76d224d)
**Description:** Guardrails ship as templates controlled by one hard, soft, off, or manual mode surface; sandboxing is deferred
**Review-by:** 2027-03-15
**Amended-by:** `memory/decisions/2026-07-23-assurance-profile-review-disposition.md` (assurance profiles as a thing documentation can describe)

## Context

The proposed risk-tiered guardrail design compared local checks, acknowledgements,
independent-agent review, provider enforcement, and capability sandboxing. During human
review, the owner approved the direction but rejected an always-on bundle: sandboxing is
not needed now, proposed mechanisms should be available as templates, and expensive
agent review must not consume tokens on every change. The revised proposal lives in
`docs/designs/risk-tiered-agent-guardrails.md`.

## Decision

AgentFold guardrail mechanisms are template-first. Adoption does not silently activate
them. One versioned configuration surface assigns every guard one of four modes:

- `hard`: run automatically at the declared trigger and block the transition on a
  finding, incomplete coverage, or error;
- `soft`: run automatically and report without blocking;
- `off`: do not run and contribute no assurance claim; or
- `manual`: run only when explicitly invoked and do not become an always-on gate.

Independent-agent review is `manual` in the starter template because it is
token-expensive. A repository may opt into another mode. Mode changes remain visible
policy changes, and a disabled/manual critical guard lowers the deployment's honest
assurance claim rather than masquerading as clean. Separately controlled provider rules
can remain mandatory regardless of repository-local mode.

Capability sandboxing is deferred. Adding it requires a separate future design; it is
not part of the initial implementation sequence.

## Alternatives considered

- Enable every proposed layer by default — rejected because routine work would pay the
  cost of high-risk controls and agents would habituate to repeated review.
- Give each guard custom enablement semantics — rejected because inconsistent switches
  are hard to discover, audit, and compose.
- Remove expensive mechanisms entirely — rejected because manual or repository-selected
  use preserves them for genuinely high-consequence work.
- Include sandboxing now — rejected by the owner as unnecessary for the current phase.

## Consequences

Future guardrail templates and runners share the four-mode vocabulary and report
disabled/manual state explicitly. Documentation and assurance profiles describe only
observed active controls. Implementations remain replaceable, while adopters can choose
friction and token cost without editing guard code.
