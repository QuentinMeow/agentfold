# Design layered guardrails for critical agent obligations

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-22, by codex, from chat
**Parent:** none

## Goal

Research how AI coding agents should create and evaluate software designs, then design
a filesystem- and git-native harness that makes agents confront important obligations
even when they forget prose instructions. The design must distinguish tolerable drift
from critical failures such as committing PII, compare multiple enforcement approaches,
and preserve freedom for future, more capable agents.

## Acceptance criteria

- [x] The documentation and design folders exist with local contracts appropriate to the
      folder-as-a-service architecture.
- [x] A research-backed design document defines agent-oriented design principles and
      traces material claims to primary or authoritative sources.
- [x] The design explores the choice space breadth-first, compares multiple approaches
      and enforcement times, and recommends a layered architecture with explicit
      trade-offs, failure modes, and escape hatches.
- [x] PII prevention is worked through as a concrete threat model, including imperfect
      detectors and direct agent inspection of inputs and outputs.
- [x] The proposal relies primarily on files, git, hooks, automation, and CI while
      avoiding constraints that would unnecessarily limit smarter future agents.
- [x] Repository checks pass and the completed work has an evidence-backed review.

## Links

- `handbook/principles/systems-over-instructions.md`
- `handbook/principles/folder-as-a-service.md`
- `roadmap/desired-state.md`
