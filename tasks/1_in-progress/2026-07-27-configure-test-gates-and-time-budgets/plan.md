# Plan — configurable test gates and time budgets

- [x] 1. Specify and validate the `agentfold.toml` testing schema, including defaults,
      supported modes and triggers, critical categories, and actionable configuration errors.
- [x] 2. Add a candidate fingerprint, monotonic component timing, machine-readable results,
      and exact-input receipt reuse without adding tracked noise on normal runs.
- [x] 3. Define explicit source-to-test ownership and risk classification; split or extract
      enough pure checks and integration smoke coverage to select a safe routine manifest.
- [x] 4. Implement the routine gate's end-to-end budget, clean timeout handling, reversible
      deferral, and honest selected/deferred coverage report.
- [ ] 5. Implement the complete final lane for explicit manual execution, exact receipt
      validation, and non-deferrable critical-scope behavior.
- [x] 6. Implement deterministic budget-regression task and pickup generation, open-task
      deduplication, recurrence links, actor-note preservation, and read-only finding output.
- [ ] 7. Wire pre-commit and the credential-free diagnostic to the routine and explicit-manual
      lanes without running the complete suite twice for the same candidate; document the
      adopter-facing configuration.
- [ ] 8. Add focused regression tests, benchmark representative service, automation, and
      cross-cutting changes, and record real before/after evidence against the routine and
      explicit-final targets before review.

## Authorized manual-only replan

- [x] 9. Admit the exact-byte two-snapshot test-only migration floor in `21d5a24`: the complete
      known hard workflow bytes or the complete base-pinned manual workflow bytes, with every
      partial, renamed, appended, or authority-bearing variant rejected.
- [x] 10. Switch the starter to manual final verification, remove the unsafe publisher, and make
      every automatic/provider-hard invocation fail closed.
- [x] 11. Label explicit final evidence as cooperative and record the same-interpreter exit
      limitation without making an automatic-enforcement claim.
- [ ] 12. Run the focused regression set and complete a fresh review of the manual-only result;
      leave controlled completion and external publication to the two backlog follow-ups.
