# Refactor repository agent instructions

**Claimed-by:** codex
**Filed:** 2026-08-09, by codex, from chat
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Make AgentFold's instruction hierarchy shorter, more local, and easier for agents to
follow without changing repository behavior by accident. The root contract should be a
compact operating map; each nested `AGENTS.md` should own only its subtree's additional
rules; deep procedures and mechanically enforceable invariants should remain in their
canonical documents, skills, templates, hooks, or tests.

## Acceptance criteria

- [ ] The root `AGENTS.md` is materially shorter and routes agents to canonical depth
      without dropping the boot, coordination, safety, or publication obligations needed
      before those deeper files are opened.
- [ ] Every tracked `AGENTS.md` is audited; ancestor restatements and stale routing are
      removed while genuinely local boundaries, commands, and interfaces remain.
- [ ] The chosen compatibility, dependency, and temporary-implementation defaults are
      stated at the narrowest scope that owns them and do not silently overturn an
      existing public interface, immutable record, portability constraint, or decision.
- [ ] Objective rules are linked to their existing mechanical enforcement instead of
      being expanded into duplicate prose.
- [ ] All instruction links resolve, the reconciler passes, and the full test suite passes
      with real output recorded.

## Links

- Related future automation: `message-queue/needs-agent/requests/non-blocking-detect-lexical-restatement-across-contracts.md`
- Current precedence rule: `handbook/principles/folder-as-a-service.md`
