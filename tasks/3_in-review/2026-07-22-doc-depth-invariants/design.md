# Design notes — Codify queue-message disposability and README depth rules

**Status:** decided

## Problem

Where should each of the two chat-given rules live, given that
`handbook/principles/` files are near-immutable (changing one needs a human-approved
decision), and should the README depth rule get mechanical enforcement?

## Options considered

### Option A — amend `handbook/principles/files-as-messages.md`
The projection idea is arguably part of the principle. But principles are
near-immutable, so this path needs a `message-queue/needs-human/decisions/` round-trip for what is a
clarification, not a reversal.

### Option B — leaf contracts + operating docs (chosen)
State the projection rule in `message-queue/AGENTS.md` (the queue's own contract) and
the writing-side guidance in `handbook/decision-guide.md` (freely improvable operating
doc). No principle changes.

### On a `references/` folder for README depth
Rejected: `handbook/` already is the named-by-purpose references home, and
`handbook/naming-conventions.md` bans generic buckets like a catch-all `docs/`.
Adding `references/` would create a second home for the same facts.

## Chosen

Option B, plus a mechanical half: a root-README line budget in `reconcile.py`
(`agents-budget` check, 140 lines — same ceiling as the root `AGENTS.md`), because the
repo's own principle is systems over instructions. The human directed both rules in
chat, so this is a delegated two-way door; ADRs record it (see
`memory/decisions/2026-07-22-queue-items-are-regenerable-projections.md` and
`memory/decisions/2026-07-22-root-readme-line-budget.md`).
