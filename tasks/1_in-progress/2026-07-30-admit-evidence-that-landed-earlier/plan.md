# Plan — Let a queue item be resolved by the work that already landed for its task

- [x] 1. Give `resolution_evidence_problem` the item's queue path as its first argument and
      thread it through all six call sites; behaviour unchanged.
- [x] 2. Hoist the `task:<id>` commit-message pattern out of `task_ids_from_change_range`
      into one module constant both readers share.
- [x] 3. Add the admitted-task set: tasks linking this exact queue path at `prior_revision`,
      minus the task ids in the item's own timing boundary; empty for every unreadable or
      unparseable input.
- [x] 4. Add the earlier-evidence predicate: `git log <tips> -- <evidence>`, a `task:<id>`
      token naming an admitted task, and that task past `0_backlog` at that commit. Never
      raises, never yields a finding.
- [x] 5. Read each `task.md` in `task_ids_linking_queue_at` straight from the recursive
      listing's object through the `cat-file --batch` reader.
- [x] 6. Regression tests in `automation/tests/test_reconcile_queue.py`: admit merged-earlier
      with a matching trailer; refuse never-changed, own-boundary task, backlog-at-commit,
      and no trailer.
- [x] 7. Verify: the live acceptance test on both branches, the 14-item table, the four
      laundering escalations, the legitimate positive path, a shallow clone, the subset
      property replayed over history, the full suite, `--check`, and the spawn-count delta.
