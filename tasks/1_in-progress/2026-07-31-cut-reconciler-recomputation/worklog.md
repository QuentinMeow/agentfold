# Worklog — Cut the reconciler's repeated recomputation

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-31 — cut-reconciler-recomputation (claude)

- Claimed the task off `task/2026-07-30-clear-the-stuck-queue-items`, the tip of the
  nine-layer stack whose first layer added the persistent `cat-file --batch` reader and the
  commit/tree caches. This task builds on that layer rather than repeating it.
- Measured before changing anything, then profiled at the stack tip to see which hot spots
  survived the object-read caching.
