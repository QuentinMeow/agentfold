# Verification — stop reading a merge parent edge as a lifecycle step

**Verified:** 2026-07-25 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Reported reproduction, before the fix

Run on `main` at 74b9d0dfd98f13c17124a9b40d955ff9461e0572, clean tree, unmodified code.

```
$ python3 automation/reconcile/reconcile.py --check --range fef828849653ece624ecf5a9d2b92e7416fcf7f1...74b9d0dfd98f13c17124a9b40d955ff9461e0572
[task-admission] tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md: task snapshot 74b9d0dfd98f13c17124a9b40d955ff9461e0572 violated lifecycle topology: new task:2026-07-25-fix-handover-projection-code-span-copy was created directly in 1_in-progress
    fix: create new tasks in 0_backlog, then claim and move them through the lifecycle
reconcile: 1 finding(s)
exit=1
```

## Mechanism confirmed before changing code

```
$ git rev-list --parents -n 1 74b9d0d
74b9d0dfd98f13c17124a9b40d955ff9461e0572 fef828849653ece624ecf5a9d2b92e7416fcf7f1 35582c25f00a0c7bd43db69aa9a27b59c6bacf83
$ git merge-base 35582c2 fef8288
17c1e16138632fe914e5ee69882eb26e9f4890c7
$ git ls-tree -r --name-only 35582c2 | grep fix-handover-projection || echo "(none)"
(none)
$ git ls-tree -r --name-only fef8288 | grep fix-handover-projection || echo "(none)"
tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/plan.md
tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md
tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/worklog.md
$ git log --oneline --all --diff-filter=A -- 'tasks/*/2026-07-25-fix-handover-projection-code-span-copy/task.md'
b4c1ec5 harness: file the blocked handover projection repair
$ git log --oneline -1 0456738
0456738 harness: claim the handover projection code-span repair
$ git log --oneline -1 17c1e16
17c1e16 harness: claim the markdown co-change mining task
```

The task was filed in `0_backlog` by b4c1ec5 and claimed by 0456738, both after
17c1e16, so the second parent's tree carries no record of it.

## Same reproduction after the fix

`--range` binds the check to the captured head or an exact base-plus-head synthetic
merge (`validate_range_candidate`), which is the shape a provider merge ref has, so the
fixed code was evaluated against the same range through two synthetic candidates that
differ only in whether the repair is present.

```
$ export GIT_INDEX_FILE=/Users/quentinmiao/code/ai-harness/tmp/merge-parent-topology/synthetic.index
$ git read-tree 74b9d0dfd98f13c17124a9b40d955ff9461e0572
$ git update-index --cacheinfo 100644,$(git rev-parse e805812:automation/reconcile/reconcile.py),automation/reconcile/reconcile.py
$ git update-index --cacheinfo 100644,$(git rev-parse e805812:automation/tests/test_reconcile_queue.py),automation/tests/test_reconcile_queue.py
$ TREE=$(git write-tree)
$ unset GIT_INDEX_FILE
$ git commit-tree $TREE -p fef828849653ece624ecf5a9d2b92e7416fcf7f1 -p 74b9d0dfd98f13c17124a9b40d955ff9461e0572 -m "probe: the pull request 13 merge with only the topology fix applied"
79c9e859c3650cc726593f480135074a81631599
$ git rev-list --parents -n 1 79c9e859c3650cc726593f480135074a81631599
79c9e859c3650cc726593f480135074a81631599 fef828849653ece624ecf5a9d2b92e7416fcf7f1 74b9d0dfd98f13c17124a9b40d955ff9461e0572
$ git diff --stat 74b9d0dfd98f13c17124a9b40d955ff9461e0572 79c9e859c3650cc726593f480135074a81631599
 automation/reconcile/reconcile.py        |  16 ++-
 automation/tests/test_reconcile_queue.py | 231 +++++++++++++++++++++++++++++++
 2 files changed, 246 insertions(+), 1 deletion(-)
```

```
$ git worktree add --detach "$PROBE" 79c9e859c3650cc726593f480135074a81631599
Preparing worktree (detached HEAD 79c9e85)
HEAD is now at 79c9e85 probe: the pull request 13 merge with only the topology fix applied
$ git -C "$PROBE" status --short --untracked-files=all | head
$ git -C "$PROBE" rev-parse HEAD
79c9e859c3650cc726593f480135074a81631599
$ python3 "$PROBE/automation/reconcile/reconcile.py" --check --range fef828849653ece624ecf5a9d2b92e7416fcf7f1...74b9d0dfd98f13c17124a9b40d955ff9461e0572
reconcile: 0 finding(s)
exit=0
```

Control, so the change in output is attributable to the repair and not to the synthetic
candidate shape: the same construction with 74b9d0d's tree unmodified.

```
$ git commit-tree 74b9d0dfd98f13c17124a9b40d955ff9461e0572^{tree} -p fef828849653ece624ecf5a9d2b92e7416fcf7f1 -p 74b9d0dfd98f13c17124a9b40d955ff9461e0572 -m "probe: the pull request 13 merge with no fix applied"
db29ad426c56916ebd73fbc09a6cebf8d52d0fe3
$ git worktree add --detach "$CTRLDIR" db29ad426c56916ebd73fbc09a6cebf8d52d0fe3
Preparing worktree (detached HEAD db29ad4)
HEAD is now at db29ad4 probe: the pull request 13 merge with no fix applied
$ git -C "$CTRLDIR" status --short --untracked-files=all | head
$ python3 "$CTRLDIR/automation/reconcile/reconcile.py" --check --range fef828849653ece624ecf5a9d2b92e7416fcf7f1...74b9d0dfd98f13c17124a9b40d955ff9461e0572
[task-admission] tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md: task snapshot 74b9d0dfd98f13c17124a9b40d955ff9461e0572 violated lifecycle topology: new task:2026-07-25-fix-handover-projection-code-span-copy was created directly in 1_in-progress
    fix: create new tasks in 0_backlog, then claim and move them through the lifecycle
reconcile: 1 finding(s)
exit=1
```

Both probe worktrees were then removed.

```
$ git worktree list
/Users/quentinmiao/code/ai-harness  e805812 [task/2026-07-25-fix-merge-parent-task-topology]
```

## New tests against the pre-fix reconciler

`automation/reconcile/reconcile.py` was reverted to its committed state while the new
tests stayed in place, so each test's pre-fix verdict is recorded rather than assumed.

```
$ git checkout -- automation/reconcile/reconcile.py
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests -k task_admission_accepts -k task_admission_still -k task_admission_keeps -v
test_task_admission_accepts_a_merge_claiming_a_backlog_task ... FAIL
test_task_admission_accepts_a_merge_parent_that_predates_a_task ... FAIL
test_task_admission_keeps_the_adoption_escape_for_a_first_task ... ok
test_task_admission_still_rejects_a_linear_in_progress_creation ... ok
test_task_admission_still_rejects_a_merge_creation_no_parent_had ... ok
test_task_admission_still_rejects_an_illegal_merge_advance ... FAIL

======================================================================
FAIL: test_task_admission_accepts_a_merge_claiming_a_backlog_task
AssertionError: Lists differ: [] != ['task snapshot 0aa825f1f7f399b1aab48f47e4[106 chars]ess']
First extra element 0:
'task snapshot 0aa825f1f7f399b1aab48f47e486d67ad1a3f84e violated lifecycle topology: new task:2026-07-23-example was created directly in 1_in-progress'

======================================================================
FAIL: test_task_admission_accepts_a_merge_parent_that_predates_a_task
AssertionError: Lists differ: [] != ['task snapshot b92732ac9c18c4bea65e90239b[106 chars]ess']
First extra element 0:
'task snapshot b92732ac9c18c4bea65e90239bb482580620ba0a violated lifecycle topology: new task:2026-07-23-example was created directly in 1_in-progress'

======================================================================
FAIL: test_task_admission_still_rejects_an_illegal_merge_advance
AssertionError: Lists differ: [] != ['task snapshot a839f76594a86205346da64a63[99 chars]one']
First extra element 0:
'task snapshot a839f76594a86205346da64a63f2d531a3b2ba62 violated lifecycle topology: new task:2026-07-23-example was created directly in 4_done'
 : ['task snapshot a839f76594a86205346da64a63f2d531a3b2ba62 violated lifecycle topology: task:2026-07-23-example jumped from 0_backlog to 4_done', 'task snapshot a839f76594a86205346da64a63f2d531a3b2ba62 violated lifecycle topology: new task:2026-07-23-example was created directly in 4_done']

----------------------------------------------------------------------
Ran 6 tests in 3.540s

FAILED (failures=3)
```

Pre-fix verdicts, and what each test therefore proves:

| Test | Pre-fix | Discriminates |
|---|---|---|
| `accepts_a_merge_parent_that_predates_a_task` | FAIL | yes — the exact reported defect, in a fixture |
| `accepts_a_merge_claiming_a_backlog_task` | FAIL | yes — a legal `0_backlog` to `1_in-progress` merge advance was also being reported |
| `still_rejects_an_illegal_merge_advance` | FAIL on the second assertion; its `jumped from 0_backlog to 4_done` assertion already passed | yes — proves the illegal jump survives the suppression, which is what the rejected union shape would have lost |
| `still_rejects_a_linear_in_progress_creation` | ok | no — regression guard for the single-parent path |
| `still_rejects_a_merge_creation_no_parent_had` | ok | no — regression guard for a merge no parent of which has the task |
| `keeps_the_adoption_escape_for_a_first_task` | ok | no — regression guard for the `adopting` escape |

## New tests against the fixed reconciler

```
$ git apply tmp/merge-parent-topology/fix.patch
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests -k task_admission_accepts -k task_admission_still -k task_admission_keeps -v
test_task_admission_accepts_a_merge_claiming_a_backlog_task ... ok
test_task_admission_accepts_a_merge_parent_that_predates_a_task ... ok
test_task_admission_keeps_the_adoption_escape_for_a_first_task ... ok
test_task_admission_still_rejects_a_linear_in_progress_creation ... ok
test_task_admission_still_rejects_a_merge_creation_no_parent_had ... ok
test_task_admission_still_rejects_an_illegal_merge_advance ... ok

----------------------------------------------------------------------
Ran 6 tests in 4.768s

OK
```

## Repository invariants

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
exit=0
```

## Core scope gate

```
$ python3 automation/check_core_scope.py --staged
core-scope: pass (2 core path(s), task 2026-07-25-fix-merge-parent-task-topology; independent review manual; not invoked)
exit=0
```

## Full test suite

```
$ python3 automation/run_tests.py
Ran 118 tests in 47.190s
Ran 55 tests in 2.138s
Ran 24 tests in 0.014s
Ran 9 tests in 0.012s
Ran 40 tests in 14.782s
Ran 28 tests in 10.696s
Ran 291 tests in 217.517s
Ran 9 tests in 0.005s
Ran 19 tests in 1.899s
tests: 1/1 files passed
tests: 2/2 files passed
tests: 1/1 files passed
Ran 5 tests in 0.173s
Ran 3 tests in 0.363s
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
exit=0
```

The `Ran ...` lines above are the per-file totals `run_tests.py` prints in order; the
291-test line is `automation/tests/test_reconcile_queue.py`, up from 285 before this
task's six additions. Every line of this run is reproduced verbatim from
`automation/run_tests.py` with no selection other than dropping the progress-dot and
separator lines between the totals.
