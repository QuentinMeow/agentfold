# Plan — cache the reconciler's Git object reads

- [x] 1. Count the per-path `ls-tree` spawns per check on this repository, so the target
      is measured rather than assumed (`design.md` table).
- [x] 2. Separate the unmerged branch's caching from its resolution-evidence rule; confirm
      commit-by-commit that the caching landed before the rule and can be taken alone.
- [x] 3. Add `read_raw_git_object` plus `parse_raw_git_tree` /
      `parse_raw_git_commit_tree` / `git_tree_entries` / `object_root_tree` /
      `object_path_entry`, with `UNREAD_TREE_ENTRY` as the "ask Git yourself" answer.
- [x] 4. Consult it from `git_tree_blob_entry` and `git_tree_path_entry`, leaving both
      subprocess paths untouched behind the sentinel.
- [x] 5. Prove equivalence differentially: the same calls with the reader on and off over
      every path kind in the repository, recorded in `verification.md`.
- [x] 6. Prove whole-run equivalence and degradation: identical findings with the reader
      forcibly unavailable.
- [x] 7. Prove the shallow-clone failure path: the discarded branch raises, this change
      reports the same findings and the same exit code as main.
- [x] 8. Measure `--check` before and after over several runs and record the spread.
- [x] 9. Full suite and `reconcile.py --check` green, then commit on
      task/2026-07-30-cache-reconciler-git-object-reads.
