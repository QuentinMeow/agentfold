# Worklog — cache the reconciler's Git object reads

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — claim (claude)

- Claimed and moved to `1_in-progress`; the pickup request is resolved in this commit.
- Measured before planning anything: 102 of one `--check` run's Git spawns are per-path
  `ls-tree`, concentrated in three checks. Counts and times are in `design.md`.
- Scope is the caching only. The unmerged branch
  task/2026-07-26-resolve-queue-items-whose-evidence-already-merged carried both the
  caching and a resolution-evidence rule; the rule is being discarded and is not in this
  task.

## 2026-07-30 — extract the caching from the discarded evidence branch (claude)

- The branch's history made the split clean rather than surgical. `e5bf650 fix: harden
  and batch queue evidence lineage` introduced its `git_object_snapshot`; the rule
  functions and the `--no-replace-objects` sweep are separate later commits. The caching
  was never entangled with the rule — it was only committed alongside it.
- main has moved since that branch forked. `_GIT_TREE_BLOB_ENTRY_CACHE`,
  `scope_immutable_git_caches`, and the reusable blob reader all landed in the meantime,
  so this is an extraction against today's main, not a replay of the branch's diff. The
  new caches join `scope_immutable_git_caches`, which already documents exactly this
  rationale for blobs and ancestry, instead of the branch's per-invocation reset lists —
  that alone removed about 40 lines the branch needed, including its additions to
  `start_git_snapshot_cache`, `stop_git_snapshot_cache`, and `git_revision_candidate`.
- Two things the branch did that this deliberately does not. It read the parent list out
  of raw commit objects, which loses the graft and shallow-boundary view `git rev-list`
  gives; only the `tree` header is read here. And its reader raised on any unreadable
  object, which is what turns a shallow clone into `exit 2` with zero findings; this one
  answers `None` and lets the caller run the `ls-tree` it always ran.
- The branch's port also returned a raw tree's `40000` where `ls-tree` prints `040000`.
  The new equivalence guard fails on exactly that, which is recorded in
  `verification.md` as a mutation check rather than asserted.
- Dead end worth not repeating: the first differential harness compared 43 revisions ×
  210 paths and cleared the reader between calls, which meant tens of thousands of
  `ls-tree` spawns and no result in ten minutes. Twelve revisions and twenty-four path
  shapes cover every distinct case in seconds.
- Reproducing the branch's `exit 2` needed the right shape of input: a staged deletion of
  an unclaimed queue item fails the lifecycle check first and never reaches the evidence
  rule, so both versions agree there. Calling its `complete_creation_parents` directly in
  the shallow clone is what shows the raise.
- Noticed in passing, not this task: `reconcile.py --check` reports findings for files
  under the git-ignored tmp/, so a scratch clone left there produces an `agents-budget`
  finding for a file that is not in the repository.
