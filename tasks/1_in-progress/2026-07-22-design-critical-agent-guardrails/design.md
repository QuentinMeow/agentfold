# Design notes — Design layered guardrails for critical agent obligations

**Status:** exploring

## Problem

Many handbook rules are advisory prose, so an agent can forget them. The harness needs
to make critical obligations unavoidable without turning every preference into a hard
gate, treating an imperfect detector as an oracle, or forcing future agents down one
implementation path.

## Options considered

### Option A — Prose and checklists

Keep obligations in contracts and templates. This preserves flexibility but cannot
reliably defend hard boundaries when the working context is incomplete or compacted.

### Option B — Universal blocking checks

Turn every rule into a pre-commit failure. This is simple and visible, but false
positives, broken checks, and advisory drift can deadlock unrelated work.

### Option C — Risk-tiered, layered evidence gates

Classify obligations by consequence and detectability, then combine deterministic
checks, explicit agent attestations, independent scans, and CI/merge controls. Critical
boundaries fail closed; judgment-heavy or recoverable obligations retain escape hatches
and eventual repair.

## Recommended

Option C is the proposal, not an accepted decision. The durable design is
`docs/designs/risk-tiered-agent-guardrails.md`. It keeps policy, detection, evidence,
and enforcement separate; uses local hooks for feedback and remotely protected checks
for authority; reserves acknowledgement receipts for judgment-heavy cases; and requires
separate approval for confirmed critical findings. It encodes outcomes and evidence,
not an agent's internal procedure, so stronger future agents retain latitude. No agent
should implement the proposed controls as settled architecture until the proposal is
accepted through the repository's normal decision process.
