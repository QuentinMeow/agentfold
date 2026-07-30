# Verification — in-process fixture Git objects

Commands actually run on 2026-07-30, on macOS 25.5.0 with `git version 2.23.0` and
Python 3.7.6, in a worktree on this task's branch.

## Conformance: the written objects are what real Git writes

`automation/tests/test_reconcile_queue.py` builds one history twice — once through real
`git add` and `git commit` with a pinned identity and pinned dates, once through
`automation/tests/fixture_git.py` — over five commits covering nested directories, an
executable file, a symlink, a modification, a deletion, a branch, and a merge whose
extra parent comes from an uncommitted `git merge --no-ff --no-commit`. It compares the
object identifiers, the decompressed object bytes, the staged index listing, the
porcelain status and the whole commit log, and pins the resulting head identifier.

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_written_fixture_objects_match_what_real_git_writes -v
test_written_fixture_objects_match_what_real_git_writes (automation.tests.test_reconcile_queue.ReconcileQueueTests)
Guard the shortcut: the writer must produce real Git's objects exactly. ... ok

----------------------------------------------------------------------
Ran 1 test in 0.444s

OK
```

The compressed bytes match too, once the writer compresses at Git's own default
loose-object level rather than zlib's. The test deliberately asserts the decompressed
bytes instead, because zlib framing belongs to the compressor and not to the object
format. Measured separately, driving the same history builder the test uses:

```
$ python3 - <<'PY'   # drives ReconcileQueueTests.build_fixture_history directly
loose objects compared: 23
identical compressed bytes: 23
head: c3352b6f7af71715c6d07639d17eb0d04626372e
```

That head identifier is the one the test pins, so fixture object identifiers are
reproducible run to run: the identity is pinned, and each commit's clock is derived
(the first commit sits on a pinned epoch, every later commit a minute past its newest
parent) rather than read from the machine.

## Spawn census, before and after

Counted in process by wrapping `subprocess.Popen.__init__`, so the numbers are exact
rather than sampled. `before` is the file at `9aeb41a` in a separate worktree; `after`
is this branch. Both run the same file, in the same session, alternating.

```
=== before, round 1 (git add and git commit spawned) ===
tests run: 299  failures: 0  errors: 0
wall seconds: 76.75
total spawns: 7045  git spawns: 7045
    1449  git ls-tree
     793  git rev-parse
     789  git ls-files
     712  git rev-list
     647  git add
     526  git commit
     512  git log
     384  git merge-base
     361  git diff-tree
     334  git cat-file
     279  git diff
     103  git checkout
      40  git merge
      33  git show
      32  git branch
      19  git hash-object
       8  git diff-index
       7  git diff-files
       5  git config
       4  git rm
       2  git init
       2  git commit-tree
       2  git restore
       1  git tag
       1  git write-tree
=== after, round 1 (git add and git commit written in process) ===
tests run: 300  failures: 0  errors: 0
wall seconds: 64.92
total spawns: 5900  git spawns: 5900
    1449  git ls-tree
     796  git rev-parse
     791  git ls-files
     712  git rev-list
     514  git log
     384  git merge-base
     361  git diff-tree
     334  git cat-file
     279  git diff
     107  git checkout
      42  git merge
      34  git branch
      33  git show
      19  git hash-object
       8  git diff-index
       7  git diff-files
       7  git add
       5  git config
       5  git commit
       4  git rm
       2  git init
       2  git commit-tree
       2  git restore
       1  git tag
       1  git write-tree
       1  git status
```

7045 to 5900 git spawns, a removal of 1145. `git add` falls from 647 to 7 and
`git commit` from 526 to 5. Of what remains, the new conformance test spawns 4 adds and
5 commits itself, since one of its two arms is real Git on purpose. Outside that test
the file spawns no `git commit` at all, and three `git add` calls: one intent-to-add,
and the two adds of the single fixture that writes ignore rules. Both are declines the
writer makes deliberately, and both fall through to real Git unchanged. The extra
`checkout`, `merge`, `branch` and `status` spawns after the change are the conformance
test's own, not a regression.

## Wall time, both variants interleaved in one session

Separate runs on this machine are not comparable — identical code has measured 193s and
91s here, and other agents are using it — so both variants alternate inside one session.
Two sessions were run; the second is the one whose census is pasted above.

```
session 1 (summaries only)          session 2 (labelled, censused above)
before round 1   76.55s             before round 1   76.75s
after  round 1   60.94s             after  round 1   64.92s
before round 2   96.95s             before round 2   80.83s
after  round 2   66.42s             after  round 2   80.50s
```

Seven of eight runs favour the change; the eighth is a tie under contention. Median
before 78.8s against median after 65.7s, about 17 percent. Wall time is the supporting
evidence and it is noisy; the spawn count is the headline, and it is deterministic.
Note also that every `after` run carries one extra test — the conformance guard, which
builds the whole history twice, once with real Git.

## Full run of the changed file

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 300 tests in 64.471s

OK
```

## Repository gates

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
exit=0
$ python3 automation/check_core_scope.py --staged
core-scope: pass (2 core path(s), task 2026-07-30-write-fixture-git-objects-in-process; independent review manual; not invoked)
exit=0
```

## Not changed

`automation/tests/test_check_core_scope.py` creates a repository with
`--object-format=sha256`, which identifies objects with a different algorithm; it is
untouched and keeps using real Git throughout. `automation/tests/test_check_action_projection.py`
is the next candidate at roughly 96 adds and 23 commits, and was left alone so this
change stays in one file while other branches are in flight.
