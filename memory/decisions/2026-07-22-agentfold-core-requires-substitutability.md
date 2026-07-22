# AgentFold core requires generality, portability, and repository-local state

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** human (the owner corrected an agent-specific core proposal in chat)
**Description:** Core must survive agent, provider, and adopted-repository substitution; personal setup and user-global writes stay external
**Review-by:** 2027-01-22

## Context

A proposed canonical skill combined a provider-specific operational diagnostic with an
installer for one agent's user-global configuration. The diagnostic could be invoked by
multiple agents, but that did not make the use case a general AgentFold lifecycle
capability. The owner rejected the proposal and clarified that AgentFold is for all
agents and repositories, not one local setup or service.

## Decision

A tracked core mechanism must be both generally applicable to AgentFold and portable.
It must remain valid when the agent runtime, external provider, and adopted product
repository are each substituted. Tracked core executables do not configure user-global
state.

Agent/provider adapters may be tracked only as thin, optional, policy-free forwarders to
a canonical repository behavior, and may write only inside the clone. Personal setup,
single-provider operations, and product-specific workflows belong in local configuration,
a private overlay, a separate plugin/repository, or an appropriate product service—not
in AgentFold core.

## Alternatives considered

- Treat cross-agent executability as sufficient — rejected because a portable tool can
  still solve only one provider or user's operating problem.
- Ban vendor names in core — rejected as stale, evadable, and hostile to legitimate
  design discussion and thin adapters.
- Check in a full adapter framework — rejected until a general interface is justified by
  more than one concrete implementation.
- Require human approval for every core edit — rejected as unnecessarily restrictive;
  structured evidence plus independent review preserves autonomous progress.

## Consequences

Core-changing tasks carry explicit substitution evidence and an independent core-fit
verdict. Git automation rejects missing evidence and obvious user-global access, but it
does not dictate an agent's implementation sequence. A personal integration can still
be durable; its durable home is simply outside this repository.
