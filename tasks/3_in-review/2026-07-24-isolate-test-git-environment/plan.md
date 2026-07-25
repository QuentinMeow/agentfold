# Plan — isolate repository tests from Git hook state

- [x] 1. Preserve the claimed task and root-cause design before the production repair.
- [x] 2. Add and run a focused red regression for Git-local environment contamination.
- [x] 3. Implement the minimal fail-closed child-environment boundary in `automation/run_tests.py`.
- [x] 4. Run focused, full-suite, reconciler, diff, and linked-worktree state-preservation checks.
- [x] 5. Repair the panel's discovery, quarantine, ambient working-directory, and probe-coverage blockers.
- [x] 6. Re-run focused/full tests and the stronger probe on a new immutable candidate.
- [x] 7. Record real verification and obtain a fresh independent panel majority.
- [x] 8. Rebuild PR #8 on latest main and repair projected-path, Git-config,
      identity, ignored-test, and copy-amplification findings.
- [ ] 9. Bind the final main-based range for human merge review and publish it.
