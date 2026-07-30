# Design notes — spawn fewer Git processes in the reconciler and its fixtures

**Status:** decided

## Problem

The suite spends 92-93% of its wall time inside Git subprocesses, at roughly 33 spawns per
test in the dominant file. The reconciler read one blob per `git show` and re-derived
immutable object facts on every invocation.

## Options considered

### Option A — Make each Git call cheaper

Rejected as already explored elsewhere: a RAM disk measured 9%, fsync tuning 8%, and
batching calls through `sh -c` was measurably slower because the shell is another process.

### Option B — Make fewer Git calls

Two independent levers: reuse a per-test repository skeleton instead of running
`git init` plus two `git config` calls, and read through one long-lived
`git cat-file --batch` process instead of a `git show` per artifact. Chosen.

### Option C — Replace Git with a library

Rejected: `automation/AGENTS.md` requires Python standard library only, so automation runs
on a bare clone.

## Chosen

Option B, both levers, with the measurement designed to attribute them separately. That
attribution mattered: the fixture hoist did not register at file scale even though its
microbenchmark is real, so only the batching lever is claimed as a win.

Caching is safe because every cached key is a full object ID, and what an object ID
contains cannot change. The cache is scoped per repository and never stores failures.

## Core fit

**Agent substitution:** pass — spawn counts and batched Git reads are repository mechanisms with no agent-runtime dependency
**Provider substitution:** pass — the change is local, and it reduces cost in CI as well without needing provider participation
**Repository substitution:** pass — any adopted repository whose checks shell out to Git per artifact pays the same per-process cost
**User-global writes:** none
**Why AgentFold core:** the reconciler is the referee every commit runs, so the cost of its Git access is paid by every adopter on every commit
**Thin adapter:** none
