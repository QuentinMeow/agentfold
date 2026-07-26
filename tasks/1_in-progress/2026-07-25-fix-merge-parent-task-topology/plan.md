# Plan — stop reading a merge parent edge as a lifecycle step

- [x] 1. Claim the task, move it to `1_in-progress`, and resolve its pickup request in one
      coordination commit on `main`.
- [x] 2. Record the reproduction of the false finding on the merge range, before any code
      change, in `verification.md`.
- [x] 3. Add a sibling-parent lookup beside `task_record_paths_at` in
      `automation/reconcile/reconcile.py`, built on the existing `candidate_parent_oids`
      helper so the index candidate and a commit candidate resolve the same way.
- [x] 4. Condition only the `if not prior:` creation finding in `task_topology_problems` on
      that lookup, leaving `before`, `after`, the rename set, and every sibling rule
      untouched.
- [x] 5. Add tests in `automation/tests/test_reconcile_queue.py` over real merge commits:
      the cleared false positive, a linear direct-to-`1_in-progress` creation, a merge no
      parent of which carries the task, a `0_backlog` parent advanced to `1_in-progress` by
      the merge, and the `adopting` escape.
- [x] 6. Run each new test against the pre-repair function to record which ones
      discriminate, and note every verdict in `verification.md`.
- [x] 7. Record real output for the merge range, a full `--check`, and the whole test suite
      in `verification.md`.
- [x] 8. Open the pull request with a validated action-projection body.
