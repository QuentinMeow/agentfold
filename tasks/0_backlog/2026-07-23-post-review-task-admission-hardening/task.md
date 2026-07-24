# Harden first-adoption task admission after human review

**Claimed-by:** unclaimed
**Mode:** async
**Filed:** 2026-07-23, by codex, from the deferred findings of task `2026-07-23-first-class-message-queue`
**Parent:** 2026-07-23-first-class-message-queue
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-post-review-task-admission-hardening.md`

## Goal

Close the deliberately deferred first-adoption and performance gaps in task admission
after the first human review of the first-class message-queue change. Keep the check
filesystem- and Git-based, and do not reinterpret append-only historical records as
live actions.

## Acceptance criteria

- [ ] On initial schema adoption, an unchanged live `task.md`, `plan.md`, or
      `design.md` human action without an exact task-owned queue projection is rejected.
- [ ] Initial adoption treats pre-adoption worklogs and verification output as
      historical evidence, while every later edit remains governed.
- [ ] Task-history admission avoids redundant whole-tree scans or records a measured,
      reviewed reason to retain them.
- [ ] Regression tests cover unchanged activation asks, historical-record
      grandfathering, and a representative long task history.
- [ ] The implementation starts only after the first human review of the parent
      change is recorded.

## Links

- Parent task: `2026-07-23-first-class-message-queue`
- Deferred audit evidence: the parent task's design and worklog
