# Plan — stale-base pull-request admission

- [ ] 1. Reproduce the pull-request event base advancing beneath a recomputed merge candidate.
- [ ] 2. Reuse the existing bounded parent-interrogation boundary in `reconcile-and-test`.
- [ ] 3. Prove recomputed valid candidates pass and unrelated candidates still fail closed.
- [ ] 4. Run the focused workflow suite, full repository suite, reconciler, and core-scope check.
- [ ] 5. Publish, independently review, and merge the repair before landing pull request #79.
