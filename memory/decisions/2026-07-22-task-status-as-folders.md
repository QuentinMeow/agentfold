# Task status is the folder the task sits in

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** agent
**Description:** tasks/0_backlog…4_done folders ARE the status; no status field exists to drift
**Review-by:** 2027-01-22

## Context

Task state needs to be glanceable for humans (`ls tasks/1_in-progress/`) and
single-sourced for agents. The source project used numbered status folders *plus* a
per-item status field with a "must agree" rule — two sources of truth needing a
consistency check.

## Decision

Folder location is the **only** status. `git mv` is the state transition; there is no
status field. References use the immutable task id and resolve via `ls tasks/*/<id>`.

## Alternatives considered

- **Frontmatter status + flat folders** (Backlog.md style): stable paths, but status
  requires opening files or maintaining a generated board — one more derived artifact.
- **Folder + mirrored field** (source project): glanceable *and* machine-parseable
  in-file, but the pair drifts and needs its own reconciler check. Rejected for the
  template: the simplest SSOT wins as the teaching example.
- **Single tasks.json** (task-master style): merge-hostile with parallel agents;
  rejected outright.

## Consequences

Links must use task ids, not paths (enforced socially + by the link checker ignoring
`tasks/*/` deep paths). Status transitions are commits, giving a free audit trail of
when each task moved.
