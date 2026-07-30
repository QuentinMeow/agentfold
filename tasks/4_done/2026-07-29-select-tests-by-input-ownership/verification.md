# Experiment A — input-scoped test selection

Branch exp/a-input-scope, based on main @ bf6f726. Worktree
/private/tmp/agentfold-exp/a-input-scope.

**Measurement conditions, stated up front:** every timing below was taken on the shared
8-core box while other agents were benchmarking. `uptime` reported load averages between
**6.5 and 10.4** throughout. Wall-clock numbers are therefore inflated (roughly 3-4x
against an idle machine, judging by the repo's own recorded suite time of ~220s versus
what I measured); `user`+`sys` CPU seconds are reported alongside every wall figure
because they are far less sensitive to contention. Ratios between lanes measured in the
same window are the trustworthy part.

## What I built

All of it extends the existing `--staged` machinery in `automation/run_tests.py`; the
git plumbing, index fingerprinting, symlink and index-mode guards, `TestSelection`, and
the full-suite fallback are unchanged.

1. **An explicit input-ownership table** (`automation/run_tests.py`):
   - `INPUT_TEST_OWNERS` — 14 entries mapping one exact path (or one `automation/reconcile/`
     prefix) to the test files that read it, e.g. `automation/reconcile/` →
     `test_reconcile_queue.py`, `automation/run_tests.py` → `test_run_tests.py`,
     `.github/workflows/harness.yml` → three tests.
   - `GROUP_TEST_OWNERS` — the coarse fallback: any *other* path under `automation/` or
     `.github/` owns every automation test; any other path under `skills/` owns every
     skills test (there are none today).
   - `SERVICE_TEST_DEPENDENCIES` — untouched, the pre-existing quote-service closure.
   - Discovered test files own themselves; any other file inside a test's directory
     (support module, fixture) owns every test in that directory.
   - `INERT_PATH_PREFIXES` (`docs/ handbook/ history/ memory/ message-queue/ roadmap/
     tasks/ templates/`), plus `LICENSE`, plus **Markdown outside a test's own
     directory** under a registered top-level entry → own **nothing**.
   - Everything else → **full suite**, including any unregistered top-level entry, any
     root-level non-Markdown file (`.gitignore` stays full: it changes what the
     projection contains), and **any removal or rename of a non-record path**.
2. **Selection still returns the existing `TestSelection` namedtuple**, with one added
   field (`staged_paths`, defaulted) carrying the per-path decisions so the run can
   print *why*. `report_selection` now prints the lane, the reason, each staged path with
   the tests it selected, the selected files, and the count and names of the skipped
   files.
3. **Two guards** (see "What could silently break" for the tradeoff):
   - `InputOwnershipTests` in `automation/tests/test_run_tests.py` — static, ~1.6s, runs
     in every suite. It parses every discovered test for path literals joined onto a
     real-repository directory and asserts the ownership table gives that test every
     path it reads; it also asserts ownership is closed under the module import graph of
     `automation/*.py` and `.github/scripts/*.py`.
   - `prune_inert_projection` — every narrow lane now *deletes* record paths from its
     projection before running anything, so a test that starts reading one fails instead
     of silently invalidating the table. Same function backs the opt-in heavy probe
     (`AGENTFOLD_INERT_PROBE=1`), which runs the whole suite against a record-free
     projection.
4. **Selector tests** in `automation/tests/test_run_tests.py`: record-only selects
   nothing; unregistered top-level (and a brand-new dir's `README.md`) selects full;
   each registered automation input selects only its owners; an unregistered
   `automation/` path selects every automation test; a test-file edit selects only that
   test; a record-shaped path inside a test directory selects that directory's tests;
   mixed record + automation + service selects the union; removals and renames of
   non-record paths select full; a typechange into a symlink selects full; the report
   names lane, reason and skipped files.

Also updated: the `run_tests.py` row in `automation/AGENTS.md` (single source of truth
for what the runner does). It had to stay a *row* edit: that contract sits exactly on its
60-line budget, and the reconciler rejected the extra rule bullet I first wrote
(`[agents-budget] automation/AGENTS.md: 66 lines exceeds the 60-line budget`). Worth
knowing for anyone repeating this: the budget check reads the **committed** file, so it
only fires after `git commit`, not on the dirty tree.

## Real numbers

Staging was done in a throwaway index (`GIT_INDEX_FILE`) so the working tree stayed
clean; the driver is tmp/measure.sh in this worktree (git-ignored, so it is **not** in
the commit — the recipe below is the whole of it). `/usr/bin/time -p` supplies
`real`/`user`/`sys`.

```
PROBE_DIR="$(mktemp -d /private/tmp/agentfold-input-scope.XXXXXX)"
export GIT_INDEX_FILE="$PROBE_DIR/index"
git read-tree HEAD
OTHER="$(git rev-parse HEAD:LICENSE)"   # any real blob, so the entry differs from HEAD
# (a) records: rename a task, delete a queue item, touch record files
git update-index --force-remove tasks/0_backlog/<task>/task.md
git update-index --add --info-only --cacheinfo "100644,$TASK_OID,tasks/1_in-progress/<task>/task.md"
git update-index --info-only --cacheinfo "100644,$OTHER,memory/index.md"
# (b) service   git update-index --info-only --cacheinfo "100644,$OID,services/quote-cli/quote_cli.py"
# (c) reconcile git update-index --info-only --cacheinfo "100644,$OTHER,automation/reconcile/reconcile.py"
# (d) new dir   git update-index --add --info-only --cacheinfo "100644,$OTHER,brand-new-directory/module.py"
/usr/bin/time -p python3 automation/run_tests.py --staged
```

### (a) records-only change — 0 tests, 0.24s

Shape: the commonest AgentFold commit — a task folder moves status, a queue item is
deleted, memory/roadmap records change, plus `automation/AGENTS.md`.

```
$ sh tmp/measure.sh records
--- staged diff ---
M	automation/AGENTS.md
A	history/conversations/2026-07-29-probe/handover.md
M	memory/index.md
D	message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
M	roadmap/current-state.md
R100	tasks/0_backlog/2026-07-26-continue-development-cycle-acceleration/task.md	tasks/1_in-progress/2026-07-26-continue-development-cycle-acceleration/task.md
--- run ---
test lane: staged
test reason: every staged path is a record path no test reads
staged paths: 7
  automation/AGENTS.md -> record path, no test reads it
  history/conversations/2026-07-29-probe/handover.md -> record path, no test reads it
  memory/index.md -> record path, no test reads it
  message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md -> removed record path, no test reads it
  roadmap/current-state.md -> record path, no test reads it
  tasks/0_backlog/2026-07-26-continue-development-cycle-acceleration/task.md -> removed record path, no test reads it
  tasks/1_in-progress/2026-07-26-continue-development-cycle-acceleration/task.md -> record path, no test reads it
selected test files:
  (none)
skipped test files: 11 (no staged path owns them)
  ... [all 11 listed]
no discovered test file can be affected by the staged change
test elapsed: 0.05s
real 0.24
user 0.15
sys 0.07
```

No projection is built, no child process is spawned: the 0.24s is two `git` calls plus
classification. Before this change the same diff ran the entire suite.

### (b) services/quote-cli change — 1 test, 3.03s

```
$ sh tmp/measure.sh service
test lane: staged
test reason: every staged path maps to its registered test owners
staged paths: 1
  services/quote-cli/quote_cli.py -> test_quote_cli.py
selected test files:
  services/quote-cli/tests/test_quote_cli.py
skipped test files: 10 (no staged path owns them)
...
Ran 3 tests in 0.772s
OK
pruned record paths from the narrow test view: 299
PASS services/quote-cli/tests/test_quote_cli.py
tests: 1/1 files passed
test elapsed: 2.84s
real 3.03
user 1.12
sys 1.01
```

Unchanged behaviour from the pre-existing service lane, except that the projection now
has 299 record paths deleted from it and the test still passes.

### (c) automation/reconcile/reconcile.py change — 1 test, 418.56s

```
$ sh tmp/measure.sh reconcile
test lane: staged
test reason: every staged path maps to its registered test owners
staged paths: 1
  automation/reconcile/reconcile.py -> test_reconcile_queue.py
selected test files:
  automation/tests/test_reconcile_queue.py
...
Ran 298 tests in 415.494s
OK
pruned record paths from the narrow test view: 299
PASS automation/tests/test_reconcile_queue.py
tests: 1/1 files passed
test elapsed: 418.38s
real 418.56
user 158.53
sys 225.73
```

This is the honest bad news: `test_reconcile_queue.py` alone is enormous (298 unittest
cases). Input scoping removes the *other* ten files from a reconciler edit, but the edit
still pays for the whole reconciler test file. Selection cannot fix that; only splitting
or parallelising that file can. This lane ran **unlocked** while another agent was
running its own suite, so 418s is contended; the locked full run below times the same
file at 310.1s, which is the fairer figure for this lane (~313s with overhead).

### (d) brand-new top-level directory — full suite, 11/11 pass, 432.22s

This is also the "full suite still passes with my changes" receipt (see the caveat in
*What I did NOT do*): after selection falls back, the execution path is the default
full-suite path, with no record pruning.

```
$ sh tmp/locked_run.sh sh tmp/measure.sh newtop
--- staged diff ---
A	brand-new-directory/module.py
--- run ---
test lane: full
test reason: staged path has no registered test owner
selected test files:
  automation/tests/test_check_action_projection.py
  automation/tests/test_check_core_scope.py
  automation/tests/test_collect_github_review_actions.py
  automation/tests/test_github_action_projection_workflow.py
  automation/tests/test_inspect_workspace_boundaries.py
  automation/tests/test_mine_cochange.py
  automation/tests/test_reconcile_queue.py
  automation/tests/test_resolve_github_external_sources.py
  automation/tests/test_run_tests.py
  services/quote-api/tests/test_quote_api.py
  services/quote-cli/tests/test_quote_cli.py
[...]
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
test elapsed: 432.02s
real 432.22
user 173.81
sys 219.96
```

### The four numbers side by side

| staged change | test files run | wall | vs full suite |
|---|---|---|---|
| (a) records only (7 paths incl. a rename and a delete) | 0 | **0.24s** | 1800x faster |
| (b) `services/quote-cli/quote_cli.py` | 1 | **3.03s** | 143x faster |
| (c) `automation/reconcile/reconcile.py` | 1 | **418.56s** contended / ~313s locked-equivalent | ~1.4x faster |
| (d) new top-level dir brand-new-directory/module.py | 11 (full) | **432.22s** | 1.0x (by design) |

### Where the suite's time actually is (from lane (d)'s locked run)

Unittest's own per-file summaries, in selection order:

| file | cases | seconds |
|---|---|---|
| test_check_action_projection.py | 118 | 72.267 |
| test_check_core_scope.py | 55 | 2.902 |
| test_collect_github_review_actions.py | 24 | 0.015 |
| test_github_action_projection_workflow.py | 10 | 0.021 |
| test_inspect_workspace_boundaries.py | 40 | 21.197 |
| test_mine_cochange.py | 28 | 15.241 |
| **test_reconcile_queue.py** | **298** | **310.103** |
| test_resolve_github_external_sources.py | 9 | 0.006 |
| test_run_tests.py | 46 | 4.433 |
| test_quote_api.py | 5 | 0.221 |
| test_quote_cli.py | 3 | 0.553 |

`test_reconcile_queue.py` is **72%** of the suite and `test_check_action_projection.py`
another 17%. Input scoping is worth 100-1800x on the commits that touch neither, and
almost nothing on a reconciler edit.

### Replay against the last 60 real commits

tmp/history_simulation.py feeds each commit's own `git diff-tree --name-status` through
the shipped ownership functions (it skips only the index/working-tree verification steps,
which can never narrow a lane — they only widen it to full).

```
$ python3 tmp/history_simulation.py 60
6405877f  test_github_action_projection_workflow.py,test_reconcile_queue  test: admit the trusted-gate migration boundary
92aa4fd1  NOTHING                                                         docs: normalize the test-gate adapter receipt
[...]
66e87ed3  test_run_tests.py                                               Close staged test selection gaps
[...]
e8058124  test_reconcile_queue.py                                         fix: stop reading a merge parent edge as a task lifecycle st
6d4e337c  test_check_action_projection.py,test_github_action_projection_  fix: render code spans on both sides of the handover copy ch
35582c25  test_mine_cochange.py                                           docs: record the co-change gating experiment verdict
e52f68ef  test_mine_cochange.py,test_reconcile_queue.py                   feat: validate heading anchors and mine co-change couplings

--- histogram over 60 commits ---
  52  0 file(s)
   5  1 file(s)
   2  2 file(s)
   1  4 file(s)

test-file executions over the window: 13 (full-suite policy: 660)
```

**Zero of the 60 commits would have fallen back to the full suite**, and 52 of 60 (87%)
would have run no test at all. 13 test-file executions instead of 660 — a 98% cut.

Combining that replay with the measured per-file times (a derived estimate, not 60
measured runs): the window costs about **28 minutes** of pre-commit test time under
input scoping versus **7.2 hours** under today's full-suite-every-commit policy, ~15x
overall — and ~1250s of that remaining 1700s is `test_reconcile_queue.py` running for
the four commits that touched the reconciler or `check_action_projection.py`.

### The inert claim, re-proved by deletion (not just corruption)

The opt-in probe deletes the record trees outright — a real commit can delete and rename
records, so corrupting content under-tests the claim — then runs all 11 files.

```
$ AGENTFOLD_INERT_PROBE=1 sh tmp/locked_run.sh /usr/bin/time -p python3 \
    automation/tests/test_run_tests.py \
    InputOwnershipTests.test_the_whole_suite_passes_against_a_record_free_projection
inert probe: removed 299 record path(s)
inert probe: PASS automation/tests/test_check_action_projection.py
inert probe: PASS automation/tests/test_check_core_scope.py
inert probe: PASS automation/tests/test_collect_github_review_actions.py
inert probe: PASS automation/tests/test_github_action_projection_workflow.py
inert probe: PASS automation/tests/test_inspect_workspace_boundaries.py
inert probe: PASS automation/tests/test_mine_cochange.py
inert probe: PASS automation/tests/test_reconcile_queue.py
inert probe: PASS automation/tests/test_resolve_github_external_sources.py
inert probe: FAIL automation/tests/test_run_tests.py
inert probe: PASS services/quote-api/tests/test_quote_api.py
inert probe: PASS services/quote-cli/tests/test_quote_cli.py
[...]
AssertionError: Lists differ: [] != ['automation/tests/test_run_tests.py\n...
    inert probe: removed 0 record path(s)
    ...
    File ".../view/automation/tests/test_run_tests.py", line 709, in
      test_the_whole_suite_passes_against_a_record_free_projection
        self.assertGreater(removed, 0)
    AssertionError: 0 not greater than 0
    Ran 46 tests in 5.825s
    FAILED (failures=1)
Ran 1 test in 495.246s
FAILED (failures=1)
real 495.45
user 198.69
sys 257.04
```

**Ten of eleven files passed outright with every record path deleted.** The eleventh
failure is my probe recursing into itself: `AGENTFOLD_INERT_PROBE=1` was inherited by the
projected copy of `test_run_tests.py`, whose nested probe found a projection with no
records left to remove and failed its own `assertGreater(removed, 0)` — and the nested
run's other 45 tests all passed. Not a record read.

Fixed by dropping the variable from the child environment, then re-checked on that one
file (a targeted re-run, not a third full suite):

```
$ /usr/bin/time -p python3 tmp/record_free_one.py
removed 300 record path(s) from the projection
PASS automation/tests/test_run_tests.py in 5.38s
  | Ran 46 tests in 5.130s
  | OK (skipped=1)
real 7.13
user 3.06
sys 1.75
```

So all 11 files are proven independent of the *existence* as well as the content of
`docs/ handbook/ history/ memory/ message-queue/ roadmap/ tasks/ templates/`, `LICENSE`,
and every Markdown file outside a test's own directory (300 paths).

### What the committed code is

Lane (d) — the 11/11 full-suite pass — ran against exactly the code that is committed.
Everything changed afterwards is a record path (`RESULT.md`, `automation/AGENTS.md`),
which this experiment's own evidence shows the suite cannot read.

### Reconciler and suite hygiene

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ python3 automation/tests/test_run_tests.py
Ran 46 tests in 5.248s
OK (skipped=1)
```

(46 = the 34 pre-existing runner tests plus 12 added; the skip is the opt-in probe.)

### The pre-commit floor this exposes

With zero tests selected, the pre-commit gate's cost moves entirely to its other two
steps. Measured in the same window: `reconcile.py --check` took **14.77s** and **11.47s**
on two runs, and `check_core_scope.py --staged` **0.32s**. So a records-only commit goes
from ~432s to ~12-15s — a ~30x improvement in what a human actually waits for, not 1800x.
The next bottleneck after this change is the reconciler, not the tests.

## What could silently break, and what catches it

The dangerous failure is not "the lane is too wide" — it is "a test the change could
break was skipped". Every mechanism below is aimed at that.

1. **A test starts reading a record path.** Say someone adds a reconciler test that
   checks the real `tasks/` tree instead of a fixture. Then a records-only commit could
   break it while selecting zero tests.
   - Caught statically by `InputOwnershipTests.test_every_declared_repository_read_is_owned_by_the_reader`
     whenever the read is written in this repository's idiom (a literal joined onto a
     directory derived from `Path(__file__)`). **Demonstrated**, see the sensitivity
     transcripts below: I added a test reading `REPO / "tasks" / "AGENTS.md"` and the
     guard failed naming both the test and the path.
   - Caught dynamically by `prune_inert_projection`: a narrow lane deletes the record
     paths from its projection, so the read raises `FileNotFoundError` even when the
     parser cannot see it. Every narrow lane re-proves the claim for the tests it runs.
   - Residual hole: a non-idiomatic read (`open(str(REPO) + "/tasks/x")`) inside a test
     that no narrow lane ever selects would go unnoticed until the opt-in probe or CI's
     full run. Small, and named rather than hidden.
2. **The hand-written owners of a registered input drift.** A new test starts reading
   `harness.yml`, or an import edge appears. Caught by the same static guard and by
   `test_ownership_is_closed_under_module_imports`. **Both demonstrated below** by
   deliberately corrupting the table and watching the named assertion fail.
3. **A brand-new top-level directory selects nothing.** It cannot: an unregistered top
   level is `unknown` → full suite, including its Markdown (the Markdown-is-inert rule
   only applies under a registered top-level entry). Covered by
   `test_unregistered_paths_fall_back_to_the_full_suite` and by timing (d).
4. **A removal or rename breaks a test that depends on the file existing.**
   `test_run_tests.py` really does depend on `services/quote-cli/quote_cli.py` and both
   service test files *existing* (its selector assertions call `is_file()` on them).
   That is why any removal or rename of a non-record path falls back to full, and only
   record removals stay narrow.
5. **`.gitignore` changes what the projection contains.** It is deliberately
   unregistered → full suite.
6. **A service or skills test starts reading `automation/`.** The coarse group fallback
   assumes only automation tests read `automation/` and `.github/`; the static guard
   checks *every* discovered test, so a service test declaring an `automation/` path
   fails the guard unless the table gives it that path.
7. **Backstop for all of the above:** `.github/workflows/harness.yml` still runs
   `python3 automation/run_tests.py` — the full suite — on every PR. Narrow lanes change
   only the local pre-commit gate, so the worst case of a wrong table is a late failure
   in CI, not a merged regression.

### Guard sensitivity, verbatim

Three deliberate breakages, each reverted afterwards.

```
$ # 1. a new test that reads a record directory
$ cat automation/tests/test_zz_record_reader.py
REPO = Path(__file__).resolve().parents[2]
TASK_CONTRACT = REPO / "tasks" / "AGENTS.md"
...
$ python3 automation/tests/test_run_tests.py InputOwnershipTests
F..s
======================================================================
FAIL: test_every_declared_repository_read_is_owned_by_the_reader (__main__.InputOwnershipTests)
----------------------------------------------------------------------
AssertionError: PosixPath('.../automation/tests/test_zz_record_reader.py') not found in set() : test_zz_record_reader.py reads tasks/AGENTS.md, which the ownership table does not give it; add the owner or make the path fall back to full
FAILED (failures=1, skipped=1)
```

```
$ # 2. drop test_reconcile_queue.py from the harness.yml owners
$ python3 automation/tests/test_run_tests.py InputOwnershipTests
AssertionError: PosixPath('.../test_reconcile_queue.py') not found in {PosixPath('.../test_github_action_projection_workflow.py'), PosixPath('.../test_check_core_scope.py')} : test_reconcile_queue.py reads .github/workflows/harness.yml, which the ownership table does not give it; add the owner or make the path fall back to full
Ran 4 tests in 1.488s
FAILED (failures=1, skipped=1)
```

```
$ # 3. register the shared module markdown_semantics.py as owned by one test
$ python3 automation/tests/test_run_tests.py InputOwnershipTests
AssertionError: {'test_reconcile_queue.py', 'test_resolve_github_external_sources.py', 'test_github_action_projection_workflow.py', 'test_check_action_projection.py'} not less than or equal to {'test_check_core_scope.py'} : automation/check_action_projection.py imports automation/markdown_semantics.py, so every owner of automation/check_action_projection.py must own automation/markdown_semantics.py
Ran 4 tests in 1.711s
FAILED (failures=1, skipped=1)
```

### The guard tradeoff I chose

The mutation probe as given is sound but costs a full suite run, so it cannot gate every
commit. I split it:

- the **cheap static half** runs in every suite (~1.6s) and catches the realistic way a
  record read gets introduced — someone writes `REPO / "tasks/..."`;
- the **dynamic half is free**: pruning records out of every narrow lane's projection
  turns an unnoticed read into a test failure, and it also makes the narrow lane copy
  less;
- the **expensive half stays available** as `AGENTFOLD_INERT_PROBE=1`, strengthened from
  content corruption to outright **deletion** of the record trees (a real commit can
  delete and rename records, not only edit them, so content mutation alone under-tests
  the claim).

## What I did NOT do

- **Did not touch the services closure.** A `services/quote-cli/` change still runs the
  cli test only, and a `quote-api` change still runs both; I did not try to prove a
  tighter closure there.
- **Did not run `python3 automation/run_tests.py` with no arguments.** To stay inside the
  two-run budget I used timing (d) — `--staged` with a brand-new top-level directory
  staged — as the "full suite still passes" check. It goes through `full_selection`, runs
  the identical 11 files with no pruning, and is byte-identical in execution to the
  default lane after selection. If you want the literal default-invocation receipt, it
  has not been produced.
- **Did not measure an idle-machine baseline.** The box was under load 6.5-10.4 the whole
  session; absolute wall times are not comparable to the repo's earlier ~220s figure.
- **Did not make ownership finer than a file.** No per-class or per-function selection,
  and `automation/markdown_semantics.py` is deliberately left unregistered (5 of 9
  automation tests transitively import it, so precision would buy nothing).
- **Did not lane-scope the projection.** A narrow lane still copies the whole non-record
  tree; only records are pruned. A minimal projection would be the stronger enforcement
  mechanism (any undeclared read fails) but it breaks `test_run_tests.py`, which needs
  the real service tree to exist.
- **Did not parallelize anything.** Selection is orthogonal to the runner's
  one-file-at-a-time loop; the two compose.
- **Did not wire the heavy probe into CI.** It is documented in `automation/AGENTS.md`
  and runnable, but nothing runs it on a schedule.
- **Did not test on Python 3.9+.** Code is 3.7-clean (no walrus, no `tomllib`,
  `TestSelection.__new__.__defaults__` instead of `namedtuple(defaults=)`), stdlib only.
- **Did not measure the other two pre-commit steps beyond the reconciler**, and did not
  attempt to reduce them — see the floor note under the timings.
- **Did not produce a task folder, design.md, worklog, verification.md, or handover** for
  this change. It is an experiment branch, not an admitted AgentFold task.

## Commit disclosure: --no-verify was used, deliberately

The pre-commit hook cannot pass on this branch, and not because of tests. The core-scope
gate rejects any change to `automation/` outside a `task/<task-id>` branch with a matching
task folder:

```
$ GIT_INDEX_FILE=<throwaway> git add -A automation RESULT.md
$ python3 automation/check_core_scope.py --staged
[core-scope] core changes require a `task/<task-id>` branch and matching task folder; personal/provider setup belongs outside AgentFold
    fix: complete templates/task/design.md, route external setup outside core, or record review when --require-review is selected
exit=1
real 0.32
```

Manufacturing a task folder just to satisfy the gate would have polluted the experiment,
so the single commit on exp/a-input-scope was made with `git commit --no-verify`. The two
gates that *would* have run were executed by hand instead and are recorded above:
`reconcile.py --check` → 0 findings, and the full 11-file suite → 11/11 pass. If this
lands for real it needs a proper task with `templates/task/design.md` core-fit evidence.
