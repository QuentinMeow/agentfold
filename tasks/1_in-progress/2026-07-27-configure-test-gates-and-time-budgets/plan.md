# Plan — configurable test gates and time budgets

- [x] 1. Specify and validate the `agentfold.toml` testing schema, including defaults,
      supported modes and triggers, critical categories, and actionable configuration errors.
- [x] 2. Add a candidate fingerprint, a POSIX cross-process monotonic invocation clock,
      machine-readable gate and command outcomes, and exact-input receipt reuse without adding
      tracked noise on normal runs.
- [x] 3. Define explicit source-to-test ownership and risk classification; split or extract
      enough pure checks and integration smoke coverage to select a safe routine manifest.
- [x] 4. Implement the routine gate's invocation-to-terminal-freeze decision budget, clean
      timeout handling, reversible deferral, and honest selected/deferred coverage report.
- [x] 5. Implement the complete final lane for explicit manual execution, exact receipt
      validation, and non-deferrable critical-scope behavior.
- [x] 6. Implement deterministic budget-regression task and pickup generation, open-task
      deduplication, recurrence links, actor-note preservation, and read-only finding output.
- [x] 7. Wire pre-commit and the credential-free diagnostic to the routine and explicit-manual
      lanes without running the complete suite twice for the same candidate; document the
      adopter-facing configuration.
- [ ] 8. Add focused regression tests, benchmark representative service, automation, and
      cross-cutting changes, and record real before/after evidence against the routine and
      explicit-final targets before review.

## Authorized manual-only replan

- [x] 9. Land test-only migration bridges before each incompatible production change. Each
      bridge accepts only the exact old and new repository states and rejects mixed or altered
      states, so both sides can be tested safely during the two-commit transition. The cleanup
      bridges are `c78a8d6` and `7d580d3`; the contract bridge is `fcc8d8d`.
- [x] 10. Switch the starter to manual final verification, remove the unsafe publisher, and make
      every automatic/provider-hard invocation fail closed.
- [x] 11. Label explicit final evidence as cooperative and record the same-interpreter exit
      limitation without making an automatic-enforcement claim.
- [ ] 12. Run the focused regression set and complete a fresh review of the manual-only result;
      leave controlled completion and external publication to the two backlog follow-ups.
- [x] 13. Repair the unanimous panel's six blockers: reject reserved authority before imports,
      execute one immutable closure with disposable component indexes, restore non-enforcing PR
      admission diagnostics, freeze terminal publication, include candidate-only namespaces,
      and retire obsolete human asks. Complete the three follow-up focused repair reviews.
- [x] 14. Narrow runtime support to CPython 3.7+ on POSIX, carry the bootstrap monotonic source
      across controller startup, and require the v5 receipt/pass-report/v1 commit-marker set for
      reuse while keeping publication failure separate from the immutable gate decision.
- [ ] 15. Run a fresh exact final/full verification for the repaired production candidate,
      commit it, and obtain a new revision-bound merge review before moving the task to done.
