# Plan — protect AgentFold core portability

- [x] 1. Audit the rejected change against AgentFold's existing contracts and record the
      root-cause reasoning in `design.md`.
- [x] 2. Add the core-admission contract and an accepted ADR without embedding a vendor
      or provider-specific implementation.
- [x] 3. Extend the task schema and reconciler with a low-friction portability
      acknowledgement; migrate existing records and add canary tests.
- [x] 4. Run repository checks, explicitly invoke an independent core-fit review, then
      record exact evidence and move the task to review.
- [x] 5. Publish a clean replacement draft PR based on the guardrails-design branch and
      link it from the closed incident-specific draft.
- [x] 6. Confirm the reviewed head and merge commit are ancestors of `main`, then close
      the task lifecycle.
