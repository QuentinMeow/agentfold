# Verification — cache the reconciler's Git object reads

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output. Timings on one host are not comparable
across sessions, and this host's variance is wide, so every before/after pair below was
taken in one session, alternating between main's `reconcile.py` and this branch's on the
same working tree, and is reported as a spread rather than one number.

Four scratch scripts under the git-ignored tmp/ produced the measurements. They are not
committed, so each is described where it is used and a reader can rebuild it:

- measure.py — alternates the working-tree `reconcile.py` between main's version and
  this branch's, timing `--check` and one per-check profile per round.
- spawncount.py — wraps `subprocess.run`/`Popen` and counts Git spawns per check,
  grouped by argv shape with object IDs collapsed.
- parity.py — calls `git_tree_path_entry`/`git_tree_blob_entry` twice per case, once
  with the object reader available and once with it forced unavailable, and compares.
- degrade.py — the same comparison for a whole run: every check's findings, plus the
  `ls-tree` spawn count each mode pays.

## The reconciler is green and the suite passes

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 78.89s
```

Trimmed: the runner prints its inert-probe and lane preamble above these lines. Re-run
from the committed tree, the same 11/11 pass in 83.66s — suite timing on this host moves
by several seconds run to run and is not a claim this change makes.

## Per-path `ls-tree` spawns: 102 become 0

spawncount.py, one cold process each, main's `reconcile.py` then this branch's.
Only the three affected checks are shown; every other check spawns the same Git it did.

```
$ cp tmp/before-reconcile.py automation/reconcile/reconcile.py   # main's version
$ python3 tmp/spawncount.py
queue-resolution              1.071s findings=0 spawns=58
task-admission                0.813s findings=0 spawns=42
handover-queue-projection    15.404s findings=0 spawns=324

   59  handover-queue-projection git --no-replace-objects ls-tree -z <oid> --
   49  handover-queue-projection git --no-replace-objects log --no-renames -1 --format=%H
   25  queue-resolution         git --no-replace-objects ls-tree -z <oid> --
   18  task-admission           git --no-replace-objects ls-tree -z <oid> --
    6  queue-schema             git cat-file -t <oid>
    3  queue-schema             git merge-base <oid> <oid>
```

```
$ cp tmp/after-reconcile.py automation/reconcile/reconcile.py    # this branch
$ python3 tmp/spawncount.py
queue-resolution              0.292s findings=0 spawns=9
task-admission                0.285s findings=0 spawns=6
handover-queue-projection    11.060s findings=0 spawns=206

   49  handover-queue-projection git --no-replace-objects log --no-renames -1 --format=%H
    6  queue-schema             git cat-file -t <oid>
    3  queue-schema             git merge-base <oid> <oid>
    3  handover-queue-projection git --no-replace-objects log --full-history --reverse --format=%H
    2  queue-resolution         git diff --cached --name-status -z -M
    1  <setup>                  git ls-files --stage -z
```

All 102 `ls-tree -z <oid> -- <path>` spawns — the shape this change replaces — are gone.
The `git log` spawns that now dominate `handover-queue-projection` are a different
question and are not this task's.

## `--check` timings, six interleaved rounds

measure.py, six rounds. Each round runs main's version and then this branch's on the same
working tree, so the host's variance hits both.

```
$ python3 tmp/measure.py 6
round 0 before total=26.35s queue-resolution=1.3326 exit=0
round 0 after  total=23.15s queue-resolution=0.3638 exit=0
round 1 before total=27.11s queue-resolution=0.9440 exit=0
round 1 after  total=19.13s queue-resolution=0.4116 exit=0
round 2 before total=24.49s queue-resolution=0.9511 exit=0
round 2 after  total=18.32s queue-resolution=0.3376 exit=0
round 3 before total=18.57s queue-resolution=0.8445 exit=0
round 3 after  total=16.95s queue-resolution=0.3046 exit=0
round 4 before total=20.10s queue-resolution=0.9750 exit=0
round 4 after  total=16.69s queue-resolution=0.3070 exit=0
round 5 before total=23.10s queue-resolution=0.9191 exit=0
round 5 after  total=17.77s queue-resolution=0.3051 exit=0

total            before n=6 min=18.574 median=23.796 max=27.110 mean=23.288
total            after  n=6 min=16.689 median=18.048 max=23.146 mean=18.669
total            speedup on medians: 1.32x

queue-resolution before n=6 min=0.845 median=0.948 max=1.333 mean=0.994
queue-resolution after  n=6 min=0.305 median=0.322 max=0.412 mean=0.338
queue-resolution speedup on medians: 2.94x

before exit=0 output='reconcile: 0 finding(s)\n'
after exit=0 output='reconcile: 0 finding(s)\n'
```

The spreads overlap on the whole run and do not overlap on `queue-resolution`: every
"after" round of that check is faster than every "before" round. Both versions printed
`reconcile: 0 finding(s)` and exited 0 in all six rounds — that is the last two lines,
which collect the distinct (exit code, output) pairs each version produced.

## The answers are identical, not merely equal in count

parity.py compares `git_tree_path_entry` and `git_tree_blob_entry` with the object
reader on and off across twelve revisions — eight commits, a tree, the empty tree, an
absent object ID, and the symbolic name `HEAD` — times twenty-four path shapes, including
directories, a nested blob, an absent path, a path under a blob, an empty path, `.`,
`..`, and a trailing slash.

```
$ python3 tmp/parity.py
compared 576 (revision, path, function) triples
mismatches: 0
```

degrade.py makes the same comparison for a whole run, and counts the spawns each
mode pays so the second run is demonstrably taking the uncached path:

```
$ python3 tmp/degrade.py
with raw reader:    0 finding(s) in 25.10s, 2 ls-tree spawns
without raw reader: 0 finding(s) in 28.27s, 104 ls-tree spawns
findings identical: yes
```

## The equivalence guard has teeth

`ls-tree` prints `040000` for a directory where a raw tree object stores `40000`. With
`mode.zfill(6)` removed — which is what a naive port of the discarded branch does — the
new guard fails:

```
$ python3 -m unittest ...ReconcileQueueTests.test_cached_object_reads_match_ls_tree_for_every_entry_kind
- (('040000', 'tree', '2d5227ba518686c5c99731559951832c67215410'), None)
?    -
+ (('40000', 'tree', '2d5227ba518686c5c99731559951832c67215410'), None) : `docs` at f445a3cc4ef44310c3bc68f4522c287dc76a1686

Ran 1 test in 0.603s

FAILED (failures=1)
```

Restored, the three new guards pass:

```
$ python3 -m unittest \
    ...ReconcileQueueTests.test_cached_object_reads_match_ls_tree_for_every_entry_kind \
    ...ReconcileQueueTests.test_unreadable_object_falls_back_instead_of_raising \
    ...ReconcileQueueTests.test_object_reader_never_supplies_commit_parents -v
test_cached_object_reads_match_ls_tree_for_every_entry_kind ... ok
test_unreadable_object_falls_back_instead_of_raising ... ok
test_object_reader_never_supplies_commit_parents ... ok

Ran 3 tests in 3.305s

OK
```

## Shallow clone: the failure path the discarded branch had

A depth-1 clone of this repository, where every commit before the boundary is a missing
object.

```
$ git clone --depth 1 file://<this worktree> tmp/shallow
$ cd tmp/shallow && git rev-parse --is-shallow-repository
true
```

The clone's HEAD carries main's `reconcile.py`. This is what it reports there — three
pre-existing findings for review revisions a depth-1 clone cannot resolve:

```
$ python3 automation/reconcile/reconcile.py --check ; echo "EXIT_MAIN=$?"
[queue-schema] message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md: **Review revision:** is not a reviewable Git artifact: 00690e89b53573aff4ca90929cc96852d00f7293 is unavailable; d7eefcee521ad319bbf428c796c96740833f2a17 is unavailable
    fix: use available literal commit ids with a shared history
[queue-schema] message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md: **Review revision:** is not a reviewable Git artifact: d87b755e6259101bf76b0a2783b35dfb3f163fb0 is unavailable; 8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b is unavailable
    fix: use available literal commit ids with a shared history
[queue-schema] message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md: **Review revision:** is not a reviewable Git artifact: 25d03257b5ee61753fa9bada609722c4e84a8064 is unavailable; fd2374d99796300ed4325c2961e696092c17875e is unavailable
    fix: use available literal commit ids with a shared history
reconcile: 3 finding(s)
EXIT_MAIN=1
```

This branch's `reconcile.py` copied over it prints the same three findings, in the same
order, with the same fixes — only the trailing summary is repeated here:

```
$ cp <this worktree>/automation/reconcile/reconcile.py automation/reconcile/reconcile.py
$ python3 automation/reconcile/reconcile.py --check ; echo "EXIT_CACHED=$?"
[... the identical three findings ...]
reconcile: 3 finding(s)
EXIT_CACHED=1
```

Staging a queue deletion makes `queue-resolution` actually run its deletion path, which
is the code the discarded branch changed. This branch's version, then main's on the same
staged state:

```
$ git rm -q message-queue/needs-agent/requests/non-blocking-build-the-stage-2-edge-schema.md
$ python3 automation/reconcile/reconcile.py --check ; echo "EXIT_CACHED_WITH_DELETION=$?"
[... the identical three queue-schema findings ...]
[queue-resolution] message-queue/needs-agent/requests/non-blocking-build-the-stage-2-edge-schema.md: deleted unresolved queue item: agent action was not committed as in-repair before deletion
    fix: commit the required claim/response evidence before deleting it
reconcile: 4 finding(s)
EXIT_CACHED_WITH_DELETION=1

$ git checkout HEAD -- automation/reconcile/reconcile.py
$ python3 automation/reconcile/reconcile.py --check ; echo "EXIT_MAIN_WITH_DELETION=$?"
[... the identical four findings ...]
reconcile: 4 finding(s)
EXIT_MAIN_WITH_DELETION=1
```

Four scenarios, identical findings, exit 1 every time. No `exit 2`, no silenced checks.
Lines in square brackets are elisions of output already printed verbatim above; every
other line is exactly what the command printed.

The discarded branch's version, installed in the same clone, raises out of the same
repository state — this is the mechanism that becomes `exit 2` with zero findings once a
claimed item reaches the evidence rule:

```
$ python3 shallow_probe.py       # the discarded branch's reconcile.py
shallow: true
HEAD: 6cd2de987a8894a8fd01cb36f7e910005f68c9cb
complete_creation_parents raised GitSnapshotError: creation history for `message-queue/needs-agent/requests/non-blocking-build-the-stage-2-edge-schema.md` is shallow or incomplete at 6cd2de987a8894a8fd01cb36f7e910005f68c9cb
read_raw_git_object: not present in this reconcile.py
```

The same probe against this branch's version — the missing boundary parent answers
`None`, the walk answers "ask Git yourself", and the parent list stays what `rev-list`
says it is:

```
$ python3 shallow_probe.py       # this branch's reconcile.py
shallow: true
HEAD: 6cd2de987a8894a8fd01cb36f7e910005f68c9cb
complete_creation_parents: not present in this reconcile.py
parents recorded in the raw HEAD commit: ['431423e4ca670c5d5ae1e42be0a453fd62c235f7']
revision_parents (rev-list, grafted view): []
read_raw_git_object(431423e4ca67) -> None
object_path_entry(431423e4ca67, AGENTS.md) -> UNREAD_TREE_ENTRY
```

shallow_probe.py imports the installed `reconcile.py`, calls
`complete_creation_parents` when that function exists, and otherwise prints what the raw
reader and `revision_parents` answer for the commit's unreachable parent.

## Review verdicts (when a review was explicitly run)

No independent review was invoked for this change; `--require-review` was not selected.
