# Verification — Contain the test suite's temporary Git repositories to one scratch root

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output. Snapshot counts come from a small
script written for this task (`tmp/snapshot_tmp.py`, git-ignored scratch, not committed)
that lists directories in `tempfile.gettempdir()` whose name starts with `tmp` or
`agentfold`, flagging whether each contains a nested `.git`/`objects` — the signal that
distinguishes a leaked fixture repository from unrelated churn already on a shared
machine (this machine already had dozens of unrelated `tmp*` directories from other tools
before this task touched anything).

## Baseline: a completed run leaks nothing (true before and after the fix)

Before any code change:

```
$ python3 tmp/snapshot_tmp.py tmp/before2.tsv && python3 automation/run_tests.py > tmp/run2.log 2>&1; echo "exit=$?" && python3 tmp/snapshot_tmp.py tmp/after2.tsv && diff tmp/before2.tsv tmp/after2.tsv
63 candidate directories snapshotted to tmp/before2.tsv
exit=0
63 candidate directories snapshotted to tmp/after2.tsv
(no diff output — zero new directories)
```

After the fix, re-checked the same way (also re-run a second time for this record):

```
$ python3 tmp/snapshot_tmp.py tmp/vfinal_before.tsv && python3 automation/run_tests.py > tmp/vfinal_run.log 2>&1; echo "exit=$?" && python3 tmp/snapshot_tmp.py tmp/vfinal_after.tsv && diff tmp/vfinal_before.tsv tmp/vfinal_after.tsv; echo "diff-exit=$?"
63 candidate directories snapshotted to tmp/vfinal_before.tsv
exit=0
63 candidate directories snapshotted to tmp/vfinal_after.tsv
diff-exit=0
```

The historical "596 directories per run" / "937 leaked directories" figures
(`history/conversations/2026-07-29-1833PDT-fast-local-test-feedback/handover.md`) were not
reproduced on a completed run, before or after this change — the suite already shards at
test-method granularity and each fixture's own context manager already cleans up when the
process exits normally. Note: one otherwise-identical completed-run comparison, taken by
dispatching the "before" snapshot and the run as two separate concurrent tool calls
instead of one sequential shell chain, showed spurious diffs (directories that appeared
then vanished, or unrelated bare `tmp*` entries with no git content). Every number quoted
in this file was taken from a single sequential `&&`-chained shell command so no
concurrently-dispatched tool call could race the process being measured.

## The actual failure: a killed run, before the fix

Simulated a developer killing an interrupted run: start the runner in its own process
group, let it run 15s, then `SIGKILL` the whole group (`tmp/interrupt_run.py`, git-ignored
scratch).

```
$ python3 tmp/snapshot_tmp.py tmp/base_before_kill.tsv && python3 tmp/interrupt_run.py 15 && python3 tmp/snapshot_tmp.py tmp/base_after_kill.tsv && diff tmp/base_before_kill.tsv tmp/base_after_kill.tsv
63 candidate directories snapshotted to tmp/base_before_kill.tsv
killed whole process group after 15.00s (target 15.0s)
81 candidate directories snapshotted to tmp/base_after_kill.tsv
1a2,9
> agentfold-git-fixture-6v5b7auf	False	1785484723.9612963
> agentfold-git-fixture-a8a3b2ss	False	1785484719.8677118
> agentfold-git-fixture-bkuhnpng	False	1785484725.057421
> agentfold-git-fixture-d8950efc	False	1785484724.6803002
> agentfold-git-fixture-gt43f3rj	False	1785484723.02856
> agentfold-git-fixture-krv6z27f	False	1785484714.6924684
> agentfold-git-fixture-rc94_ohp	False	1785484720.6304991
> agentfold-git-fixture-ujn1cjun	False	1785484717.5243459
2a11
> agentfold-tests-x7yrcavi	False	1785484710.8340101
10a20
> tmp08nrexyb	True	1785484725.6382167
13a24
> tmp3rmo9d08	True	1785484725.2109287
21a33
> tmp5yhvz6x1	True	1785484725.3646748
22a35
> tmp8doihyb_	True	1785484725.5661075
31a45
> tmpfbtfpbeo	True	1785484725.660234
33a48
> tmpg116h0sy	True	1785484725.3778012
53a69
> tmprcc63e0v	True	1785484725.273174
58a75
> tmpvt61hms6	False	1785484715.8935568
60a78
> tmpx24dk54d	True	1785484725.126881
```

18 new directories, scattered as top-level siblings in the real system temp directory,
after a single 15-second interruption of one full-suite run — 8 per-process fixture-skeleton
caches, the run's own outer scratch root, and 9 individual test fixtures (7 of them
confirmed git repositories by the nested-`.git` check). A second, earlier trial (same
method, different random kill timing) found 12 new directories of the same shape. All were
removed by hand (`rm -rf`) after each measurement.

## After the fix: the same kill leaves one directory

```
$ python3 tmp/snapshot_tmp.py tmp/fix_before_kill.tsv
63 candidate directories snapshotted to tmp/fix_before_kill.tsv
$ python3 tmp/interrupt_run.py 15
killed whole process group after 15.00s (target 15.0s)
$ python3 tmp/snapshot_tmp.py tmp/fix_after_kill.tsv && diff tmp/fix_before_kill.tsv tmp/fix_after_kill.tsv
64 candidate directories snapshotted to tmp/fix_after_kill.tsv
2a3
> agentfold-tests-x4m5t_n7	False	1785485122.000241
```

One new directory. Its contents, confirmed nested rather than scattered:

```
$ find /var/folders/9g/nnmcgvqd5kvc99gqpbv1d1kr0000gn/T/agentfold-tests-x4m5t_n7 -maxdepth 2
.../agentfold-tests-x4m5t_n7/git-home
.../agentfold-tests-x4m5t_n7/git-xdg-config
.../agentfold-tests-x4m5t_n7/view
.../agentfold-tests-x4m5t_n7/tmp
.../agentfold-tests-x4m5t_n7/tmp/agentfold-git-fixture-to62zfrk
.../agentfold-tests-x4m5t_n7/tmp/tmpd9azj7_m
.../agentfold-tests-x4m5t_n7/tmp/agentfold-git-fixture-_aqkholg
.../agentfold-tests-x4m5t_n7/tmp/agentfold-git-fixture-ixbt13xj
.../agentfold-tests-x4m5t_n7/tmp/tmp44u49og1
.../agentfold-tests-x4m5t_n7/tmp/agentfold-git-fixture-g85w_mar
.../agentfold-tests-x4m5t_n7/tmp/tmps_b9sma0
.../agentfold-tests-x4m5t_n7/tmp/agentfold-git-fixture-ra1y_161
.../agentfold-tests-x4m5t_n7/tmp/tmpeopiwflp
.../agentfold-tests-x4m5t_n7/tmp/tmpwpa8t730
.../agentfold-tests-x4m5t_n7/tmp/tmpl66wf57q
.../agentfold-tests-x4m5t_n7/tmp/agentfold-git-fixture-8s9m9ali
.../agentfold-tests-x4m5t_n7/tmp/tmp97ibyo99
.../agentfold-tests-x4m5t_n7/tmp/agentfold-git-fixture-p_3nksep
```

The 7 fixture-skeleton caches and 8 per-test repositories that would previously have been
scattered as siblings across the real system temp directory are now nested under this one
run's own `.../tmp/` — deleting the one top-level directory removes everything.
Removed by hand after the measurement (`rm -rf .../agentfold-tests-x4m5t_n7`).

**Not solved:** interruption itself. `SIGKILL` (and an uncaught `SIGTERM`) skip every
`finally` block, context-manager `__exit__`, and `atexit` hook, so nothing can run cleanup
in response to it. What changed is where the unavoidable debris lands.

## Full suite still passes, and what it asserts is unchanged

```
$ python3 automation/run_tests.py
...
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
test elapsed: 38.68s
```

The new/extended assertions, run directly:

```
$ python3 -m unittest automation.tests.test_run_tests -v 2>&1 | grep -i "isolated_scratch_tmpdir\|passes_the_isolated_environment"
test_isolated_scratch_tmpdir_redirects_child_fixture_repositories (automation.tests.test_run_tests.RunTestsIsolationTests)
A killed run must leave at most one named directory, not hundreds. ... ok
test_main_passes_the_isolated_environment_to_each_test (automation.tests.test_run_tests.RunTestsIsolationTests) ... ok
```

Full `test_run_tests.py` run in isolation: `Ran 66 tests in 4.539s / OK (skipped=1)` — the
same one skip (`AGENTFOLD_INERT_PROBE` opt-in) that existed before this change; no test's
assertions were altered, only two additions.

## Runtime: before vs after

Full-suite wall time (`test elapsed`, `python3 automation/run_tests.py`, default `--jobs`
i.e. one shard per physical core). Some pairs interleaved via `git stash` / `git stash pop`
on `automation/run_tests.py` to reduce the machine-noise bias documented in
`history/conversations/2026-07-29-1833PDT-fast-local-test-feedback/handover.md` (that
session measured 91s vs 193s for *identical* code across separate lock holds on this same
machine).

| Run | Original code | Fixed code |
|---|---|---|
| 1 | 41.07s | 52.88s |
| 2 | 40.57s | 48.83s |
| 3 | 37.51s | 53.61s |
| 4 (interleaved a) | 49.49s | 42.84s |
| 5 (interleaved b) | 35.86s | 47.60s |
| 6 | — | 45.98s |
| 7 | — | 38.15s |
| 8 | — | 33.74s |
| 9 | — | 54.35s |
| **range** | 35.86-49.49s | 33.74-54.35s |
| **average** | 40.90s (n=5) | 46.44s (n=9) |

The ranges overlap almost completely; the ~5.5s (13%) average difference is well inside
the 2x variance already documented on this machine for byte-identical code, and there is
no mechanism by which the change (one `Path.mkdir()` call and three dict assignments,
executed once per run, not once per test) could cost seconds of wall time. Read as: no
measurable regression distinguishable from this machine's known run-to-run noise.

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```
