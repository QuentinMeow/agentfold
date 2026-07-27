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
