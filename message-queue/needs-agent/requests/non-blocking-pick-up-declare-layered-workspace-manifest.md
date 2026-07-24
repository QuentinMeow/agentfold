# Pick up the layered workspace manifest and status task

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** Claim the manifest/status task after the parent task is done, create its plan and worklog, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-24-declare-layered-workspace-manifest/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-24-declare-layered-workspace-manifest/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed; the topology inspector continues to make only its bounded read-only claims.

## What you need to know

The parent design intentionally separates declared storage topology from content,
capability, backup, scan, and publication evidence. This task adds a private manifest
and status surface without broadening those claims.

## Done when

The task has a claimant, has moved to `1_in-progress`, has a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed.
