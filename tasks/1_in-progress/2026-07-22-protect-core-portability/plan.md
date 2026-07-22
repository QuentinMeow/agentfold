# Plan — protect AgentFold core portability

- [ ] 1. Audit the rejected change against AgentFold's existing contracts and record the
      root-cause reasoning in `design.md`.
- [ ] 2. Add the core-admission contract and an accepted ADR without embedding a vendor
      or provider-specific implementation.
- [ ] 3. Extend the task schema and reconciler with a low-friction portability
      acknowledgement; migrate existing records and add canary tests.
- [ ] 4. Run repository checks and an independent core-fit review, then record exact
      evidence and move the task to review.
- [ ] 5. Publish a clean replacement draft PR based on the guardrails-design branch and
      link it from the closed incident-specific draft.
