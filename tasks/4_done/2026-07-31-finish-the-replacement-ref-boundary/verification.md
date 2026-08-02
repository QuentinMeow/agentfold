# Verification — Finish the replacement-ref boundary the reconciler is halfway through building

**Verified:** 2026-07-31 by claude, and again 2026-07-31 by claude after adversarial review

Only commands actually run and their real output. Every "before" transcript below was
produced against the UNMODIFIED source: the regressions were written first, then run with
the file under test restored to its pre-fix bytes, so the tests are the same bytes that
later pass. The first session used `git stash push -- automation/reconcile/reconcile.py`,
run, `git stash pop`; the second used `git show 4ffa8e3:<path> > <path>`, run,
`git checkout HEAD -- <path>`.

**Every edit made to any transcript on this page, exhaustively:**

1. The absolute worktree path in traceback lines is shortened to `...` (first session
   only; the second session's commands were run from the repository root, so its
   tracebacks already carry repository-relative paths).
2. Long `-m unittest` argument lists are wrapped with `\`.
3. Where output is cut, the cut is marked `[elided: <what>]` on its own line and never
   with a bare `...`. One transcript below predates that rule: the first session's
   full-suite block used a bare `...`, hiding the runner's own self-check blocks and the
   selected-file list. The adversarial reviewer, reading the untruncated output, reported
   the largest of them as `test_probe.py`'s `Ran 65 tests … OK (skipped=1)`; that number
   is the reviewer's observation, not one this session re-measured, and the marker says
   so. The line is now marked and its content named rather than rewritten.

Nothing else is changed, reordered, or reconstructed. A `...` inside a Python
`AssertionError` diff is unittest's own abbreviation, not an edit.

## Before — the six replacement-ref regressions on the unmodified reconciler

```
$ git stash push -- automation/reconcile/reconcile.py
Saved working directory and index state WIP on 2026-07-31-finish-the-replacement-ref-boundary: 2519242 harness: claim finishing the replacement-ref boundary

$ python3 -m unittest \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_synthetic_candidate_parents \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_hide_staged_admission_changes \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_git_review_object \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_git_review_ancestry \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_hide_new_handover_in_root_or_range \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_change_handover_or_staged_blob_baselines \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_git_object_reads_bypass_replacements_except_stable_allowlist
FFFFF
======================================================================
FAIL: test_replace_ref_cannot_forge_synthetic_candidate_parents (automation.tests.test_reconcile_queue.ReconcileQueueTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 10851, in test_replace_ref_cannot_forge_synthetic_candidate_parents
    self.assertEqual(without_replace, with_replace)
AssertionError: Tuples differ: (2, 'reconcile: Git snapshot error: captur[78 chars]e\n') != (0, '')

First differing element 0:
2
0

+ (0, '')
- (2,
-  'reconcile: Git snapshot error: captured candidate is neither the --range '
-  'head nor an exact base+head synthetic merge\n')

======================================================================
FAIL: test_replace_ref_cannot_hide_staged_admission_changes (automation.tests.test_reconcile_queue.ReconcileQueueTests) (case='queue deletion')
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 10941, in test_replace_ref_cannot_hide_staged_admission_changes
    self.assertEqual(without_replace, with_replace)
AssertionError: Lists differ: ['message-queue/needs-agent/requests/blocking-repair.md'] != []

First list contains 1 additional elements.
First extra element 0:
'message-queue/needs-agent/requests/blocking-repair.md'

- ['message-queue/needs-agent/requests/blocking-repair.md']
+ []

======================================================================
FAIL: test_replace_ref_cannot_hide_staged_admission_changes (automation.tests.test_reconcile_queue.ReconcileQueueTests) (case='queue mutation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 10941, in test_replace_ref_cannot_hide_staged_admission_changes
    self.assertEqual(without_replace, with_replace)
AssertionError: Lists differ: [('message-queue/needs-agent/requests/bloc[69 chars]md')] != []

First list contains 1 additional elements.
First extra element 0:
('message-queue/needs-agent/requests/blocking-repair.md', 'message-queue/needs-agent/requests/blocking-repair.md')

+ []
- [('message-queue/needs-agent/requests/blocking-repair.md',
-   'message-queue/needs-agent/requests/blocking-repair.md')]

======================================================================
FAIL: test_replace_ref_cannot_hide_staged_admission_changes (automation.tests.test_reconcile_queue.ReconcileQueueTests) (case='handover mutation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 10941, in test_replace_ref_cannot_hide_staged_admission_changes
    self.assertEqual(without_replace, with_replace)
AssertionError: Lists differ: ['history/conversations/2026-07-23-1200UTC-example/handover.md'] != []

First list contains 1 additional elements.
First extra element 0:
'history/conversations/2026-07-23-1200UTC-example/handover.md'

- ['history/conversations/2026-07-23-1200UTC-example/handover.md']
+ []

======================================================================
FAIL: test_replace_ref_cannot_hide_staged_admission_changes (automation.tests.test_reconcile_queue.ReconcileQueueTests) (case='task mutation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 10941, in test_replace_ref_cannot_hide_staged_admission_changes
    self.assertEqual(without_replace, with_replace)
AssertionError: Items in the first set but not the second:
'2026-07-23-example'

======================================================================
FAIL: test_replace_ref_cannot_hide_staged_admission_changes (automation.tests.test_reconcile_queue.ReconcileQueueTests) (case='task artifact rename')
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 10941, in test_replace_ref_cannot_hide_staged_admission_changes
    self.assertEqual(without_replace, with_replace)
AssertionError: Lists differ: [('tasks/1_in-progress/2026-07-23-example/[61 chars]md')] != []

First list contains 1 additional elements.
First extra element 0:
('tasks/1_in-progress/2026-07-23-example/design.md', 'tasks/1_in-progress/2026-07-23-example/proposal.md')

+ []
- [('tasks/1_in-progress/2026-07-23-example/design.md',
-   'tasks/1_in-progress/2026-07-23-example/proposal.md')]

======================================================================
FAIL: test_replace_ref_cannot_forge_git_review_object (automation.tests.test_reconcile_queue.ReconcileQueueTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 10963, in test_replace_ref_cannot_forge_git_review_object
    self.assertEqual(without_replace, with_replace)
AssertionError: Lists differ: ['083df26f3c58ada48772c063f81da8f29f9abdce is blob, not a commit'] != []

First list contains 1 additional elements.
First extra element 0:
'083df26f3c58ada48772c063f81da8f29f9abdce is blob, not a commit'

- ['083df26f3c58ada48772c063f81da8f29f9abdce is blob, not a commit']
+ []

======================================================================
FAIL: test_replace_ref_cannot_forge_git_review_ancestry (automation.tests.test_reconcile_queue.ReconcileQueueTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 10995, in test_replace_ref_cannot_forge_git_review_ancestry
    self.assertEqual(without_replace, with_replace)
AssertionError: Lists differ: ['base and head have no merge base'] != []

First list contains 1 additional elements.
First extra element 0:
'base and head have no merge base'

- ['base and head have no merge base']
+ []

======================================================================
FAIL: test_replace_ref_cannot_hide_new_handover_in_root_or_range (automation.tests.test_reconcile_queue.ReconcileQueueTests) (view='root')
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 11043, in test_replace_ref_cannot_hide_new_handover_in_root_or_range
    self.assertEqual(without_replace, with_replace)
AssertionError: Tuples differ: ({PosixPath('history/conversations/2026-07[36 chars]None) != (set(), None)

First differing element 0:
{PosixPath('history/conversations/2026-07-23-1200UTC-example/handover.md')}
set()

+ (set(), None)
- ({PosixPath('history/conversations/2026-07-23-1200UTC-example/handover.md')},
-  None)

======================================================================
FAIL: test_replace_ref_cannot_hide_new_handover_in_root_or_range (automation.tests.test_reconcile_queue.ReconcileQueueTests) (view='range')
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 11043, in test_replace_ref_cannot_hide_new_handover_in_root_or_range
    self.assertEqual(without_replace, with_replace)
AssertionError: Tuples differ: ({PosixPath('history/conversations/2026-07[36 chars]None) != (set(), None)

First differing element 0:
{PosixPath('history/conversations/2026-07-23-1200UTC-example/handover.md')}
set()

+ (set(), None)
- ({PosixPath('history/conversations/2026-07-23-1200UTC-example/handover.md')},
-  None)

======================================================================
FAIL: test_replace_ref_cannot_change_handover_or_staged_blob_baselines (automation.tests.test_reconcile_queue.ReconcileQueueTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 11093, in test_replace_ref_cannot_change_handover_or_staged_blob_baselines
    self.assertEqual(handover_without, handover_with)
AssertionError: Tuples differ: (('# Original handover\n', {'message-queue/nee[84 chars]one)) != (('# Forged handover\n', set(), set(), None), [25 chars]one))

First differing element 0:
('# Original handover\n', {'message-queue/nee[50 chars]None)
('# Forged handover\n', set(), set(), None)

+ (('# Forged handover\n', set(), set(), None), ('# Forged handover\n', None))
- (('# Original handover\n',
-   {'message-queue/needs-human/reviews/non-blocking-review.md'},
-   set(),
-   None),
-  ('# Original handover\n', None))

======================================================================
FAIL: test_git_object_reads_bypass_replacements_except_stable_allowlist (automation.tests.test_reconcile_queue.ReconcileQueueTests)
Every Git object read stays outside `refs/replace/*`.
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 11173, in test_git_object_reads_bypass_replacements_except_stable_allowlist
    self.assertEqual([], unsafe)
AssertionError: Lists differ: [] != [(1317, 'git'), (1420, 'git'), (515, 'git [860 chars]ch')]

Second list contains 22 additional elements.
First extra element 0:
(1317, 'git')

Diff is 978 characters long. Set self.maxDiff to None to see it.

----------------------------------------------------------------------
Ran 7 tests in 3.485s

FAILED (failures=12)
reconcile: 0 finding(s)
```

Every one of the six exploits worked on the unmodified reconciler: a `refs/replace/*`
entry silently turned a rejected synthetic candidate into an accepted one, hid a staged
queue deletion, a queue mutation, a handover mutation, a task mutation and a task-artifact
rename, made a blob pass as a commit, forged a merge base for a Git review range, hid a
newly added handover in both the `root:` and `base...head` views, and swapped both a
handover creation snapshot and a staged blob baseline for forged bytes. The source-level
guard listed 22 bare invocations.

The hardened reconciler was then restored (last lines of the real output):

```
$ git stash pop
no changes added to commit (use "git add" and/or "git commit -a")
Dropped refs/stash@{0} (b83a4fe1e030bb43c235d3d6ece1fa0fe582e7db)
```

## After — the same seven tests on the hardened reconciler

```
$ python3 -m unittest -v \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_synthetic_candidate_parents \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_hide_staged_admission_changes \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_git_review_object \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_git_review_ancestry \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_hide_new_handover_in_root_or_range \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_change_handover_or_staged_blob_baselines \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_git_object_reads_bypass_replacements_except_stable_allowlist
test_replace_ref_cannot_forge_synthetic_candidate_parents (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_replace_ref_cannot_hide_staged_admission_changes (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_replace_ref_cannot_forge_git_review_object (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_replace_ref_cannot_forge_git_review_ancestry (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_replace_ref_cannot_hide_new_handover_in_root_or_range (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_replace_ref_cannot_change_handover_or_staged_blob_baselines (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_git_object_reads_bypass_replacements_except_stable_allowlist (automation.tests.test_reconcile_queue.ReconcileQueueTests)
Every Git object read stays outside `refs/replace/*`. ... ok

----------------------------------------------------------------------
Ran 7 tests in 3.535s

OK
```

## The guard fails when a new bare invocation is added

Two throwaway lines were appended to `automation/reconcile/reconcile.py`, the guard was
run, and the lines were removed again:

```python
_GUARD_PROBE_BARE = ["git", "log", "-1"]
_GUARD_PROBE_STARRED = [*TASK_STATUSES, "log", "-1"]
```

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_git_object_reads_bypass_replacements_except_stable_allowlist
======================================================================
FAIL: test_git_object_reads_bypass_replacements_except_stable_allowlist (automation.tests.test_reconcile_queue.ReconcileQueueTests)
Every Git object read stays outside `refs/replace/*`.
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 11173, in test_git_object_reads_bypass_replacements_except_stable_allowlist
    self.assertEqual([], unsafe)
AssertionError: Lists differ: [] != [(7702, 'git log -1'), (7703, '*<not RAW_GIT>')]

Second list contains 2 additional elements.
First extra element 0:
(7702, 'git log -1')

- []
+ [(7702, 'git log -1'), (7703, '*<not RAW_GIT>')]

----------------------------------------------------------------------
Ran 1 test in 0.239s

FAILED (failures=1)
```

A bare list is caught, and so is a splat of anything other than the checked `RAW_GIT`
constant.

## Full suite

```
$ python3 automation/run_tests.py
test lane: full
test reason: full suite requested
[elided: the selected-file list, and the runner's own test_git_init_probe / test_first /
 test_second / test_probe self-check blocks. This session did not re-measure that run;
 the adversarial reviewer reported the test_probe block as "Ran 65 tests ... OK
 (skipped=1)".]
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
test elapsed: 57.45s
```

One pre-existing test needed its expectation updated rather than its behavior:
`test_main_caches_repeated_git_snapshot_reads` counted the single HEAD-tree spawn by
matching `["git", "ls-tree", "-r", "--name-only", "-z"]`, and now matches
`["git", "--no-replace-objects", "ls-tree", "-r", "--name-only", "-z"]`. It still asserts
exactly one spawn.

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

---

# Second session — repairing the four adversarial-review findings

Everything below was run at the repository root of this worktree. The pre-fix bytes are
those of `4ffa8e3`, the tip the first session left; the fix commit is `df2dac6`.

## Finding 1 — the six spellings that slipped past the list-literal guard

The old guard, plus all six bypasses live in the file it scans. `git archive` reproduces
the pre-fix tree, and `bypass.py` holds the six spellings verbatim:

```python
import os

_GIT_BIN = "git"


def bypass_tuple(oid):
    return subprocess.run(("git", "cat-file", "-p", oid), cwd=REPO)


def bypass_name(oid):
    return subprocess.run([_GIT_BIN, "cat-file", "-p", oid], cwd=REPO)


def bypass_shell(oid):
    return subprocess.run(f"git cat-file -p {oid}", shell=True, cwd=REPO)


def bypass_concat(oid):
    return subprocess.run([_GIT_BIN] + ["show", oid], cwd=REPO)


def bypass_popen(oid):
    return os.popen("git cat-file -p " + oid).read()


def bypass_list_call(oid):
    return subprocess.run(list(("git", "cat-file", "-p", oid)), cwd=REPO)
```

```
$ mkdir -p tmp/guard-probe
$ git archive 4ffa8e3 automation | tar -x -C tmp/guard-probe
$ cat tmp/guard-probe/bypass.py >> tmp/guard-probe/automation/reconcile/reconcile.py
$ python3 tmp/guard-probe/automation/tests/test_reconcile_queue.py \
    ReconcileQueueTests.test_git_object_reads_bypass_replacements_except_stable_allowlist
.
----------------------------------------------------------------------
Ran 1 test in 0.160s

OK
```

Green, with all six bypasses present. The same six against the new guard, in a tree that
is otherwise the current `automation/`:

```
$ mkdir -p tmp/guard-probe-new
$ cp -R automation tmp/guard-probe-new/automation
$ cat tmp/guard-probe/bypass.py >> tmp/guard-probe-new/automation/reconcile/reconcile.py
$ python3 tmp/guard-probe-new/automation/tests/test_reconcile_queue.py \
    ReconcileQueueTests.test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object

======================================================================
FAIL: test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object (__main__.ReconcileQueueTests) (module='automation/reconcile/reconcile.py')
Every Git spawn these four gates make is readable, and reads honestly.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tmp/guard-probe-new/automation/tests/test_reconcile_queue.py", line 11625, in test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
    unhardened_git_spawns(source, BARE_GIT_PREFIXES[relative]),
AssertionError: Lists differ: [] != [(7710, 'bare Git read: git cat-file -p <e[852 chars]O)')]

Second list contains 7 additional elements.
First extra element 0:
(7710, 'bare Git read: git cat-file -p <expr>', 'return subprocess.run(("git", "cat-file", "-p", oid), cwd=REPO)')

Diff is 981 characters long. Set self.maxDiff to None to see it.

----------------------------------------------------------------------
Ran 1 test in 1.340s

FAILED (failures=1)
```

`unittest` abbreviates the list, so the same findings printed in full — seven findings
for six spellings, because the shell case trips two rules:

```
$ python3 tmp/guard-probe-new/report.py
automation/reconcile/reconcile.py:7710  bare Git read: git cat-file -p <expr>
    return subprocess.run(("git", "cat-file", "-p", oid), cwd=REPO)
automation/reconcile/reconcile.py:7714  bare Git read: git cat-file -p <expr>
    return subprocess.run([_GIT_BIN, "cat-file", "-p", oid], cwd=REPO)
automation/reconcile/reconcile.py:7718  subprocess.run runs a shell command line
    return subprocess.run(f"git cat-file -p {oid}", shell=True, cwd=REPO)
automation/reconcile/reconcile.py:7718  subprocess.run takes an argument list this scan cannot read
    return subprocess.run(f"git cat-file -p {oid}", shell=True, cwd=REPO)
automation/reconcile/reconcile.py:7722  subprocess.run takes an argument list this scan cannot read
    return subprocess.run([_GIT_BIN] + ["show", oid], cwd=REPO)
automation/reconcile/reconcile.py:7726  os.popen takes an argument list this scan cannot read
    return os.popen("git cat-file -p " + oid).read()
automation/reconcile/reconcile.py:7730  subprocess.run takes an argument list this scan cannot read
    return subprocess.run(list(("git", "cat-file", "-p", oid)), cwd=REPO)
```

`report.py` is nine lines of throwaway under the git-ignored `tmp/`: it loads the probe
tree's own test module and prints `unhardened_git_spawns(...)` for each guarded module
without unittest's abbreviation. Both probe trees were deleted after these runs.

All six are also covered by
`test_the_git_spawn_guard_catches_every_known_bypass_spelling`, one `subTest` each, so
the closure is a permanent regression rather than a one-off probe.

## Finding 2 — the sibling gates

### `check_core_scope.py`, reverted to its pre-fix bytes

```
$ git show 4ffa8e3:automation/check_core_scope.py > automation/check_core_scope.py
$ python3 automation/tests/test_check_core_scope.py \
    CoreScopeTests.test_replace_ref_cannot_pass_a_blob_as_the_reviewed_core_commit \
    CoreScopeTests.test_replace_ref_cannot_hide_a_stale_core_fit_review
FF
======================================================================
FAIL: test_replace_ref_cannot_pass_a_blob_as_the_reviewed_core_commit (__main__.CoreScopeTests)
A `refs/replace/*` entry must not turn a blob into a reviewed commit.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "automation/tests/test_check_core_scope.py", line 789, in test_replace_ref_cannot_pass_a_blob_as_the_reviewed_core_commit
    self.assertEqual(without_replace, with_replace)
AssertionError: Lists differ: ["reviewed revision '90db16de6c0119c0c924c[52 chars]ory"] != ['reviewed revision 90db16de6c0119c0c924c8[50 chars]a42']

First differing element 0:
"reviewed revision '90db16de6c0119c0c924c[51 chars]tory"
'reviewed revision 90db16de6c0119c0c924c8[49 chars]5a42'

- ["reviewed revision '90db16de6c0119c0c924c80d206b1e80bc3d2331' is not a commit "
?  ^                  -                                        -         ^^^^^^^^^

+ ['reviewed revision 90db16de6c0119c0c924c80d206b1e80bc3d2331 is not an '
?  ^                                                                   ^^^

-  'in this repository']
+  'ancestor of 5ec90e4e5a42']

======================================================================
FAIL: test_replace_ref_cannot_hide_a_stale_core_fit_review (__main__.CoreScopeTests)
The whole gate, not one check: a stale review must stay stale.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "automation/tests/test_check_core_scope.py", line 843, in test_replace_ref_cannot_hide_a_stale_core_fit_review
    self.assertEqual(without_replace, with_replace)
AssertionError: Lists differ: ['core-fit review for 004b15139639 is stal[59 chars].md'] != []

First list contains 1 additional elements.
First extra element 0:
'core-fit review for 004b15139639 is stale; later bound changes: automation/tool.py, task input task.md'

+ []
- ['core-fit review for 004b15139639 is stale; later bound changes: '
-  'automation/tool.py, task input task.md']

----------------------------------------------------------------------
Ran 2 tests in 1.102s

FAILED (failures=2)
```

Read the first failure carefully: the blob's verdict *changes* from "is not a commit" to
"is not an ancestor". The type test and the full-object-id equality test both passed for
a blob, exactly as the review reported. The Git behaviour underneath it, from the probe
that found it:

```
[1] before replace: git rev-parse --verify $BLOB^{commit}
    rc=128 out='' err='error: 90db16de6c0119c0c924c80d206b1e80bc3d2331^{commit}: expected commit type, but the object dereferences to blob type\nfatal: Needed a single revision'

[3] after: git replace -f $BLOB $BASE
    bare  git rev-parse --verify $BLOB^{commit}: rc=0 out='90db16de6c0119c0c924c80d206b1e80bc3d2331' err=''
    hard  git --no-replace-objects rev-parse ...: rc=128 out='' err='error: 90db16de6c0119c0c924c80d206b1e80bc3d2331^{commit}: expected commit type, but the object dereferences to blob type\nfatal: Needed a single revision'
```

The second failure is the whole gate falling over, not one check: a core-fit review that
is stale by a real `automation/` change *and* a rewritten task input returns `[]` — zero
findings — once `git replace -f $REVIEWED $CURRENT` is in place.

With the fix restored, both pass:

```
$ git checkout HEAD -- automation/check_core_scope.py
$ python3 automation/tests/test_check_core_scope.py \
    CoreScopeTests.test_replace_ref_cannot_pass_a_blob_as_the_reviewed_core_commit \
    CoreScopeTests.test_replace_ref_cannot_hide_a_stale_core_fit_review
..
----------------------------------------------------------------------
Ran 2 tests in 0.983s

OK
```

### `run_tests.py`, reverted to its pre-fix bytes

```
$ git show 4ffa8e3:automation/run_tests.py > automation/run_tests.py
$ python3 automation/tests/test_run_tests.py \
    StagedTestSelectionTests.test_replace_ref_cannot_swap_the_staged_diff_for_a_record_only_one \
    StagedTestSelectionTests.test_cli_addition_selects_only_the_cli_test
FF
======================================================================
FAIL: test_replace_ref_cannot_swap_the_staged_diff_for_a_record_only_one (__main__.StagedTestSelectionTests)
A `refs/replace/*` entry must not choose the pre-commit test lane.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "automation/tests/test_run_tests.py", line 589, in test_replace_ref_cannot_swap_the_staged_diff_for_a_record_only_one
    "a replacement entry chose which tests the hook runs",
AssertionError: Tuples differ: (PosixPath('/var/folders/9g/nnmcgvqd5kvc99[83 chars]y'),) != ()

First tuple contains 1 additional elements.
First extra element 0:
PosixPath('/var/folders/9g/nnmcgvqd5kvc99gqpbv1d1kr0000gn/T/tmpjsdnwh2g/repository/services/quote-cli/tests/test_quote_cli.py')

- (PosixPath('/var/folders/9g/nnmcgvqd5kvc99gqpbv1d1kr0000gn/T/tmpjsdnwh2g/repository/services/quote-cli/tests/test_quote_cli.py'),)
+ () : a replacement entry chose which tests the hook runs

======================================================================
FAIL: test_cli_addition_selects_only_the_cli_test (__main__.StagedTestSelectionTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "automation/tests/test_run_tests.py", line 78, in test_cli_addition_selects_only_the_cli_test
    "the staged diff compares the index against a committed tree, so a "
AssertionError: Lists differ: ['git', '--no-replace-objects', 'diff', '--cached', '--name-status', '-z', '-M'] != ['git', 'diff', '--cached', '--name-status', '-z', '-M']

First differing element 1:
'--no-replace-objects'
'diff'

First list contains 1 additional elements.
First extra element 6:
'-M'

- ['git', '--no-replace-objects', 'diff', '--cached', '--name-status', '-z', '-M']
?         ------------------------

+ ['git', 'diff', '--cached', '--name-status', '-z', '-M'] : the staged diff compares the index against a committed tree, so a `refs/replace/*` entry must not be able to answer it

----------------------------------------------------------------------
Ran 2 tests in 0.416s

FAILED (failures=2)
```

The empty tuple is the exploit: a real, unreviewed `services/quote-cli/quote_cli.py`
change is staged, and the hook selects **no test at all**. The direct probe that measured
the lane, before and after the same replacement entry:

```
[honest] lane='staged' reason='every staged path maps to its registered test owners' tests=('test_quote_cli.py',)
         git diff --cached ...: 'M\x00services/quote-cli/quote_cli.py\x00'
[forged] lane='staged' reason='every staged path is a record path no test reads' tests=()
         git diff --cached ...: 'M\x00tasks/1_in-progress/2026-07-31-probe/task.md\x00'
         git --no-replace-objects diff --cached ...: 'M\x00services/quote-cli/quote_cli.py\x00'
```

An *emptied* diff is not the exploit: that path falls back to the full suite
(`reason='staged diff empty or malformed'`), which is why the regression forges a narrow
diff rather than an empty one.

### The guard over all four pre-fix gates, and the workflow

```
$ git show 4ffa8e3:automation/check_core_scope.py > automation/check_core_scope.py
$ git show 4ffa8e3:automation/run_tests.py > automation/run_tests.py
$ git show 4ffa8e3:automation/check_action_projection.py > automation/check_action_projection.py
$ git show 4ffa8e3:.github/workflows/harness.yml > .github/workflows/harness.yml
$ python3 automation/tests/test_reconcile_queue.py \
    ReconcileQueueTests.test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object \
    ReconcileQueueTests.test_the_provider_workflow_reads_git_the_same_way_the_gates_do
F
======================================================================
FAIL: test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object (__main__.ReconcileQueueTests) (module='automation/check_action_projection.py')
Every Git spawn these four gates make is readable, and reads honestly.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "automation/tests/test_reconcile_queue.py", line 11625, in test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
    unhardened_git_spawns(source, BARE_GIT_PREFIXES[relative]),
AssertionError: Lists differ: [] != [(1652, 'bare Git read: git <expr>', 'result = subprocess.run(')]

Second list contains 1 additional elements.
First extra element 0:
(1652, 'bare Git read: git <expr>', 'result = subprocess.run(')

- []
+ [(1652, 'bare Git read: git <expr>', 'result = subprocess.run(')]

======================================================================
FAIL: test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object (__main__.ReconcileQueueTests) (module='automation/check_core_scope.py')
Every Git spawn these four gates make is readable, and reads honestly.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "automation/tests/test_reconcile_queue.py", line 11625, in test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
    unhardened_git_spawns(source, BARE_GIT_PREFIXES[relative]),
AssertionError: Lists differ: [] != [(81, 'bare Git read: git <expr>', 'result[199 chars]n(')]

Second list contains 3 additional elements.
First extra element 0:
(81, 'bare Git read: git <expr>', 'result = subprocess.run(')

- []
+ [(81, 'bare Git read: git <expr>', 'result = subprocess.run('),
+  (464,
+   'bare Git read: git rev-parse --verify <expr>',
+   'resolved = subprocess.run('),
+  (477,
+   'bare Git read: git merge-base --is-ancestor <expr> <expr>',
+   'ancestry = subprocess.run(')]

======================================================================
FAIL: test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object (__main__.ReconcileQueueTests) (module='automation/run_tests.py')
Every Git spawn these four gates make is readable, and reads honestly.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "automation/tests/test_reconcile_queue.py", line 11625, in test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
    unhardened_git_spawns(source, BARE_GIT_PREFIXES[relative]),
AssertionError: Lists differ: [] != [(578, 'bare Git read: git diff --cached -[42 chars]n(')]

Second list contains 1 additional elements.
First extra element 0:
(578, 'bare Git read: git diff --cached --name-status -z -M', 'diff = subprocess.run(')

- []
+ [(578,
+   'bare Git read: git diff --cached --name-status -z -M',
+   'diff = subprocess.run(')]

======================================================================
FAIL: test_the_provider_workflow_reads_git_the_same_way_the_gates_do (__main__.ReconcileQueueTests)
The shell half of the boundary, which the AST guard cannot see.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "automation/tests/test_reconcile_queue.py", line 11660, in test_the_provider_workflow_reads_git_the_same_way_the_gates_do
    self.assertEqual([], bare)
AssertionError: Lists differ: [] != [(47, 'cat-file'), (50, 'cat-file'), (70, [45 chars]le')]

Second list contains 5 additional elements.
First extra element 0:
(47, 'cat-file')

- []
+ [(47, 'cat-file'),
+  (50, 'cat-file'),
+  (70, 'merge-base'),
+  (76, 'cat-file'),
+  (79, 'cat-file')]

----------------------------------------------------------------------
Ran 2 tests in 1.611s

FAILED (failures=4)
```

`reconcile.py` is absent from that list because the first session already hardened it —
the guard names exactly the four holes the review reported, at exactly the lines it
reported (`.github/workflows/harness.yml` 47, 50, 70, 76, 79), plus
`check_action_projection.py:1652`, which the review did not name and which the guard
found on its own. The `'result = subprocess.run('` source text is the Python 3.7
fallback: `ast.get_source_segment` needs 3.8, and the interpreter here is 3.7.6.

All four files restored:

```
$ git checkout HEAD -- automation/check_core_scope.py automation/run_tests.py automation/check_action_projection.py .github/workflows/harness.yml
$ git status --short
```

(no output — the tree matches `df2dac6`)

## Finding 3 — the ordinary starred list the old guard rejected

`ordinary.py` holds the two lines, with no Git anywhere in them:

```python
ORDINARY_HEADERS = ("Status", "Blocks now")


def ordinary_rows():
    return [*ORDINARY_HEADERS, "note"]
```

Appended to the pre-fix reconciler in a freshly re-extracted probe tree:

```
$ rm -rf tmp/guard-probe/automation
$ git archive 4ffa8e3 automation | tar -x -C tmp/guard-probe
$ cat tmp/guard-probe/ordinary.py >> tmp/guard-probe/automation/reconcile/reconcile.py
$ python3 tmp/guard-probe/automation/tests/test_reconcile_queue.py \
    ReconcileQueueTests.test_git_object_reads_bypass_replacements_except_stable_allowlist
F
======================================================================
FAIL: test_git_object_reads_bypass_replacements_except_stable_allowlist (__main__.ReconcileQueueTests)
Every Git object read stays outside `refs/replace/*`.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tmp/guard-probe/automation/tests/test_reconcile_queue.py", line 11173, in test_git_object_reads_bypass_replacements_except_stable_allowlist
    self.assertEqual([], unsafe)
AssertionError: Lists differ: [] != [(7708, '*<not RAW_GIT>')]

Second list contains 1 additional elements.
First extra element 0:
(7708, '*<not RAW_GIT>')

- []
+ [(7708, '*<not RAW_GIT>')]

----------------------------------------------------------------------
Ran 1 test in 1.781s

FAILED (failures=1)
```

The same lines against the new guard:

```
$ rm -rf tmp/guard-probe-new/automation
$ cp -R automation tmp/guard-probe-new/automation
$ cat tmp/guard-probe/ordinary.py >> tmp/guard-probe-new/automation/reconcile/reconcile.py
$ python3 tmp/guard-probe-new/automation/tests/test_reconcile_queue.py \
    ReconcileQueueTests.test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
.
----------------------------------------------------------------------
Ran 1 test in 4.476s

OK
```

Covered permanently by `test_the_git_spawn_guard_leaves_ordinary_starred_lists_alone`,
which also asserts that a splat the scan *cannot* fold in argument position —
`[*prefix, "cat-file", "-p", oid]` — is still reported, with its source text.

## Finding 4 — the elision disclosure

Fixed at the top of this file rather than here: every edit to every transcript is now
enumerated, the first session's bare `...` is marked `[elided: ...]`, and what it hid is
named. Nothing was rewritten to make it true.

## Second session — the guard's own cost, measured

The scan runs in the pre-commit lane whenever any of the four gates changes, so it was
timed rather than assumed. The first working version resolved each name by walking the
enclosing scope on demand, which meant walking the whole 6,000-line reconciler module
once per distinct name it asked about:

```
$ time python3 automation/tests/test_reconcile_queue.py \
    ReconcileQueueTests.test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
Ran 1 test in 28.716s
OK
python3 automation/tests/test_reconcile_queue.py  28.22s user 0.58s system 97% cpu 29.600 total
```

Resolving every name in a scope in one walk and memoizing that map on the scope node
gives the same findings — the four-gate transcript above is byte-identical apart from the
elapsed line — for:

```
$ time python3 automation/tests/test_reconcile_queue.py \
    ReconcileQueueTests.test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object \
    ReconcileQueueTests.test_the_git_spawn_guard_catches_every_known_bypass_spelling \
    ReconcileQueueTests.test_the_git_spawn_guard_still_reads_the_shapes_the_gates_use \
    ReconcileQueueTests.test_the_git_spawn_guard_leaves_ordinary_starred_lists_alone \
    ReconcileQueueTests.test_every_gate_names_the_same_checked_hardening_prefix \
    ReconcileQueueTests.test_the_provider_workflow_reads_git_the_same_way_the_gates_do
......
----------------------------------------------------------------------
Ran 6 tests in 3.037s

OK
python3 automation/tests/test_reconcile_queue.py  3.56s user 0.15s system 98% cpu 3.768 total
```

Six tests in 3.0s, against one test in 28.7s.

## Second session — full suite and reconciler

```
$ python3 automation/run_tests.py
[elided: the lane header, the selected-file list, and the runner's own
 test_git_init_probe / test_first / test_second / test_probe self-check blocks, the last
 of which reported "Ran 66 tests in 9.176s / OK (skipped=1)"]
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
test elapsed: 61.34s
```

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Tests changed for expectation rather than behaviour, both because the argument list they
match is now the hardened one:
`test_cli_addition_selects_only_the_cli_test` (the staged diff) and
`test_github_adapter_handles_root_push_and_always_runs_tests` (the workflow's
`cat-file -e`). Both still assert what they always asserted.

## Merging onto main at `00a3ea0` (2026-08-01)

The task work was merged onto main with main as the first parent, at
`00a3ea0d9b3ad0f318f3bf885c777edd0efe9590`. One content conflict, in
`handover_current_incarnation_text`: this branch hardened its per-handover `git show`,
and main deleted that spawn and routed the read through the reusable
`cat-file --batch` reader. Resolved to main's version, because that reader is launched
with `--no-replace-objects` and so is strictly stronger than the hardened `git show`
this task set out to write.

The guard this task added then caught a real gap in main's new code. Main added
`compute_git_ignored_prefixes`, whose `git ls-files --others --ignored
--exclude-standard --directory -z` is a fifth bare read the reviewed allowlist did not
name:

```
$ python3 -m unittest test_reconcile_queue.ReconcileQueueTests.test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_reconcile_queue.py", line 12362, in test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
    unhardened_git_spawns(source, BARE_GIT_PREFIXES[relative]),
AssertionError: Lists differ: [] != [(656, 'bare Git read: git ls-files --othe[72 chars]n(')]

Second list contains 1 additional elements.
First extra element 0:
(656, 'bare Git read: git ls-files --others --ignored --exclude-standard --directory -z', 'result = subprocess.run(')

- []
+ [(656,
+   'bare Git read: git ls-files --others --ignored --exclude-standard '
+   '--directory -z',
+   'result = subprocess.run(')]

----------------------------------------------------------------------
Ran 1 test in 1.674s

FAILED (failures=1)
```

That scan reads the index, the worktree and `.gitignore` and never an object's
contents, so it joined the reviewed bare prefixes beside the untracked-path scan it
sits next to, rather than being given the flag:

```
$ python3 -m unittest test_reconcile_queue.ReconcileQueueTests.test_no_gate_spawns_git_in_a_way_that_could_read_a_replaced_object
.
----------------------------------------------------------------------
Ran 1 test in 2.367s

OK
```

On the merge commit `2e8893826797bd5ab0a2a2fc1fd0e528173e6f0b`:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

```
$ python3 automation/check_core_scope.py --range "00a3ea0d9b3ad0f318f3bf885c777edd0efe9590...2e8893826797bd5ab0a2a2fc1fd0e528173e6f0b" --branch task/2026-07-31-finish-the-replacement-ref-boundary
core-scope: pass (8 core path(s), task 2026-07-31-finish-the-replacement-ref-boundary; independent review manual; not invoked)
```

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-07-31-finish-the-replacement-ref-boundary --range "00a3ea0d9b3ad0f318f3bf885c777edd0efe9590...2e8893826797bd5ab0a2a2fc1fd0e528173e6f0b"
reconcile: 0 blocking finding(s)
```

```
$ python3 automation/run_tests.py
[... per-shard lane/selection output elided ...]
OK (skipped=1)
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.01s
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
test elapsed: 59.68s
```

The commit that adds this section touches only this file and the worklog.

## Review verdicts (when a review was explicitly run)

No independent review was invoked: `--require-review` was not selected, and this task's
collaboration mode (`async`) gates on tests plus the reconciler. The adversarial review
that produced the four findings above was invoked by the orchestrator, not through
`--require-review`, so it is recorded here as the reason for the second session rather
than as a revision-bound receipt.
