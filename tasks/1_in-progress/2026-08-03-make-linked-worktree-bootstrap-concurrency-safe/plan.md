# Plan — linked-worktree bootstrap concurrency

- [x] 1. Characterize clone-global and worktree-local installer writes with regression tests.
- [x] 2. Separate the two phases without changing successful single-worktree bootstrap behavior.
- [x] 3. Make concurrent clone-global setup serialize or become a correct no-op.
- [x] 4. Verify local adapters point into each linked worktree and real files are preserved.
- [ ] 5. Run focused concurrency probes, the full suite, and independent review.
- [x] 6. Publish the task, design, implementation, and real verification in draft PR #79.
