# Pick up the layered override-lineage task

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After `2026-07-24-declare-layered-workspace-manifest` is done, claim the override-lineage task, create its plan and worklog, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-24-track-layered-override-lineage/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-24-track-layered-override-lineage/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed; same-path lineage and layered admission leases remain unimplemented.

## What you need to know

The design requires three distinct identities for same-path work: admitted public base,
explicit public candidate, and private effective result. It also forbids generic tools
from claiming a layered effective view without a current manifest-bound lease.

## Done when

The prerequisite is done, the task has a claimant and has moved to `1_in-progress`,
its plan and worklog exist, and this request and its reciprocal task link are removed.
