# Verification — Finish the replacement-ref boundary the reconciler is halfway through building

**Verified:** 2026-07-31 by claude

Only commands actually run and their real output. Every "before" transcript below was
produced against the UNMODIFIED reconciler: the regressions were written first, then run
with `automation/reconcile/reconcile.py` restored to the tree at the claim commit
(`git stash push -- automation/reconcile/reconcile.py`, run, `git stash pop`), so the
tests are the same bytes that later pass. The only edit to any transcript is that the
absolute worktree path in traceback lines is shortened to `...`, and the long `-m unittest`
argument lists are wrapped with `\`.

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

## Review verdicts (when a review was explicitly run)

No independent review was invoked: `--require-review` was not selected, and this task's
collaboration mode (`async`) gates on tests plus the reconciler.
