# Verification — read each repository view once per action-projection run

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output. Timings on one host are not comparable
across sessions, so every before/after pair below was taken in one session, alternating
between a worktree at origin/main and this branch.

## The gate itself: 84 Git processes become 2

One `projection_findings` run against this repository, counted by wrapping
`subprocess.run` and timing the call. Two runs of each, alternating.

```
$ python3 gate_cost.py <worktree at origin/main>
git spawns:   84   elapsed: 0.707s   findings: 1
git spawns:   84   elapsed: 0.701s   findings: 1
$ python3 gate_cost.py <this branch>
git spawns:    2   elapsed: 0.028s   findings: 1
git spawns:    2   elapsed: 0.027s   findings: 1
```

The same one finding is reported on both sides. The remaining two processes are the one
index read and the one batched size read.

## The verdicts are identical, not merely equal in count

17 probes — the four `projection_findings` bodies below, the live queue listing, four path
prefixes, and four path lookups including a directory and an absent path — serialised to
JSON from each side and compared byte for byte.

```
$ python3 equiv.py <worktree at origin/main> > before.json
$ python3 equiv.py <this branch> > after.json
$ diff -q before.json after.json && echo IDENTICAL
IDENTICAL output across 17 probes
live queue paths compared: 41
tracked AGENTS.md: True | tracked tasks(dir): False
record tasks(dir): None | record AGENTS.md: ['100644', '7803afbed0d45318bd2a0b552f81e18a4de93204', '0']
paths under tasks: 152 | under message-queue: 47 | under nope: 0
```

## The equivalence guards pass against the old implementation too

Four of the new tests describe behaviour that must not have changed, so they were run
against the unmodified module in the origin/main worktree. A guard that only passed on
the new code would prove nothing.

```
$ cd <worktree at origin/main> && python3 -m unittest \
    ...RepositoryViewTests.test_a_directory_is_not_a_tracked_file_and_has_no_record \
    ...RepositoryViewTests.test_a_path_recorded_at_several_merge_stages_is_not_one_record \
    ...RepositoryViewTests.test_an_empty_tracked_file_is_not_a_tracked_regular_file \
    ...RepositoryViewTests.test_outside_every_scope_each_lookup_reads_the_repository_again -v
test_a_directory_is_not_a_tracked_file_and_has_no_record ... ok
test_a_path_recorded_at_several_merge_stages_is_not_one_record ... ok
test_an_empty_tracked_file_is_not_a_tracked_regular_file ... ok
test_outside_every_scope_each_lookup_reads_the_repository_again ... ok

Ran 4 tests in 0.401s

OK
```

The one case that does differ is the empty prefix, which used to raise from Git and now
raises a `ValueError`:

```
RuntimeError: fatal: empty string is not a valid pathspec. please use . instead if you meant to match all paths
```

## The module's own tests

The same 119 tests, before and after:

```
$ python3 -m unittest automation.tests.test_check_action_projection     # origin/main
Ran 119 tests in 16.149s
OK

$ python3 -m unittest automation.tests.test_check_action_projection     # this branch
Ran 119 tests in 11.164s
OK
```

Its Git process count over the same run, counted by wrapping `subprocess.run`:

```
$ python3 count_spawns.py automation.tests.test_check_action_projection   # origin/main
TOTAL git spawns: 1496
    700  git ls-files
    304  git cat-file
    182  git show
    138  git add
     53  git rev-parse
     23  git commit
     72  git ls-tree

$ python3 count_spawns.py automation.tests.test_check_action_projection   # this branch
TOTAL git spawns: 962
    387  git ls-files
    176  git cat-file
    141  git show
    138  git add
     53  git rev-parse
     23  git commit
     20  git ls-tree
```

The 387 remaining index reads are one per run, and the module drives 439 separate runs
against repositories it mutates between them, so they are not shareable.

With the ten new tests included:

```
$ python3 -m unittest automation.tests.test_check_action_projection
Ran 129 tests in 11.486s
OK
```

## The complete suite is unchanged, and that is the honest result

Two alternating rounds, origin/main worktree first each time:

```
round 1  before(main): test elapsed: 40.07s   after(branch): test elapsed: 48.60s
round 2  before(main): test elapsed: 49.78s   after(branch): test elapsed: 48.98s
```

The spread within one side is larger than any difference between the sides. Sharded across
cores this module is not the critical path — `test_reconcile_queue.py` is — so making it
cheaper does not move the suite's wall clock. The gain is in the gate, which CI invokes
nine times per workflow, and in serial runs of the module.

```
$ python3 automation/run_tests.py --jobs 8
...
tests: 11/11 files passed
test elapsed: 25.58s
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```
