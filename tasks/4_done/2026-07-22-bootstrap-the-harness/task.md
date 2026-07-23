# Bootstrap the AgentFold harness

**Claimed-by:** claude (bootstrap session)
**Mode:** autonomous
**Filed:** 2026-07-22, by the repo owner (chat request, transcribed here — chat leaves no trace)
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Extract the generalizable agent-harness patterns from a private working project into
this repo: folder-as-a-service structure, message queue, task tracking, history with
handovers, memory with forgetting, roadmap, portable skills, and mechanical enforcement
via a reconciler — as a reusable open-source example, agent-agnostic and free of any
source-project specifics.

## Acceptance criteria

- [x] Every folder in the repo tour exists, named so a stranger can guess its contents
- [x] Every file schema has exactly one home in `templates/` (single source of truth)
- [x] `automation/reconcile/reconcile.py --check` passes on the finished repo
- [x] Example services under `services/` pass their tests
- [x] Real design decisions recorded as ADRs in `memory/decisions/`
- [x] This task itself is tracked with the system it builds (this folder)

## Links

- Handover: `history/conversations/2026-07-22-0014PDT-bootstrap-the-harness/handover.md`
- Design reasoning: `design.md` in this folder; ADRs in `memory/decisions/`
