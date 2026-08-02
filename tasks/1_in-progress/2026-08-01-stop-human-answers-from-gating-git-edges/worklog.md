# Worklog — Stop a human answer from holding any Git edge

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-01 — human-gating-model (claude)

- Claimed the task and reproduced the deadlock on `main` @ `0e63bbe`: plain
  `--check` is clean, `--check --at-transition merge` reports four boundary
  findings.
- Confirmed the live inventory differs from the design's: the first-class-queue
  review was folded before this task started, and PR #56 added a new merge-bound
  human re-review, so four human items migrate rather than the design's four
  originals.
- Found one instruction in the design that current `main` cannot execute: the
  dangling `Depends on:` on the revised-assurance review is not a lifecycle-mutable
  field, so editing it on a live item changes action identity and is refused.
  Recorded as a known issue instead of forced.
