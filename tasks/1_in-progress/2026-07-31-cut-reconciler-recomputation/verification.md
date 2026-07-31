# Verification — Cut the reconciler's repeated recomputation

**Verified:** 2026-07-31 by claude

Only commands actually run and their real output. Every number below was observed on this
machine during this session.

**Machine drift warning, observed rather than assumed.** The same `--check` baseline measured
5.11s early in the session and 10.51s later, with nothing changed between them. Absolute
seconds are therefore only comparable inside one measurement block. Every before/after ratio
below comes from `tmp/perf/ab.py timeit`, which alternates baseline and current runs inside
one block so the drift cancels.

## Differential harness

Baseline sources are materialised from the pre-change commit
`4d72249fc4cfc8da62efa61b9f7b5fcfe6f7f4aa` into the git-ignored `tmp/` mirror, whose depth
makes `REPO` and `AUTOMATION` resolve to the real repository. Both versions then read the same
clean working tree and the same Git index, so `--range` still sees an unmodified candidate.

```
$ python3 tmp/perf/ab.py parity 4d72249fc4cfc8da62efa61b9f7b5fcfe6f7f4aa check \
    range:bf5bcf95923691e7ebc674ef734cfa15a2a24742...9c12bb77f9461dba5a3e4a8782067df4d66e15b6 \
    range:b352c94b2e5f46f2a2a99630ce491699e38d81e5...9c12bb77f9461dba5a3e4a8782067df4d66e15b6 \
    rootrange:9c12bb77f9461dba5a3e4a8782067df4d66e15b6
  A-baseline  check                    rc=0 lines=   1    5.55s
  A-baseline  range:bf5bcf95923691e7   rc=0 lines=   1   24.62s
  A-baseline  range:b352c94b2e5f46f2   rc=0 lines=   1   60.99s
  A-baseline  rootrange:9c12bb77f946   rc=1 lines= 111  280.36s
  B-current   check                    rc=0 lines=   1    4.77s
  B-current   range:bf5bcf95923691e7   rc=0 lines=   1   31.08s
  B-current   range:b352c94b2e5f46f2   rc=0 lines=   1   59.49s
  B-current   rootrange:9c12bb77f946   rc=1 lines= 111  263.73s

parity check                    IDENTICAL  rc=0/0  stdout lines=1
parity range:bf5bcf95923691e7   IDENTICAL  rc=0/0  stdout lines=1
parity range:b352c94b2e5f46f2   IDENTICAL  rc=0/0  stdout lines=1
parity rootrange:9c12bb77f946   IDENTICAL  rc=1/1  stdout lines=111

PARITY: ALL IDENTICAL
```

`IDENTICAL` compares the exit code, the whole stdout finding list, and stderr. The root range
carries the 55 blocking findings (111 stdout lines: two lines per finding plus the summary),
so that exact set is what was proved unchanged. The seconds in this block are order-biased —
all baseline runs precede all current runs — and are not the speed evidence; the interleaved
block below is.

Control: pointing the harness at the working tree's own commit compares the current
reconciler with itself, which must agree — it confirms the mirror actually runs and that the
two sides are read the same way.

```
$ python3 tmp/perf/ab.py parity 9c12bb77f9461dba5a3e4a8782067df4d66e15b6 check
  A-baseline  check                    rc=0 lines=   1    3.83s
  B-current   check                    rc=0 lines=   1    3.74s

parity check                    IDENTICAL  rc=0/0  stdout lines=1

PARITY: ALL IDENTICAL
```

## Wall time, interleaved baseline/current

```
$ python3 tmp/perf/ab.py timeit 4d72249fc4cfc8da62efa61b9f7b5fcfe6f7f4aa 5 check
check
   baseline runs [10.19, 10.08, 10.51, 10.58, 10.63]  -> min 10.08s med 10.51s max 10.63s
   current  runs [5.07, 5.25, 5.58, 5.24, 5.4]  -> min 5.07s med 5.25s max 5.58s
   speedup  2.00x on medians, 1.99x on minima
```

```
$ python3 tmp/perf/ab.py timeit 4d72249fc4cfc8da62efa61b9f7b5fcfe6f7f4aa 3 \
    range:bf5bcf95923691e7ebc674ef734cfa15a2a24742...9c12bb77f9461dba5a3e4a8782067df4d66e15b6 \
    range:b352c94b2e5f46f2a2a99630ce491699e38d81e5...9c12bb77f9461dba5a3e4a8782067df4d66e15b6
range:bf5bcf95923691e7...9c12bb77f946
   baseline runs [47.62, 44.47, 46.93]  -> min 44.47s med 46.93s max 47.62s
   current  runs [24.58, 24.53, 26.06]  -> min 24.53s med 24.58s max 26.06s
   speedup  1.91x on medians, 1.81x on minima
range:b352c94b2e5f46f2...9c12bb77f946
   baseline runs [112.02, 109.44, 114.15]  -> min 109.44s med 112.02s max 114.15s
   current  runs [53.46, 55.45, 55.26]  -> min 53.46s med 55.26s max 55.45s
   speedup  2.03x on medians, 2.05x on minima
```

```
$ python3 tmp/perf/ab.py timeit 4d72249fc4cfc8da62efa61b9f7b5fcfe6f7f4aa 2 \
    rootrange:9c12bb77f9461dba5a3e4a8782067df4d66e15b6
rootrange:9c12bb77f9461dba5a3e4a8782067df4d66e15b6
   baseline runs [435.64, 452.42]  -> min 435.64s med 444.03s max 452.42s
   current  runs [248.94, 257.6]  -> min 248.94s med 253.27s max 257.60s
   speedup  1.75x on medians, 1.75x on minima
```

Range sizes, for the record:

```
$ git rev-list --count bf5bcf95923691e7ebc674ef734cfa15a2a24742...9c12bb77f9461dba5a3e4a8782067df4d66e15b6
22
$ git rev-list --count b352c94b2e5f46f2a2a99630ce491699e38d81e5...9c12bb77f9461dba5a3e4a8782067df4d66e15b6
72
$ git rev-list --count 9c12bb77f9461dba5a3e4a8782067df4d66e15b6
363
```

The machine was in its fast state early in the session; the same `--check` measured
`6.410 total` before any change and `2.909 total` after all of them under `time`, which is the
same 2.0x at half the absolute cost.

## Profile at the stack tip, before any change

```
$ python3 tmp/perf/profile_run.py check --check
         11607839 function calls (11603614 primitive calls) in 6.506 seconds
        1    0.006    0.006    3.744    3.744 reconcile.py:7134(check_handover_queue_projection)
        1    0.015    0.015    1.566    1.566 reconcile.py:7777(check_links)
     7573    0.012    0.000    1.202    0.000 reconcile.py:698(paths_under_prefix)
       52    0.004    0.000    1.094    0.021 reconcile.py:6768(handover_current_incarnation_text)
  3632897    0.498    0.000    0.498    0.000 {method 'startswith' of 'str' objects}
```

```
$ python3 tmp/perf/profile_run.py r20 --range <twenty-commits-back range>
         41754653 function calls (41753836 primitive calls) in 28.325 seconds
        1    0.000    0.000    9.461    9.461 reconcile.py:6004(check_task_action_origin)
        1    0.003    0.003    8.411    8.411 reconcile.py:6039(check_task_admission_history)
       21    0.034    0.002    7.111    0.339 reconcile.py:5267(check_task_structure)
        1    0.007    0.007    5.678    5.678 reconcile.py:7134(check_handover_queue_projection)
     5746    3.142    0.001    3.180    0.001 check_action_projection.py:1098(declarative_action_request)
    14322    1.851    0.000    5.676    0.000 markdown_semantics.py:112(_semantic_text)
      126    0.005    0.000    1.778    0.014 reconcile.py:1901(queue_revision_edges)
```

All four named hot spots reproduced at the stack tip. Their measured share of the run differs
from the pre-layer-1 audit: `check_task_admission_history` is 30% here rather than 22%, and
`check_handover_queue_projection` is 20% of the range run rather than 26%, because layer 1
already removed the object reads inside them.

## Profile after the change

```
$ python3 tmp/perf/profile_run.py final-check --check
         4164583 function calls (4162647 primitive calls) in 5.458 seconds
        1    0.038    0.038    2.322    2.322 reconcile.py:7805(check_links)
        1    0.010    0.010    1.806    1.806 reconcile.py:7162(check_handover_queue_projection)
       52    0.006    0.000    1.305    0.025 reconcile.py:6799(handover_current_incarnation_text)
      143    1.222    0.009    1.222    0.009 {method 'poll' of 'select.poll' objects}
```

Python-level work fell from 11.6M calls to 4.16M. `check_links` is now the largest `--check`
cost, and the remaining Git cost is one history query per handover.

```
$ python3 tmp/perf/profile_run.py r20b --range <twenty-commits-back range>
         14627967 function calls (14627127 primitive calls) in 19.878 seconds
       22    0.043    0.002    2.554    0.116 reconcile.py:5271(check_task_structure)
```

`check_task_structure` fell from 7.111s to 2.554s across 22 admitted edges without being
restructured at all: the per-edge cost was Markdown re-parsing, and memoising the pure text
views removed it.

## Spawn census

```
$ python3 tmp/perf/spawn_census.py --check
--- spawn census (wall 4.21s, 160 spawns, 1.75s in them) ---
   52     1.23s  git --no-replace-objects log --no-renames -1 --format=%H
    6     0.10s  git cat-file -t <oid>
    6     0.13s  git --no-replace-objects log --full-history --reverse --format=%H
```

(The census instruments both `subprocess.run` and the `Popen` it creates, so its 160 is 80
real processes counted twice.) On the pre-commit path the only remaining repeated Git process
is the one history query per handover, discussed under "What was skipped".

## Full test suite

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
test elapsed: 27.46s
```

## Reconciler gate

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

Every commit on this branch went through the installed `automation/hooks/pre-commit`; none
used `--no-verify`.

## What was skipped, and why

- **Restructuring `check_task_admission_history`'s per-edge `list(check_task_structure())`.**
  The named largest single win reproduced (25% of a range run), but it is not soundly
  cacheable — see `design.md`, Option A — and memoising the pure text views underneath it cut
  it by 2.8x anyway, to 13% of the run. Removing the rest would need the unsound fingerprint.
- **Memoising the `queue_revision_edges` generator itself.** Its measured cost was the Git
  process it spawned per commit per consumer, and routing that through `revision_parents`
  removes it while the generator stays lazy. Materialising it would move a mid-walk failure
  ahead of findings a consumer has already streamed.
- **The second Git process in `handover_current_incarnation_text`.** The `git show` half now
  goes through the batch reader. The other half is
  `git log -1 --diff-filter=A <revision> -- <path>`, a history query the object reader cannot
  answer. Batching it over the whole `history/conversations` directory changes Git's history
  simplification — TREESAME is computed against the pathspec, so a directory-limited walk can
  reach commits a file-limited walk prunes — which can change which commit is reported as the
  creation commit. It is 1.23s of the 5.5s `--check` and was left alone rather than risk the
  answer.
- **Caching `diff-tree` and recursive `ls-tree` output on immutable object IDs.** A spawn
  census of the twenty-commits-back range shows 105 `diff-tree` and 85 recursive `ls-tree` calls
  costing about 2s of a 15s run. Worth roughly 13% on ranges and nothing at all on the
  pre-commit path — the `--check` census contains none of them — so it was left for a
  follow-up rather than spent here.
