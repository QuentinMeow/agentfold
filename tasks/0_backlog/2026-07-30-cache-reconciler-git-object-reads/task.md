# Answer the reconciler's per-path tree questions from cached Git objects

**Claimed-by:** unclaimed
**Filed:** 2026-07-30, by claude, from chat
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-cache-reconciler-git-object-reads.md`

## Goal

`automation/reconcile/reconcile.py` asks Git for one tree entry at a time. Every
`git_tree_blob_entry` and `git_tree_path_entry` call spawns
`git --no-replace-objects ls-tree -z <revision> -- <path>`, and a `--check` run over
this repository spawns 102 of them: 25 inside `queue-resolution`, 18 inside
`task-admission`, 59 inside `handover-queue-projection`. The same few commit and tree
objects are re-read for every path, even though what a full object ID contains cannot
change while the repository does not.

One persistent `cat-file --batch` reader plus a cache of parsed trees answers all of
those questions without a process per path. This is a pure performance change: the
answers, the findings, and the exit codes stay exactly what they were.

## Acceptance criteria

- [ ] WHEN a check asks for a path's tree entry at an immutable revision, THE SYSTEM
      SHALL answer it from cached raw Git objects instead of spawning `ls-tree`.
- [ ] THE SYSTEM SHALL report the same findings, in the same order, with the same exit
      code as the per-path reads — including for a directory path, an absent path, a
      path under a blob, the empty tree, and a revision that is not an object ID.
- [ ] WHEN the object reader cannot answer — a missing object in a shallow clone, a
      reader that will not start, a frame Git did not finish — THE SYSTEM SHALL fall
      back to the Git query it would have run anyway, and SHALL NOT convert a
      reportable repository state into a `GitSnapshotError` that exits 2 with no
      findings.
- [ ] `reconcile.py --check` and the full test suite SHALL pass unchanged.

## Links

- Discarded branch task/2026-07-26-resolve-queue-items-whose-evidence-already-merged,
  whose caching this extracts and whose resolution-evidence rule it does not
- Task `2026-07-30-batch-action-projection-git-reads`, the same read-once change in
  `automation/check_action_projection.py`
