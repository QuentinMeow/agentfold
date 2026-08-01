# Plan — let a candidate carry more than one task

- [ ] 1. Reproduce both halves of the contradiction with real output: the projection
      gate's exit 2 on a live pull-request candidate, and the reciprocity finding that
      forces the cross-task edit which produces it
- [ ] 2. Classify all six blocked pull requests by *why* their scope is plural, and
      separate the ones a rule change fixes from the ones whose branch is wrong
- [ ] 3. Reproduce the merge-boundary failure locally with the same arguments CI used
- [ ] 4. Write the failing tests first: plural scope accepted and projected as a union, a
      task branch absent from its own candidate still refused, an action introduced by the
      range not reported at its boundary, and an escalated rename still reported
- [ ] 5. Replace `inferred_changed_task_id` with `inferred_changed_task_ids`, bind the
      whole scope, and make the projection require the union of the scope's queue actions
- [ ] 6. Skip actions the change range introduced in `check_active_queue_boundaries`,
      matching on action identity so a timing rename cannot dodge the boundary
- [ ] 7. Update `automation/AGENTS.md` — both the adapter rule and the queue-check rule —
      within its 60-line budget
- [ ] 8. Record real verification: the four new tests failing before and passing after,
      the six candidates re-run against the repaired gate, `--check` at 0 findings, and
      the full suite at 11/11
