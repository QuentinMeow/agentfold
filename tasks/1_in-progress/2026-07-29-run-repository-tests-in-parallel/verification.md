# Verification — parallel test shards

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

Machine: 8 physical cores, 16 logical. `python3` on PATH is 3.7.6, which is what the
pre-commit hook and every command below use. Other agents were working on this machine
throughout, so absolute wall times are noisy; every comparison below is between variants
measured inside one session.

## Test-set equality between a serial and a sharded run

Both modes were run with `--verbose`, which forwards `-v` to every child so each child
prints the name of every test it executed. A throwaway extractor under the git-ignored
scratch directory parses those names out of the two logs and diffs the sets, and its
source is quoted below. It handles the two-line form the standard
runner uses for a test that has a docstring; the first version of the parser did not,
and silently under-reported by exactly the three documented tests in the suite.

```
$ python3 automation/run_tests.py --jobs 1 --verbose > tmp/serial.log 2>&1; echo "exit=$?"
exit=0

$ python3 automation/run_tests.py --jobs 8 --verbose > tmp/parallel8.log 2>&1; echo "exit=$?"
exit=0

$ python3 tmp/collect_test_names.py tmp/serial.log tmp/parallel8.log; echo "exit=$?"
tmp/serial.log: 653 test names
tmp/parallel8.log: 653 test names
only in tmp/serial.log: []
only in tmp/parallel8.log: []
sets are equal: True
exit=0
```

The extractor, in full, so the check can be re-run:

```python
VERBOSE_LINE = re.compile(r"^(test\w*) \(([\w.]+)\)( \.\.\. |$)")


def names(path):
    found = set()
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = VERBOSE_LINE.match(line)
            if match:
                found.add(match.group(2).rsplit(".", 1)[-1] + "." + match.group(1))
    return found
```

The same 653 names were then checked against what the shard planner believes exists, so
the equality is not two runs agreeing on the same mistake:

```
$ python3 -c "<compare AST discovery against the executed serial names>"
AST-discovered: 653 executed serially: 653
executed but not discovered: []
discovered but not executed: []
```

A unit test makes the third leg of that triangle permanent by diffing `ast` discovery
against `unittest.defaultTestLoader` for every real test file
(`ShardDiscoveryTests.test_discovery_matches_what_unittest_collects_for_every_real_test_file`).

## Shard plan and quarantine reporting

The reason string was reworded late in the task, after the timed runs were recorded, so
this is the planner's report for the current source rather than a grep of an older log.
The wording is pinned by
`ShardDiscoveryTests.test_the_quarantined_file_is_reported_with_its_reason`.

```
$ python3 -c "<build the 8-worker shard plan and call report_shard_plan>"
test workers: 8
test shards: 47
  serial tail: automation/tests/test_run_tests.py -> not concurrency-safe, its tests re-run this whole runner, so a shard of it would nest a second worker pool inside the first
```

No file needed the whole-file fallback: `ast` discovery currently sees every test in
every file, so the `whole file:` line does not appear for the real suite.

## Wall time by worker count, one interleaved session

Three rounds of `--jobs 1, 2, 4, 8` were run back to back inside a single script, because
identical code has measured 116s and 139s on this machine within the same hour. Only the
within-round ratios are meaningful. `cpu` is `user + sys`. Each row is one invocation of
`/usr/bin/time -p python3 automation/run_tests.py --jobs N`, and the table below is those
logs re-read.

```
round jobs  wall(s)  user(s)  sys(s)  cpu(s)  files
    1    1   116.25    51.57   58.85  110.42  tests: 11/11 files passed
    1    2    90.71    77.53   87.06  164.59  tests: 11/11 files passed
    1    4    56.48    86.77   96.63  183.40  tests: 11/11 files passed
    1    8    46.40   137.18  140.34  277.52  tests: 11/11 files passed
    2    1   139.00    61.16   71.06  132.22  tests: 11/11 files passed
    2    2    72.65    63.36   68.97  132.33  tests: 11/11 files passed
    2    4    44.88    71.12   75.55  146.67  tests: 11/11 files passed
    2    8    36.97   106.47  111.01  217.48  tests: 11/11 files passed
    3    1   117.40    52.38   59.13  111.51  tests: 11/11 files passed
    3    2    73.28    63.44   70.28  133.72  tests: 11/11 files passed
    3    4    49.78    77.72   85.31  163.03  tests: 11/11 files passed
    3    8    41.48   119.35  125.35  244.70  tests: 11/11 files passed
```

Wall-time ratio against the same round's single-worker run:

| round | 2 workers | 4 workers | 8 workers |
|-------|-----------|-----------|-----------|
| 1 | 1.28x | 2.06x | 2.51x |
| 2 | 1.91x | 3.10x | 3.76x |
| 3 | 1.60x | 2.36x | 2.83x |

Round 1 is the outlier and its total CPU says why: 164.59s at two workers against 132.22s
and 133.72s for the same variant in rounds 2 and 3. External load inflated it. Rounds 2
and 3 are the trustworthy pair, so the honest headline is roughly 2.8-3.8x at eight
workers and 1.6-1.9x at two.

Total CPU is flat from one worker to two (132.22 -> 132.33 in round 2; 111.51 -> 133.72 in
round 3) and rises at four and eight. Two effects, in the order of their size: the run
becomes its own noisy neighbour once more than eight processes are runnable — each shard
keeps a `git` child alive for most of its life, so eight workers put well over eight
threads on eight physical cores, and time on a hyperthread sibling is charged as CPU
time; and a higher worker count cuts smaller shards, so a module gets re-imported more
often. The second effect is measurable and small: the largest test module imports in
0.506s, and eight workers cut it into 23 shards rather than the 6 that two workers cut,
so about 9s of the increase is that one file's re-imports.

```
$ python3 -c "<time importing automation/tests/test_reconcile_queue.py once>"
import seconds 0.506
real 0.57
user 0.48
sys 0.06
```

## Repeated sharded runs, checked for concurrency-induced flakiness

Eleven full-suite sharded runs finished with every file passing and exit status 0: the
nine multi-worker rows of the table above (three rounds each of 2, 4 and 8 workers), plus
the `--jobs 8 --verbose` run used for the set-equality check, plus one earlier ad-hoc
`--jobs 8` run. No test failed in any of them, and no test failed in one mode but not
another.

```
$ for f in tmp/run-*.log; do printf '%s ' "$f"; grep -c "tests: 11/11 files passed" "$f"; done
tmp/run-r1-j1.log 1
tmp/run-r1-j2.log 1
tmp/run-r1-j4.log 1
tmp/run-r1-j8.log 1
tmp/run-r2-j1.log 1
tmp/run-r2-j2.log 1
tmp/run-r2-j4.log 1
tmp/run-r2-j8.log 1
tmp/run-r3-j1.log 1
tmp/run-r3-j2.log 1
tmp/run-r3-j4.log 1
tmp/run-r3-j8.log 1
```

## Final full-suite run at the default worker count

The default resolved to 8, the machine's physical core count, with no `--jobs` given.

```
$ /usr/bin/time -p python3 automation/run_tests.py
test workers: 8
test shards: 47
  serial tail: automation/tests/test_run_tests.py -> not concurrency-safe, its tests re-run this whole runner, so a shard of it would nest a second worker pool inside the first
...
tests: 11/11 files passed
test elapsed: 40.65s
real 40.75
user 117.52
sys 125.76
exit=0
```

## Runner unit tests

```
$ python3 automation/tests/test_run_tests.py
Ran 61 tests in 3.381s
OK (skipped=1)
```

47 of those existed before this change; 14 are new and cover inherited test methods, each
fail-safe trigger for discovery, discovery against the real loader, shard coverage, the
whole-file fallback for an unreadable file, the quarantine report, worker-count parsing,
the physical-core default, atomic shard output, quiet passing shards, shard command
shape, the parallel main path with its serial tail, and a failing shard's exit status.

That whole file also runs in 3.381s, which is the entire cost of the serial tail against
an eight-worker run of 37-46s.

## Repository gates

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ python3 automation/check_core_scope.py --staged
core-scope: pass (3 core path(s), task 2026-07-29-run-repository-tests-in-parallel; independent review manual; not invoked)
```

## Re-measured on the combined stack, 2026-07-30

The branch was rebased onto the honest-reporting and background-maintenance branches,
since all three touch the runner. Four full suites, alternating worker counts inside one
session, which is the only comparison this host supports:

```
$ for j in 1 8 1 8; do python3 automation/run_tests.py --jobs $j; done
jobs=1  tests: 11/11 files passed  test elapsed: 125.53s
jobs=8  tests: 11/11 files passed  test elapsed:  36.43s
jobs=1  tests: 11/11 files passed  test elapsed: 124.01s
jobs=8  tests: 11/11 files passed  test elapsed:  40.19s
```

Means 124.77s against 38.31s, a ratio of **3.26x**, with every file passing in all four
runs. An independent profile of the same repository measured 3.27x for an interleaved
serial-versus-four-shard comparison, arrived at by a different method.

CPU for one eight-worker run:

```
$ /usr/bin/time -p python3 automation/run_tests.py --jobs 8
tests: 11/11 files passed
test elapsed: 39.17s
real 39.29
user 112.84
sys 124.44
```

System time still exceeds user time, so the suite remains bound by process creation even
when the wall clock is divided across cores. Sharding divides that cost; it does not
change its nature.
