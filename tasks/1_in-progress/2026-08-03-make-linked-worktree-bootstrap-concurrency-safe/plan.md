# Plan — linked-worktree bootstrap concurrency

- [ ] 1. Characterize clone-global and worktree-local installer writes with regression tests.
- [ ] 2. Separate the two phases without changing single-worktree bootstrap behavior.
- [ ] 3. Make concurrent clone-global setup serialize or become a correct no-op.
- [ ] 4. Verify local adapters point into each linked worktree and real files are preserved.
- [ ] 5. Run focused concurrency probes, the full suite, and independent review.
- [ ] 6. Publish the task, design, implementation, and real verification in a draft PR.
