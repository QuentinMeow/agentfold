# Design notes — multi-worktree safety remediation

**Status:** decided

## Problem

The repository assumes file-based coordination is safe across independent agents, but the
audit reproduced races in linked-worktree bootstrap, coordination publication, task-branch
restacks, and landing admission. The repair must preserve the repository's canonical task
and queue records while giving each behavior change an independently reviewable boundary.

## Options considered

### Option A — one broad safety pull request

Change the installer, reconciler, Git workflow, and admission mechanism together. This
shortens the branch list but makes intermediate invariants and regressions hard to isolate.

### Option B — serial vertical slices

Ship one complete behavior at a time: linked-worktree bootstrap; displaced-tip provenance;
explicit expected-OID publication; authoritative coordination publication; stale-base
admission; then lifecycle-reference repairs. Each slice carries its task, design, tests,
and safe stopping point.

## Chosen

Use serial vertical slices. Parallel agents may research and test, but implementation that
touches shared reconciler or workflow surfaces is serialized. GitHub issues are projections
only: each points back to one canonical task and a source-bound queue item. Server-side
landing enforcement remains deferred behind the accepted advisory-gate decision.

## Dependency order

1. Linked-worktree bootstrap.
2. Displaced-tip queue provenance.
3. Explicit expected-OID task-branch publishing.
4. Authoritative coordination snapshot and compare-and-swap publication.
5. Stale-base admission, then lifecycle-reference repairs.
6. Required server-side admission only after a superseding owner decision.

## Core fit

**Agent substitution:** pass — the protocol depends on Git and repository records, not a named runtime.
**Provider substitution:** pass — local correctness uses immutable Git object IDs and provider-neutral checks.
**Repository substitution:** pass — any repository using linked worktrees and concurrent agents needs these boundaries.
**User-global writes:** none
**Why AgentFold core:** these mechanisms protect the repository's own coordination and admission invariants.
**Thin adapter:** none
