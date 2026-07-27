# Worklog — Let a queue item resolve when its resolution evidence landed in an earlier commit

## 2026-07-26 — claim-merged-evidence (codex)

- Claimed the task, moved it from backlog to `1_in-progress`, and removed its completed task-pickup request atomically.
- Recorded the converged implementation constraints in `plan.md`: the repair applies only to ordinary `needs-agent` requests; compares every resolution-evidence path against the unique current-incarnation creation snapshot; requires final readable surviving bytes to differ; retains the independent status-only claim; and preserves human, retry, pickup, and custom behavior.
- The task wording’s earlier `at or after claim edge` criterion is contradictory to the creation-snapshot baseline. The reviewed task branch will amend it openly to the intended post-creation criterion; this direct-main coordination commit intentionally does not alter substantive acceptance criteria.
