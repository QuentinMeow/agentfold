# Worklog — Cut the reconciler's repeated recomputation

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-31 — cut-reconciler-recomputation (claude)

- Claimed the task off `task/2026-07-30-clear-the-stuck-queue-items`, the tip of the
  nine-layer stack whose first layer added the persistent `cat-file --batch` reader and the
  commit/tree caches. This task builds on that layer rather than repeating it.
- Measured before changing anything, then profiled at the stack tip to see which hot spots
  survived the object-read caching. All four named hot spots reproduced, but their shares had
  moved: the biggest single cost was not on the list at all. Roughly a fifth of a range run
  was spent re-deriving Markdown semantics for documents the process had already parsed, and
  that recomputation was what made the per-edge task-structure recheck expensive in the first
  place. Memoising the pure text views on their input therefore fixed the largest named hot
  spot as a side effect: `check_task_structure` fell 7.11s -> 2.55s without being restructured.
- First swing at the differential harness swapped the reconciler sources in the worktree. That
  works for `--check` but not for `--range`, which fails closed on "candidate has unstaged
  changes". Rebuilt it to materialise the baseline into the git-ignored `tmp/` mirror instead,
  whose directory depth makes `REPO`/`AUTOMATION` resolve to the real repository — both
  versions then read one clean tree. Worth remembering: any A/B harness for this reconciler has
  to leave the working tree untouched.
- Measured a 2x machine drift directly: the same baseline `--check` took 5.11s early and
  10.51s later with nothing changed. Every ratio in `verification.md` comes from an interleaved
  baseline/current run so the drift cancels; the parity run's own seconds are order-biased and
  are not used as evidence.
- Result: `--check` 2.00x, a 22-commit range 1.91x, a 72-commit range 2.03x, and the whole
  363-commit history 1.75x, with the finding list byte-identical on all four scopes including
  the 55 blocking findings that `root:` reports.
- Left alone deliberately: the `git log -1 --diff-filter=A` per handover (batching it over the
  directory changes Git's history simplification, which can change which commit is called the
  creation commit), and caching `diff-tree`/recursive `ls-tree` output on immutable object IDs
  (about 13% on ranges, nothing on the pre-commit path). Both are written up in
  `verification.md` under "What was skipped, and why".
