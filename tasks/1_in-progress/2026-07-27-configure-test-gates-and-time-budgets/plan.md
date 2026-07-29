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
- [x] 8. Add focused regression tests, benchmark representative service, automation, and
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
      across controller startup, and require the then-current v5 receipt/pass-report/v1 marker
      set. Step 16 supersedes that receipt and handoff generation for the absolute-deadline repair.
- [x] 15. Run the explicit final gate for product candidate
      `843a44a38f328ebde40d34f759d8592847175bd4e9d65f27301f5c6d9b710b53`, reuse its
      exact full-test receipt in the normal hook, and commit the product as `3a342013`. Record
      the surviving evidence honestly after the original final report and stdout were lost.
- [x] 16. Integrate the P1 supervisor/worker repair and old/new generation bridge, then run an
      exact final gate for staged candidate `44963ec447ee095dcdedd6fb7eacc903526b2eaddcc6ae54356c670f654a28cb`.
      Preserve its valid ignored full receipt honestly; do not call the later routine failure a
      final-test failure.
- [x] 17. Repair both causes exposed by the real reversible hook: validate an exact latest-final
      full receipt before selected work, and reserve enough of the routine interval for cleanup
      and terminal brokering. Add focused exact-match, mismatch, reversible-prewarm, and selected-
      fallback deadline regressions without weakening full-receipt validation. Seven new focused
      regressions pass, the no-receipt path deferred in 6.608 seconds, the prewarmed exact receipt
      was reused in 5.587 seconds, and an independent rereview approved the repair.
- [ ] 18. The complete repaired candidate passed a new exact final gate as
      `d9d630b39a883946fa8b07e9c444a889a0144cfcf90fd1302385f50b0829c9d1`, and the unchanged
      normal commit hook reused that receipt before creating product commit `d966c19`. Obtain a
      fresh revision-bound panel with no valid blocker. Keep the retry live and merge blocked
      until that review succeeds.
- [x] 19. Repair the next panel's five blockers: narrow reversible path ownership, remove
      repository-local Git identity as a hidden input, retain validated policy facts on static
      timeouts, publish budget-task pairs without overwriting concurrent actors, and replace
      quote-specific test ownership with configured generic service dependencies. Land the
      exact-generation test bridge first and pass the 152-test focused set plus the complete
      104-case gate module.
- [ ] 20. Freeze the repaired staged candidate, run one new exact explicit final gate, commit
      through the normal receipt-reusing hook, and obtain a fresh five-reviewer revision-bound
      panel with no valid blocker before resolving the retry or moving the task to review.
- [x] 21. Repair the three pre-final rereviews: land a trusted parser compatibility floor before
      the nonempty dependency policy, propagate and bind the four safe Git identity variables,
      remove every canonical-path rollback deletion, record only observed static duration, and
      bound static stdout delivery. Land dual-generation test bridges `5397fc5` and `68af0e4`;
      pass exact parser-floor candidate `c122a31f…`; and commit it as `236b90d` through a
      receipt-reusing normal hook.
- [ ] 22. The expanded focused set and exact final gate passed for candidate `677e74a3…`, and the
      normal hook reused its identity-aligned receipt before product commit `962cca3`. Obtain a
      new five-reviewer panel with no valid blocker before resolving the retry, moving the task,
      or publishing the PR stack.
