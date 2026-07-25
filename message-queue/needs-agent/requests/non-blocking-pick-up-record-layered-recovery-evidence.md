# Pick up the layered recovery-evidence task

**Status:** open
**Filed:** 2026-07-24, by codex, from task `2026-07-24-layered-development-workspace`
**Action:** After the manifest/status task is done, claim the recovery-evidence task, create its plan and worklog, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-24-record-layered-recovery-evidence/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-07-24-record-layered-recovery-evidence/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed; no backup or recoverability claim is added and destructive protected-data operations remain outside the tooling.

## What you need to know

Backup is a vector of independently observed facts, not a boolean ladder. This task may
record and evaluate evidence, but it may not perform deletion, restoration over an
origin, replication, or upload.

## Done when

The prerequisite is done, the task has a claimant and has moved to `1_in-progress`,
its plan and worklog exist, and this request and its reciprocal task link are removed.
