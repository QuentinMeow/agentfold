# Worklog — Let a queue item resolve when its resolution evidence landed in an earlier commit

## 2026-07-26 — claim-merged-evidence (codex)

- Claimed the task, moved it from backlog to `1_in-progress`, and removed its completed task-pickup request atomically.
- Recorded the converged implementation constraints in `plan.md`: the repair applies only to ordinary `needs-agent` requests; compares every resolution-evidence path against the unique current-incarnation creation snapshot; requires final readable surviving bytes to differ; retains the independent status-only claim; and preserves human, retry, pickup, and custom behavior.
- The task wording’s earlier `at or after claim edge` criterion is contradictory to the creation-snapshot baseline. The reviewed task branch will amend it openly to the intended post-creation criterion; this direct-main coordination commit intentionally does not alter substantive acceptance criteria.

## 2026-07-26 — implement-merged-evidence (codex)

- Limited historical evidence widening to ordinary agent requests. The implementation finds a unique current-incarnation creation root over the complete DAG, follows exact and unambiguous disappearing-path predecessors on every merge parent, detects shallow boundaries, and fails closed on ambiguous roots or Git reads.
- Required every declared evidence path to use a closed repository-local grammar and retain bytes different from its creation baseline at both the deletion event and final admission candidate. Captured staged index bytes, not working-tree bytes, are authoritative.
- Kept the status-only claim check separate and left human folding, reviews, retries, pickups, and custom leaves on their prior control paths.
- Adversarial preflight found and drove regressions for merge rename baseline reset, mixed exact/renamed merge parents, mixed malformed evidence, shallow history, index/worktree disagreement, deletion-then-revert laundering, and a post-deletion change that could otherwise retroactively justify cleanup.
- Corrected the task's claim-edge wording to the chosen post-creation rule and documented its byte-level false-positive/false-negative limits in `design.md`.
- The focused 19-test matrix passed, followed by all 315 queue reconciler tests in 148.879 seconds.
- Deleted the live resolved handover-projection request and changed only its reciprocal task's `Queue actions` field to `none`; final staged admission and full-suite evidence follow in `verification.md`.

## 2026-07-26 — repair-review-blockers (codex)

- The first independent panel blocked the implementation on three issues: an exact synthetic
  merge candidate could restore creation bytes without being checked; raw commit parsing
  decoded/scanned beyond the header block and the legacy diagnostic phrase had drifted; and
  the creation walk launched several Git processes per intervening commit.
- Added the actual captured candidate to the surviving-evidence proof and restored the
  `resolution evidence was not created or changed` diagnostic contract.
- Replaced per-commit process launches with one cached parent graph and one persistent batch
  object reader. Commit headers, trees, blobs, paths, and queue-subtree boundaries are parsed
  or cached invocation-locally; raw/effective parent disagreement detects shallow history;
  both 40- and 64-character object IDs are accepted.
- Added exact synthetic-merge, raw non-UTF-8 commit-body, malformed-header, and deterministic
  300-unrelated-commit regressions. The performance regression proves one bulk parent query,
  one batch object reader, no per-revision history/tree/show process, and no additional process
  calls on a repeated lookup.
- The first full queue run exposed that existing task-admission checks also pass a raw empty
  tree object to historical artifact reads. Generalized the cached path reader to accept a
  validated commit or tree root; the affected 13-test subset and the final 320-test queue suite
  then passed.
