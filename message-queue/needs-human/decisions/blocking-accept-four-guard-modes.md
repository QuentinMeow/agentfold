# Use the same four modes for every configurable guard

**Status:** waiting
**Blocking:** yes — guardrail implementation must not invent different mode semantics
**Filed:** 2026-07-23, by codex, from the owner's PR #4 response in chat

## What you need to know

The guardrail design gives every configurable check the same behavior vocabulary in
`docs/designs/risk-tiered-agent-guardrails.md`: `hard` runs and blocks on an unsafe or
broken result, `soft` runs and reports without blocking, `off` does not run and makes no
protection claim, and `manual` runs only when explicitly requested.

## Options

### Option A — One universal vocabulary

Every guard uses those four meanings, regardless of detector or agent.
*Example consequence:* a costly reviewer guard set to `manual` never consumes tokens
unless invoked, while the same guard set to `hard` runs at its declared boundary and
blocks on failure.

### Option B — Per-guard meanings

Each guard defines its own mode words and transition effects.
*Example consequence:* `manual` could mean “ask first” for one guard and “run only from
the command line” for another, so configuration cannot be understood uniformly.

## Recommendation

Option A, because a shared vocabulary keeps configuration predictable without fixing a
specific detector or workflow.

**Your answer:** Yes — use the four semantics universally.
