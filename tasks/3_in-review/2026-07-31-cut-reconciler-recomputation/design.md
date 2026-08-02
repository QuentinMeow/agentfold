# Design notes — Cut the reconciler's repeated recomputation

**Status:** decided

## Problem

After the object-read caching layer, reconciler wall time is still O(commits x repository
size). Profiling at the stack tip shows the remaining cost is not Git object reads but
recomputation of answers the process already had: the same Markdown document is re-parsed
for every admitted Git edge, a single-path index question is answered by filtering the whole
captured index, and one governed edge walk asks Git for the same commit's parents once per
consuming check.

The acceptance bar is behaviour parity, so every change has to be provably answer-preserving
rather than merely plausible.

## Options considered

### Option A — Cache each check's finding list keyed on a content fingerprint
Cache `check_task_structure()`'s output per admitted revision, keyed on a hash of the tree
entries it reads. Attractive because that check is the single largest per-edge cost.
Consequence: the check does not read a bounded path set. `review_boundary_problem` follows a
review item's declared `Review target` to an arbitrary repository path, and
`git_range_review_freshness_problem` consults `committed_candidate_revision()` — the revision
itself, which `git_revision_candidate` rebinds. A fingerprint that misses any of these
silently changes findings, and one wide enough to be sound (the whole tree) never hits,
because every commit has a distinct tree.

### Option B — Memoise the pure functions the recomputation is made of
Markdown semantic blanking, rendered-prose extraction, invisible-character stripping and
task-record action-prose recognition are pure functions of their exact input text. Memoise
them on that text. Consequence: the same document analysed at ten revisions that did not
change it costs one parse, and correctness needs only purity — no reasoning about which
revision is bound.

### Option C — Memoise the governed edge generator itself
Materialise `queue_revision_edges` once and replay the tuple to its six consumers.
Consequence: it removes the same redundant Git work as Option D, but a generator that raises
mid-walk currently lets a consumer stream the findings it already produced; materialising
eagerly moves the failure ahead of those findings. That trades a documented streaming
guarantee (`automation/AGENTS.md`) for speed.

### Option D — Route the edge walk's parent lookup through the existing cached helper
`queue_revision_edges` inlines the very `git rev-list --parents -n 1` that
`revision_parents` already runs and caches. Consequence: one spawn per revision instead of
one per revision per consumer, with the same command, the same shallow/graft semantics, and
the same error text — and the generator stays lazy.

## Chosen

B and D, plus two local reads of the same kind: an exact index question becomes a dictionary
lookup instead of a whole-index scan (`git_index_entry_mode`), and the immutable handover
incarnation is read through the `cat-file --batch` reader that already exists instead of
spawning `git show` per handover.

A is rejected: it cannot be made sound without a fingerprint so wide it never hits, and the
measured win it targeted largely disappears once B removes the parsing underneath it.
C is rejected in favour of D, which captures the same Git cost without weakening streaming.

Parity is proved rather than argued: a differential harness materialises the pre-change
sources into the git-ignored `tmp/` mirror — whose depth makes `REPO` and `AUTOMATION`
resolve to the real repository — and runs both versions against one clean working tree, so
`--range` still sees an unmodified candidate. The finding lists, stderr, and exit codes are
diffed for `--check`, a mid-size range, and `--range root:<head>`.

## Core fit

**Agent substitution:** pass — the change is inside the reconciler and its shared Markdown
helpers; no agent runtime is named, and every runtime that runs the gate gets the same
findings faster.
**Provider substitution:** not-applicable — no provider surface is touched; the caches are
process-local and keyed on repository content.
**Repository substitution:** pass — an adopted repository of any size runs the same checks,
and the cost removed (per-edge re-parsing, per-consumer re-spawning) grows with its history,
so the benefit is largest exactly where the gate hurts most.
**User-global writes:** none
**Why AgentFold core:** the pre-commit gate is core machinery every adopter runs; its wall
time is a property of the harness, not of one person's setup. Nothing here is local config,
product code, or a private overlay.
**Thin adapter:** none
