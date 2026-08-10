# Plan — Stop the merge-ref recompute race from failing every stacked pull request

- [x] 1. Claim the task, move it to `1_in-progress`, and resolve its pickup request in one
      pushed coordination commit.
- [x] 2. Record the design: why bare equality against `github.sha` is the wrong binding,
      which of the sibling job's mechanism is reused, and the completed **Core fit** receipt.
- [x] 3. Rewrite the `review-state-action-projection` candidate step so a candidate that
      differs from `github.sha` is admitted only when the fetched merge commit has exactly
      two parents, its second parent is this event's `head.sha`, and its first parent
      contains this event's `base.sha` — the same binding
      `authoritative-external-action-projection` already uses.
- [x] 4. Bound the re-resolution: a fixed attempt count and a fixed delay, both declared in
      the step's `env:` block, with exhaustion failing the job.
- [x] 5. Extend `automation/tests/test_github_action_projection_workflow.py`: a fixture in
      which the merge ref was recomputed onto a moved base passes, and one in which the
      merge ref names a different head still fails.
- [x] 6. Record real output in `verification.md`: the full suite, the reconciler, the new
      tests, and evidence that the genuine-mismatch guard bites rather than an assertion
      that it does.
- [x] 7. Publish: rebase onto `main`, push the branch, open the pull request from
      `templates/pull-request.md`, and append the worklog entry.
