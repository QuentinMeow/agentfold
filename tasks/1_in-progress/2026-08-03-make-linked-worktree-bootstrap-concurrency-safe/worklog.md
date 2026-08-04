# Worklog — linked-worktree bootstrap concurrency

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-03 — claim-and-implement (codex / sol-high implementer)

- Claimed the task from planning PR #73 on an isolated linked-worktree branch.
- Ran the existing installer once in the new worktree; it reported hooks configured and
  twelve local adapter shims created.
- Assigned implementation and verification to a Sol high worker; the planner retains
  publication and scope decisions.

## 2026-08-03 — concurrency-safe bootstrap implementation (codex / sol-high implementer)

- Split bootstrap into a common-repository hook phase and a checkout-local adapter phase.
  A correct shared hook setting is now read-only; a temporary Git config lock is retried,
  and success is reported only after the required value is observed.
- Made identical local symlink races converge and changed a preserved real adapter path
  from warning-plus-exit-0 to one actionable error summary plus exit 1. The task design
  records why worktree readiness must fail closed and how cheaply that choice reverses.
- Added real Git coverage that creates six linked worktrees with one common Git directory
  and six distinct local Git directories, runs their fresh bootstraps concurrently, then
  runs twelve concurrent repeated bootstraps in one worktree and validates every link.
- Added deterministic coverage for a held `config.lock`, no-write behavior when the shared
  config is correct, and byte preservation for a real `CLAUDE.md` collision.
- An independent Sol xhigh review initially blocked publication on an effective worktree
  override, a stale-link unlink race, and Windows directory-link metadata. The repaired
  patch converges the effective override, never unlinks a stale adapter, and supplies the
  correct target type; the re-review approved the content with no remaining P1/P2 finding.
- An independent Terra worker reran all eight focused tests, the reconciler, and
  `git diff --check`; every check passed without editing the worktree.
- Verified the final bytes with five focused installer tests, all 67 test-runner tests
  (one explicit opt-in skip), all 16 repository test files, an actual worktree rerun, and
  the reconciler with zero blocking findings. Independent review and publication remain
  with the planner.
- Repaired three blockers from adversarial review: effective hooks are now corrected in
  a masking worktree config, stale symlinks are preserved without an unsafe unlink, and
  Windows receives directory metadata for skill links only. Added deterministic tests for
  each finding before rerunning verification.
- The final focused run passed all eight installer tests, the ownership lane passed all
  67 tests with its one explicit opt-in skip, the full suite passed all 16 test files, and
  the reconciler again reported zero blocking findings.
