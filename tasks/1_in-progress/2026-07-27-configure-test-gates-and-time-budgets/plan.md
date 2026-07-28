# Plan — configurable test gates and time budgets

- [x] 1. Specify and validate the `agentfold.toml` testing schema, including defaults,
      supported modes and triggers, critical categories, and actionable configuration errors.
- [x] 2. Add a candidate fingerprint, monotonic component timing, machine-readable results,
      and exact-input receipt reuse without adding tracked noise on normal runs.
- [x] 3. Define explicit source-to-test ownership and risk classification; split or extract
      enough pure checks and integration smoke coverage to select a safe routine manifest.
- [x] 4. Implement the routine gate's end-to-end budget, clean timeout handling, reversible
      deferral, and honest selected/deferred coverage report.
- [ ] 5. Implement the complete final lane with manual and final-stage execution, exact receipt
      validation, and non-deferrable critical-scope behavior.
- [x] 6. Implement deterministic budget-regression task and pickup generation, open-task
      deduplication, recurrence links, actor-note preservation, and read-only finding output.
- [ ] 7. Wire pre-commit and CI/provider adapters to the configured lanes without running the
      complete suite twice for the same candidate; document the adopter-facing configuration.
- [ ] 8. Add focused regression tests, benchmark representative service, automation, and
      cross-cutting changes, and record real before/after evidence against both configured
      targets before review.

## Authorized manual-only replan

- [x] 9. Admit the test-only migration floor in `21d5a24`. It accepts the complete known hard
      regime or complete removal and uses a closed authority scan so renamed status writers,
      permissions, tokens, and direct status API calls cannot hide outside known job names.
- [ ] 10. Switch the starter to manual final verification, remove the unsafe publisher, and make
      every automatic/provider-hard invocation fail closed.
- [ ] 11. Label explicit final evidence as cooperative and record the same-interpreter exit
      limitation without making an automatic-enforcement claim.
- [ ] 12. Run the focused regression set and complete a fresh review of the manual-only result;
      leave controlled completion and external publication to the two backlog follow-ups.
