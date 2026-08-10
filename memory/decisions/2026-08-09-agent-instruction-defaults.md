# Explicit contracts constrain global engineering defaults

**Status:** decided
**Date:** 2026-08-09
**Decided-by:** human (owner instruction in chat, transcribed before folding)
**Description:** Cross-repository engineering preferences never silently override explicit public contracts, repository dependency boundaries, or bounded migration bridges
**Review-by:** 2027-02-05

## Context

The owner supplied seven general engineering rules and asked for them in personal Codex
guidance while the repository's layered `AGENTS.md` contracts were refactored. Four rules
already aligned with AgentFold. The remaining wording could be read as three absolutes:
delete all backward compatibility, prefer a library despite local dependency constraints,
and reject every implementation intended for later removal.

AgentFold already owns narrower constraints. Published service interfaces and historical
records have explicit compatibility rules; examples and automation run on the Python
standard library; migrations and experiments may be bounded without becoming permanent
architecture. Personal Codex guidance also lives outside this repository under the
existing core-admission boundary.

The owner answered: "Do what you recommend, then create PRs for all local changes."

## Decision

Cross-repository engineering defaults are contract-aware preferences:

- Obsolete internal compatibility code is removed after supported callers and stored data
  have migrated. Speculative aliases, shims, and fallbacks are not added. An explicit
  public or persisted contract remains until a breaking change is authorized.
- Existing dependencies are inspected before custom code or another package is proposed.
  A maintained library is preferred only when the repository permits it and it reduces
  total complexity and risk after supply-chain and operational costs are counted.
- Production architecture is durable at its stated scope. A necessary temporary bridge is
  named, isolated, tested, and given a concrete removal condition; an unnamed stopgap is
  not accepted as architecture.

Personal global guidance carries those reusable defaults. AgentFold records only their
portable interpretation and repository-specific exceptions; it does not track or install
the user-global file.

## Alternatives considered

- Apply the screenshot literally — rejected because a personal preference would conflict
  with explicit consumer, history, and portability promises.
- Treat all three areas as independent conflicts — rejected because dependency selection
  and bounded bridges already align once current constraints are counted; compatibility is
  the only direct contradiction under an absolute reading.
- Omit compatibility guidance — rejected because the resulting silence would not capture
  the owner's chosen balance between cleanup and explicit contracts.

## Consequences

Agents remove stale internal compatibility mechanisms aggressively but do not infer
permission to break a published interface or persisted format. Repository-local dependency
rules remain authoritative. Temporary work is reviewable because its boundary, tests, and
exit are named.

Reversing this policy requires a new decision record and a separate edit to personal
guidance; no repository mechanism writes outside the clone.
