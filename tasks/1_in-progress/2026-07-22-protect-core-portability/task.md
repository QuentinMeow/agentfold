# Protect AgentFold core portability

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-22, by codex, from the owner's architecture correction in chat
**Parent:** none
**Repository scope:** core

## Goal

Make the boundary between AgentFold core and personal, agent-specific, provider-specific,
or product-specific tooling explicit and difficult to overlook. Preserve AgentFold's
open-ended, agent-agnostic architecture while forcing every task author to state why a
change belongs in this repository before implementation reaches review.

## Acceptance criteria

- [ ] The replacement branch contains none of the Codex/GitHub authentication artifacts
      from the closed PR and is based directly on the guardrails-design branch.
- [ ] The root contract states both admission tests: a core change is generally useful
      to AgentFold's lifecycle and does not require one agent, provider, user, or product.
- [ ] Every task schema requires an explicit repository-scope classification, a
      repository-fit rationale, agent-support scope, and the deliberately excluded
      external pieces; the reconciler and Git boundary gate reject missing,
      placeholder, or contradictory declarations.
- [ ] Existing task records are migrated, and positive/negative tests exercise the new
      check without relying on vendor keyword bans.
- [ ] An independent core-fit reviewer verifies that the mechanism does not overfit the
      triggering incident or unnecessarily constrain future agents.

## Links

- Root contracts: `AGENTS.md`, `skills/AGENTS.md`, and `automation/AGENTS.md`
- Portability decision: `memory/decisions/2026-07-22-visible-skills-dir-with-symlinks.md`
- Enforcement principle: `handbook/principles/systems-over-instructions.md`
