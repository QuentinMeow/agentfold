# Plan — isolate repository tests from Git hook state

- [x] 1. Preserve the claimed task and root-cause design before the production repair.
- [x] 2. Add and run a focused red regression for Git-local environment contamination.
- [x] 3. Implement the minimal fail-closed child-environment boundary in `automation/run_tests.py`.
- [ ] 4. Run focused, full-suite, reconciler, diff, and linked-worktree state-preservation checks.
- [ ] 5. Record real verification output and hand the exact candidate to independent review.
