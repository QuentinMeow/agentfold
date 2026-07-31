# Plan — let a human answer in one edit

- [ ] Reproduce all three defects against the real repository and record the exact output
- [ ] Move the review terminal binding from the human's commit to the agent's `folding`
      claim: relax `check_queue_schema` at `waiting`, require it at `folding`
- [ ] Add the one-time, write-once binding edge to `queue_mutation_problem`,
      `queue_parent_state_regression_problem`, and `claimed_lifecycle_problem`
- [ ] Treat a placeholder `Review outcome` as `pending` everywhere it is read
- [ ] Exempt `Your answer` / `Your review` field lines from `link-check`
- [ ] Rewrite every `templates/queue/` file so a copy-and-fill produces a valid item:
      real field lines for the default delivery class, escalation guidance visible
- [ ] Document the schema-marker fields that code requires but no template shows
- [ ] Add regression tests for all three defects, including a per-template copy-and-fill
      test that iterates `templates/queue/`
- [ ] Update `AGENTS.md`, `message-queue/AGENTS.md`, and the two handbook guides to
      describe the one-edit workflow
- [ ] Record the design, the enforceable/unenforceable boundary, and the aggressive
      alternative in `design.md`
- [ ] Run the full suite and `--check`; record real output in `verification.md`
