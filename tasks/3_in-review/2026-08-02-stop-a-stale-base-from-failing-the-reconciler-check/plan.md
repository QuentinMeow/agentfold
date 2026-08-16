# Plan — stale-base pull-request admission

- [x] 1. Reproduce the pull-request event base advancing beneath a recomputed merge candidate.
- [x] 2. Reuse the existing parent-interrogation boundary in `reconcile-and-test`; keep the already immutable checkout retry-free.
- [x] 3. Prove recomputed valid candidates pass and unrelated candidates still fail closed.
- [x] 4. Run the focused workflow suite, full repository suite, reconciler, and core-scope check.
- [ ] 5. Publish, independently review, and merge the repair before landing pull request #79.
