# Design notes — Refactor repository agent instructions

**Status:** decided

## Problem

The instruction chain is correct but costly to load: the root repeats lifecycle detail
owned by subtree contracts, some leaves restate ancestor rules, and the automation
contract describes implementation internals already encoded in code and tests. The
refactor must reduce that persistent context without weakening queue, task, record,
verification, portability, or publication behavior.

## Options considered

### Option A — Rewrite every contract to a minimal route

Keep only a short purpose statement and links in each file. This saves the most context,
but it would hide local action rules and make safe operation depend on discovering
non-contract documentation.

### Option B — Progressive disclosure with local contracts

Keep startup, routing, and hard invariants at the root; keep current schema markers and
actionable lifecycle rules in their owning subtree; route implementation detail to the
canonical code, templates, tests, skills, and handbook. Remove only proven ancestor
restatements from leaves.

## Chosen

Option B. It follows the existing closest-contract precedence rule and lowers repeated
context without changing an interface or record schema. The owner's contract-aware
compatibility, dependency, and temporary-bridge defaults live in the personal global
Codex contract and the durable decision at
`memory/decisions/2026-08-09-agent-instruction-defaults.md`; AgentFold core retains only
the stricter local promises it actually owns.

## Core fit

**Agent substitution:** pass — the hierarchy is plain Markdown and depends on repository contracts, not one agent runtime
**Provider substitution:** not-applicable — no external provider participates in instruction discovery or enforcement
**Repository substitution:** pass — concise scoped contracts and progressive disclosure apply to unrelated adopted repositories
**User-global writes:** none
**Why AgentFold core:** the tracked change refactors AgentFold's portable repository contract; the separate personal Codex edit is intentionally outside this diff
**Thin adapter:** none
