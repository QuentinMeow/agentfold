# Design notes — in-process fixture Git objects

**Status:** decided

## Problem

The repository tests build fixture history with `git add` and `git commit` purely so
they can read it back. The suite is bound by process creation rather than computation,
and those two commands are its largest remaining source of spawns. Removing them means
writing loose objects from Python, which raises one hard question: how much of Git's
own bookkeeping the fixtures still need, since the index is not part of the object
store and real Git commands keep running against the same repositories afterwards.

## Options considered

### Option A — Replace only the commit
Keep real `git add` so Git owns the index, and write only the tree and commit objects.
*Example consequence:* half the win. The census counted 647 `add` spawns against 526
`commit` spawns in this file, so leaving `add` alone leaves the larger half behind.

### Option B — Write objects and the index in process
Write blobs, trees and commits, and read and rewrite a version 2 index with real stat
data, exactly as Git writes it.
*Example consequence:* `git checkout`, `git merge` and `git rm` keep working between
in-process commits, and so does the reconciler, which reads the index itself through
`git ls-files --stage`, `git diff-index` and `git diff-files`.

### Option C — Cache whole built repositories and copy them
Build each shape of history once and copy the directory per test.
*Example consequence:* the tests build several hundred distinct shapes, so the cache
key is the history itself; the copying would not amortize.

## Chosen

Option B. Option A was rejected because the index is not optional here: the reconciler
under test reads it, and one test stages an intent-to-add entry precisely to exercise
that reading. Once the index has to be correct anyway, writing it is a hundred lines
and removes both spawns instead of one.

## Index semantics

The writer keeps a real index rather than leaving the fixtures index-free. Without one,
`git status` and `git add` would see a fully committed worktree as untracked, real
`git checkout` would refuse to replace files it does not know it tracks, `git merge`
would have nothing to merge into, and the reconciler's own index queries would report a
repository that does not match its own head. So `stage` reads the index, hashes the
worktree paths under the pathspec, records the same truncated stat data Git records,
and rewrites a version 2 index; `commit` builds the trees from that index. Reading
accepts index versions 2 and 3 and refuses version 4, whose prefix-compressed names
this writer does not decode.

## What stays on real Git

The writer serves `add` and `commit` only, and declines rather than guessing:

- Any other subcommand, including every `checkout`, `merge`, `rm`, `branch`, `tag`,
  `commit-tree` and `write-tree` the fixtures run.
- `git add -N`, and any other flag beyond a bare pathspec or `-A`: intent-to-add is an
  index state one test deliberately creates and reads back.
- A worktree carrying ignore rules, because the writer does not interpret them. One
  test writes such a file, and its `add` falls through to real Git untouched.
- Repositories whose object format is not SHA-1. `automation/tests/test_check_core_scope.py`
  creates a SHA-256 repository, which hashes objects with a different algorithm; that
  file is untouched by this task and keeps using real Git throughout.

`automation/tests/test_reconcile_queue.py` guards the substitution by building one
history twice, once through real `git add` and `git commit` with a pinned identity and
pinned dates and once through the writer, then comparing the object identifiers, the
decompressed object bytes, the staged index listing and the whole commit log. It also
pins the resulting head identifier, so a change in the writer, the identity or the
clock fails as a changed identifier rather than silently.

## Core fit

**Agent substitution:** pass — the writer is a Python test helper invoked by the test runner, so any agent runtime that runs the suite gets the same objects
**Provider substitution:** not-applicable — nothing here talks to a hosting provider; it writes local Git objects that any Git implementation reads
**Repository substitution:** pass — every adopted repository runs this suite, and every one of them pays the same fixture spawn cost the writer removes
**User-global writes:** none
**Why AgentFold core:** the harness ships its own test suite and its speed is a property of the harness, not of one clone; the helper only writes inside the temporary fixture repositories the suite already creates
**Thin adapter:** none
