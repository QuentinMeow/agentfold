# Design notes — cache the reconciler's Git object reads

**Status:** decided

## Problem

The reconciler already reads blobs through one reusable `git cat-file --batch` process,
but it still finds each blob by spawning `git --no-replace-objects ls-tree -z <revision>
-- <path>`. Measured on this repository with every cache cold, one `--check` run spawns
102 of those, and they are the only Git processes three checks pay per path:

| Check | `ls-tree -z <oid> -- <path>` spawns | check time |
|---|---|---|
| `handover-queue-projection` | 59 | 15.40s |
| `queue-resolution` | 25 | 1.07s |
| `task-admission` | 18 | 0.81s |

The questions are redundant: the walk from a commit to `message-queue/needs-agent/
requests/<item>.md` re-reads the same root tree and the same three subtrees for every
item, at every revision in a lineage.

An unmerged branch, task/2026-07-26-resolve-queue-items-whose-evidence-already-merged,
already batched these reads. Its resolution-evidence rule was found harmful and is being
discarded; its caching is not, and this task extracts only the caching.

## Options considered

### Option A — memoise `ls-tree` answers per `(revision, path)`
Already present, and already insufficient: `_GIT_TREE_PATH_ENTRY_CACHE` and
`_GIT_TREE_BLOB_ENTRY_CACHE` remove only *repeated* questions about the same path. Every
distinct path still costs a process, and distinct paths are what these checks have.

### Option B — take the unmerged branch's version whole
Its `git_object_snapshot` raises `GitSnapshotError` on any object it cannot read, and its
rule then reads raw commit parents. In a shallow clone that combination raises out of
every check into `main()`, which prints one line and returns 2 with **zero** findings —
so a shallow clone reports a clean repository as an error, silences every other check,
and blocks every commit through the hook's `set -e`. Reproduced below.

### Option C — a fallible reader that can only make an existing answer cheaper
Read commits and trees through a second persistent `cat-file --batch`, cache the parsed
trees by object ID, and answer `UNREAD_TREE_ENTRY` for anything the reader cannot supply.
Callers keep their `ls-tree` query verbatim and run it on that sentinel, so the cache is
a fast path in front of unchanged code rather than a replacement for it.

## Chosen

Option C.

`object_path_entry(revision, path)` walks the path from a revision's root tree using
`git_tree_entries`, both backed by object-ID-keyed caches that `scope_immutable_git_caches`
already governs — the same rationale that file documents for blobs and ancestry applies
unchanged to trees. `git_tree_blob_entry` and `git_tree_path_entry` consult it first and
otherwise run exactly the subprocess they ran before.

Three details carry the equivalence:

- **`ls-tree` prints a mode a raw tree does not store.** A tree object records `40000`
  for a directory; `ls-tree` prints `040000`, and prints a `kind` column the tree only
  implies. The entry is normalised to `mode.zfill(6)` with `LS_TREE_KINDS` supplying
  `tree` for `40000`/`040000` and `commit` for a `160000` gitlink, so every existing
  comparison against `("100644", "blob")` and every entry-to-entry equality keeps its
  meaning.
- **`ls-tree` cannot descend through a non-tree.** Asking for a path whose first
  component is a blob or a gitlink returns nothing; the walk returns absent for the same
  case rather than guessing.
- **Parents still come from `git rev-list`.** The branch read the parent list out of the
  raw commit object. `revision_parents` deliberately does not: `rev-list` honours grafts
  and a shallow clone's boundary, and a raw commit object does not. `parse_raw_git_commit
  _tree` therefore reads the `tree` header and nothing else, and no caller gains a new
  view of history. This is the single line separating this change from the discarded
  rule, and the next PR in that stack must not erase it casually.

Failure is never fatal. `read_raw_git_object` answers `None` for a missing object, a
reader that will not start, a short frame, or a broken pipe, and permanently disables
itself for anything that leaves the stream unusable — after which every call is a plain
`ls-tree` again. The reconciler cannot end up worse than it started: at worst it is as
slow as it was, and its error text stays the one Git already produced.

## Core fit

**Agent substitution:** pass — the change is inside a stdlib Python checker with no
agent runtime, prompt, or model surface; any agent that could run the reconciler before
runs the same reconciler with the same findings.
**Provider substitution:** pass — no provider name, API, or payload is read; the altered
code only asks Git about the repository it was already asking about.
**Repository substitution:** pass — the per-path spawn count grows with an adopted
repository's queue items, handovers, and task history, so every adopter pays this cost on
every commit through the pre-commit hook.
**User-global writes:** none
**Why AgentFold core:** the reconciler is the referee every commit passes through, and
this changes how that referee reads the repository — not any local setup, product
service, or private overlay.
**Thin adapter:** none

## What this does not do

It does not take the branch's `queue_action_creation_roots`,
`ordinary_request_resolution_evidence_problem`, `complete_creation_parents`,
`linear_queue_history_boundary`, `bulk_revision_parent_map`, or
`matching_disappearing_lineage_paths`. Those are the resolution-evidence rule, they change
which deletions are admitted, and they are not in this task.

It does not take the branch's `--no-replace-objects` sweep across `git show`, `git diff`,
`git log`, and `git merge-base` either. That is a real boundary fix, but it is a
behavioural one and belongs in its own change. The new reader passes
`--no-replace-objects` only because the `ls-tree` queries it replaces already did; the
existing blob reader keeps its existing flags and its existing semantics.

It does not finish `handover-queue-projection`. That check drops from 15.40s to 11.06s
and is still the run's single largest cost: 49 `git log -1` spawns and its own text work
remain, and neither is a tree lookup.
