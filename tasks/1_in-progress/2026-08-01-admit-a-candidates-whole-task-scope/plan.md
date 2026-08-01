# Plan — let a candidate carry more than one task

- [x] 1. Reproduce both halves of the contradiction with real output: the projection
      gate's exit 2 on a live pull-request candidate, and the reciprocity finding that
      forces the cross-task edit which produces it
- [x] 2. Classify all six blocked pull requests by *why* their scope is plural, and
      separate the ones a rule change fixes from the ones whose branch is wrong
- [x] 3. Reproduce the merge-boundary failure locally with the same arguments CI used
- [x] 4. Write the failing tests first: plural scope accepted and projected as a union, a
      task branch absent from its own candidate still refused, an action introduced by the
      range not reported at its boundary, and an escalated rename still reported
- [x] 5. Replace `inferred_changed_task_id` with `inferred_changed_task_ids`, bind the
      whole scope, and make the projection require the union of the scope's queue actions
- [x] 6. Skip actions the change range introduced in `check_active_queue_boundaries`,
      matching on action identity so a timing rename cannot dodge the boundary
- [x] 7. Update `automation/AGENTS.md` — both the adapter rule and the queue-check rule —
      within its 60-line budget, and `handbook/git-workflow.md` alongside it
- [x] 8. Record real verification: the four new tests failing before and passing after,
      the six candidates re-run against the repaired gate, `--check` at 0 findings, and
      the full suite at 11/11
- [x] 9. Add the guard the first attempt was missing: an action carrying a committed human
      response is the boundary's receipt and is never skipped
- [x] 10. File the follow-up request for the three branches the repaired gate still refuses
