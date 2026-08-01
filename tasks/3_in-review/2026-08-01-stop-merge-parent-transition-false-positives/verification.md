# Verification — stop reading a merge parent edge as a lifecycle transition

**Verified:** 2026-08-01 by claude

Only commands actually run and their real output. Every command below was run in a git
worktree of this repository; the working directory is the worktree root in all cases.

**Editing conventions used in this file, and nothing else:**

- `[... elided: <what> ...]` marks a place where real output was cut. Nothing is
  paraphrased, reordered, or reflowed, and no line is partially edited.
- `(exit N)` lines are this file's own annotation of `echo "(exit $?)"` output, run
  immediately after the command above it.
- Where a command's output is empty, that is stated as `(no output)` rather than omitted.

## Baseline — each branch is green on its own

`origin/main` was at `88117705c64caa7fe691e485937bc6ceece069f5` and
`origin/task/2026-07-31-finish-the-replacement-ref-boundary` at
`9943d65` for every run in this file.

```
$ git checkout -B probe-clean origin/task/2026-07-31-finish-the-replacement-ref-boundary
Switched to a new branch 'probe-clean'
Branch 'probe-clean' set up to track remote branch 'task/2026-07-31-finish-the-replacement-ref-boundary' from 'origin'.
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

```
$ git checkout -B mainprobe origin/main
Switched to a new branch 'mainprobe'
Branch 'mainprobe' set up to track remote branch 'main' from 'origin'.
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

This is the artifact the defect hides behind: with no `MERGE_HEAD`, the reconciler never
re-walks history, so neither branch reveals the problem alone.

## Reproduction — before any code change

Run on the unmodified tree, at `origin/main` `8811770`.

```
$ git checkout -B probe origin/task/2026-07-31-finish-the-replacement-ref-boundary
Switched to and reset branch 'probe'
Branch 'probe' set up to track remote branch 'task/2026-07-31-finish-the-replacement-ref-boundary' from 'origin'.
Your branch is up to date with 'origin/task/2026-07-31-finish-the-replacement-ref-boundary'.

$ git merge --no-commit -X theirs origin/main
Auto-merging tasks/3_in-review/2026-07-23-first-class-message-queue/task.md
Auto-merging roadmap/current-state.md
Removing message-queue/needs-agent/requests/non-blocking-pick-up-single-source-queue-prefix-rule.md
Removing message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
Auto-merging automation/tests/test_run_tests.py
Auto-merging automation/tests/test_reconcile_queue.py
Auto-merging automation/run_tests.py
Auto-merging automation/reconcile/reconcile.py
Auto-merging automation/check_action_projection.py
Automatic merge went well; stopped before committing as requested

$ python3 automation/reconcile/reconcile.py --check
[queue-task-reciprocity] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: task:2026-07-23-first-class-message-queue does not link this live queue action
    fix: add `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md` to that task's Queue actions
[queue-task-reciprocity] message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md: task:2026-07-23-first-class-message-queue does not link this live queue action
    fix: add `message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md` to that task's Queue actions
[task-structure] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: Queue actions path `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md` is not in the Git index
    fix: stage the queue item or remove the stale task reference
[task-admission] tasks/4_done/2026-07-25-fix-handover-projection-code-span-copy/task.md: task snapshot 84e3524ef36c8aed5734c48248131f6c2b397ce8 violated lifecycle topology: task:2026-07-25-fix-handover-projection-code-span-copy jumped from 1_in-progress to 4_done
    fix: use one declared lifecycle edge at a time; from 1_in-progress the allowed destination is 2_blocked, 3_in-review
[task-admission] tasks/4_done/2026-07-25-fix-handover-projection-code-span-copy/task.md: staged task candidate violated lifecycle topology: task:2026-07-25-fix-handover-projection-code-span-copy jumped from 1_in-progress to 4_done
    fix: use one declared lifecycle edge at a time; from 1_in-progress the allowed destination is 2_blocked, 3_in-review
[task-action-origin] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: task artifact introduced an unqueued human action: - [ ] [After the repair is published as one exact revision, judge whether every human-attention file is understandable and answerable on its own, and approve it, name the remaining ambiguity, or reject the format.](../../../message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md) A fresh final independent adversarial review also completes before merge.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
[task-action-origin] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: task artifact introduced an unqueued human action: Invalid human-action projection: After the repair is published as one exact revision, judge whether every human-attention file is understandable and answerable on its own, and approve it, name the remaining ambiguity, or reject the format.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
reconcile: 7 blocking finding(s)
(exit 1)
```

**Only the two `task-admission` findings belong to this task.** The other five come from
`-X theirs` taking `main`'s copy of one task record over a branch that had renamed the
queue items that record links; that is content-merge work for whoever performs the merge,
not a reconciler defect. The section "The other five findings are the resolution, not the
checker" below proves that separately, and this task changes nothing about them.

## The reported history is well-formed — the finding is false

Read from the object database, not inferred.

```
$ git log -1 --format='%H%n%P%n%s' 84e3524
84e3524ef36c8aed5734c48248131f6c2b397ce8
7c2854a1fb3a885423f080f3957d76f132b32b27 ed3a9ee2d9314cd5dde59348eca1b7e02ccdfe43
Merge pull request #41 from QuentinMeow/task/2026-07-30-clear-the-stuck-queue-items
```

```
$ git ls-tree -r --name-only 7c2854a -- tasks | grep "2026-07-25-fix-handover-projection-code-span-copy/task.md"
tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md
$ git ls-tree -r --name-only ed3a9ee -- tasks | grep "2026-07-25-fix-handover-projection-code-span-copy/task.md"
tasks/4_done/2026-07-25-fix-handover-projection-code-span-copy/task.md
$ git ls-tree -r --name-only 84e3524 -- tasks | grep "2026-07-25-fix-handover-projection-code-span-copy/task.md"
tasks/4_done/2026-07-25-fix-handover-projection-code-span-copy/task.md
```

The trunk parent holds the task at `1_in-progress`; the branch parent and the merge hold
it at `4_done`. The branch reached `4_done` in two commits, not one:

```
$ git log --oneline --format='%h %s' 7c2854a..ed3a9ee -- tasks/3_in-review/2026-07-25-fix-handover-projection-code-span-copy tasks/4_done/2026-07-25-fix-handover-projection-code-span-copy
6de7954 harness: complete the code-span repair task now its work is on main
07de276 harness: advance the merged code-span repair task to review
```

Both are governed `harness:` lifecycle commits — `1_in-progress → 3_in-review` then
`3_in-review → 4_done`. The trunk-side parent edge collapses them into one apparent jump.
The history is correct and the finding is a false positive.

## The fix isolated on one identical tree

The cleanest possible A/B: the same merged and fully resolved working tree and index, run
twice, changing only `automation/reconcile/reconcile.py`. The merge is the probe merge with
its content conflicts resolved (see the next section for how, and why that is unrelated).

The two runs happened in this order: this task's reconciler first (the last run of the
resolution section below), then `origin/main`'s written over the same file in place. They
are presented before/after here for readability; no other command ran between them.

With `origin/main`'s reconciler:

```
$ cp automation/reconcile/reconcile.py "$SCRATCH/fixed-reconcile.py"
$ git show origin/main:automation/reconcile/reconcile.py > automation/reconcile/reconcile.py
$ python3 automation/reconcile/reconcile.py --check
[task-admission] tasks/4_done/2026-07-25-fix-handover-projection-code-span-copy/task.md: task snapshot 84e3524ef36c8aed5734c48248131f6c2b397ce8 violated lifecycle topology: task:2026-07-25-fix-handover-projection-code-span-copy jumped from 1_in-progress to 4_done
    fix: use one declared lifecycle edge at a time; from 1_in-progress the allowed destination is 2_blocked, 3_in-review
[task-admission] tasks/4_done/2026-07-25-fix-handover-projection-code-span-copy/task.md: staged task candidate violated lifecycle topology: task:2026-07-25-fix-handover-projection-code-span-copy jumped from 1_in-progress to 4_done
    fix: use one declared lifecycle edge at a time; from 1_in-progress the allowed destination is 2_blocked, 3_in-review
reconcile: 2 blocking finding(s)
(exit 1)
```

With this task's reconciler, same tree, same index:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
(exit 0)
```

`$SCRATCH` is this session's scratchpad directory outside the repository; the copy exists
only so the fixed file could be restored afterwards, which it was.

## The merge probe with the fix applied

The exact reproduction command, with `main` plus this task's fix as the incoming side and
the same crude `-X theirs` resolution as the reproduction:

```
$ git checkout -B probe origin/task/2026-07-31-finish-the-replacement-ref-boundary
Branch 'probe' set up to track remote branch 'task/2026-07-31-finish-the-replacement-ref-boundary' from 'origin'.
Your branch is up to date with 'origin/task/2026-07-31-finish-the-replacement-ref-boundary'.

$ git merge --no-commit -X theirs task/2026-08-01-stop-merge-parent-transition-false-positives 2>&1 | tail -8
[... elided: `tail -8` cut the lines above these; they were not captured ...]
Removing message-queue/needs-agent/requests/non-blocking-pick-up-single-source-queue-prefix-rule.md
Removing message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
Auto-merging automation/tests/test_run_tests.py
Auto-merging automation/tests/test_reconcile_queue.py
Auto-merging automation/run_tests.py
Auto-merging automation/reconcile/reconcile.py
Auto-merging automation/check_action_projection.py
Automatic merge went well; stopped before committing as requested

$ python3 automation/reconcile/reconcile.py --check
[queue-task-reciprocity] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: task:2026-07-23-first-class-message-queue does not link this live queue action
    fix: add `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md` to that task's Queue actions
[queue-task-reciprocity] message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md: task:2026-07-23-first-class-message-queue does not link this live queue action
    fix: add `message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md` to that task's Queue actions
[task-structure] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: Queue actions path `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md` is not in the Git index
    fix: stage the queue item or remove the stale task reference
[task-action-origin] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: task artifact introduced an unqueued human action: - [ ] [After the repair is published as one exact revision, judge whether every human-attention file is understandable and answerable on its own, and approve it, name the remaining ambiguity, or reject the format.](../../../message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md) A fresh final independent adversarial review also completes before merge.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
[task-action-origin] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: task artifact introduced an unqueued human action: Invalid human-action projection: After the repair is published as one exact revision, judge whether every human-attention file is understandable and answerable on its own, and approve it, name the remaining ambiguity, or reject the format.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
reconcile: 5 blocking finding(s)
(exit 1)
```

**Seven findings became five: both `task-admission` findings are gone, and no other
finding changed.** The remaining five are the same five the reproduction produced.

## The other five findings are the resolution, not the checker

`-X theirs` is not a correct resolution of this merge, and this section shows why with the
fix still applied. The branch renamed
`message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md` to
`future-blocking-rereview-human-action-files.md` and updated the task record that links it;
`-X theirs` keeps the branch's renamed file but takes `main`'s task record, so the record
points at a deleted path and two live items are unlinked. A plain `git merge` refuses that
combination outright:

```
$ git merge --no-commit origin/main 2>&1 | tail -10
[... elided: `tail -10` cut the lines above these; they were not captured ...]
Auto-merging roadmap/current-state.md
Removing message-queue/needs-agent/requests/non-blocking-pick-up-single-source-queue-prefix-rule.md
Removing message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
Auto-merging automation/tests/test_run_tests.py
Auto-merging automation/tests/test_reconcile_queue.py
Auto-merging automation/run_tests.py
Auto-merging automation/reconcile/reconcile.py
CONFLICT (content): Merge conflict in automation/reconcile/reconcile.py
Auto-merging automation/check_action_projection.py
Automatic merge failed; fix conflicts and then commit the result.
$ git diff --name-only --diff-filter=U
automation/reconcile/reconcile.py
tasks/3_in-review/2026-07-23-first-class-message-queue/task.md
```

Taking the branch's side of that record — the correct resolution, since the branch is the
side that renamed the items — leaves exactly one finding, and it is a true one:

```
$ git checkout origin/task/2026-07-31-finish-the-replacement-ref-boundary -- tasks/3_in-review/2026-07-23-first-class-message-queue/task.md
$ python3 automation/reconcile/reconcile.py --check
[queue-task-reciprocity] message-queue/needs-human/decisions/future-blocking-dispose-merge-reviews-whose-boundary-already-passed.md: task:2026-07-23-first-class-message-queue does not link this live queue action
    fix: add `message-queue/needs-human/decisions/future-blocking-dispose-merge-reviews-whose-boundary-already-passed.md` to that task's Queue actions
reconcile: 1 blocking finding(s)
(exit 1)
```

`main` filed that decision item against the same task after the branch was cut, so the
merged record has to link it. Doing exactly what the finding says — appending that one
path to the record's `Queue actions` field and staging it — clears the merge completely:

```
$ git add tasks/3_in-review/2026-07-23-first-class-message-queue/task.md
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
(exit 0)
```

Disclosure: `git add` and the check were first issued as one `&&` command that hit this
session's two-minute tool timeout with no output; `git add` had completed, and the check
alone was re-run to produce the output above. Nothing about the tree changed in between.

**So the merge probe reaches 0 blocking findings.** Reaching it needs this task's fix
*and* a correct resolution of two content conflicts that `-X theirs` gets wrong; the fix
alone cannot clear findings about which side of a conflicted file the merger kept. The
five `-X theirs` findings are correct reports about a bad resolution, and the reconciler
was right to raise all of them.

## New tests, before the fix

Run against the unmodified `automation/reconcile/reconcile.py` at `origin/main`, with both
new tests already written.

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_accepts_a_merge_inheriting_an_advanced_task automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_still_rejects_a_merge_advance_past_a_sibling automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_still_rejects_an_illegal_merge_advance -v
test_task_admission_accepts_a_merge_inheriting_an_advanced_task (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... FAIL
test_task_admission_still_rejects_a_merge_advance_past_a_sibling (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The suppression matches the exact status, not merely the record. ... ok
test_task_admission_still_rejects_an_illegal_merge_advance (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok

======================================================================
FAIL: test_task_admission_accepts_a_merge_inheriting_an_advanced_task (automation.tests.test_reconcile_queue.ReconcileQueueTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/quentinmiao/code/ai-harness/.claude/worktrees/agent-a56f14bd9878031ff/automation/tests/test_reconcile_queue.py", line 13724, in test_task_admission_accepts_a_merge_inheriting_an_advanced_task
    ], self.messages(findings))
AssertionError: Lists differ: [] != ['task snapshot 7cdcf4ee8293b2d2369c8b0937[100 chars]one']

Second list contains 1 additional elements.
First extra element 0:
'task snapshot 7cdcf4ee8293b2d2369c8b0937b1a560b64014a1 violated lifecycle topology: task:2026-07-23-example jumped from 1_in-progress to 4_done'

- []
+ ['task snapshot 7cdcf4ee8293b2d2369c8b0937b1a560b64014a1 violated lifecycle '
+  'topology: task:2026-07-23-example jumped from 1_in-progress to 4_done']
[... elided: unittest repeats the same list a third time as the assertion's msg argument ...]

----------------------------------------------------------------------
Ran 3 tests in 4.063s

FAILED (failures=1)
```

`test_task_admission_accepts_a_merge_inheriting_an_advanced_task` discriminates: it fails
without the fix, on a real two-parent merge built by `git merge --no-ff`, and its failure
message is the same finding the repository reproduction produced.

`test_task_admission_still_rejects_a_merge_advance_past_a_sibling` passes here, as a
rejection test must. Its own discriminating run is the next section.

## The illegal-advance guard has teeth

A rejection test that passes both before and after a change proves nothing on its own, so
the guard was rewritten to the one plausible weaker shape — reusing
`task_recorded_at_other_parent`, which asks only whether a sibling parent records the task
at all — and the suite re-run. This was a temporary in-place edit of one line, reverted
immediately afterwards; nothing in the committed tree contains it.

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_still_rejects_a_merge_advance_past_a_sibling automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_still_rejects_an_illegal_merge_advance automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_accepts_a_merge_inheriting_an_advanced_task -v
test_task_admission_still_rejects_a_merge_advance_past_a_sibling (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The suppression matches the exact status, not merely the record. ... FAIL
test_task_admission_still_rejects_an_illegal_merge_advance (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_task_admission_accepts_a_merge_inheriting_an_advanced_task (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok

======================================================================
FAIL: test_task_admission_still_rejects_a_merge_advance_past_a_sibling (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The suppression matches the exact status, not merely the record.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/quentinmiao/code/ai-harness/.claude/worktrees/agent-a56f14bd9878031ff/automation/tests/test_reconcile_queue.py", line 13764, in test_task_admission_still_rejects_a_merge_advance_past_a_sibling
    ), self.messages(findings))
AssertionError: False is not true : []

----------------------------------------------------------------------
Ran 3 tests in 2.595s

FAILED (failures=1)
```

The empty finding list is the point: under the weaker shape a merge whose two parents hold
a task at `0_backlog` and `1_in-progress`, and whose own tree holds it at `4_done`, is
reported by neither edge, and no parent ever reached `4_done`, so nothing else catches it.
The exact-status match in `task_status_at_other_parent` is what stops that.

Note that `test_task_admission_still_rejects_an_illegal_merge_advance`, the pre-existing
guard inherited from task 2026-07-25-fix-merge-parent-task-topology, passes under the
weaker shape. It covers a merge whose sibling parent has **no** record of the task, so it
cannot distinguish the two shapes — which is exactly why the new sibling test was needed.

## New and neighbouring tests, after the fix

Every test in `task_topology_problems`'s coverage, including the four inherited rules the
repair must not disturb:

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_accepts_a_merge_inheriting_an_advanced_task automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_still_rejects_a_merge_advance_past_a_sibling automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_still_rejects_an_illegal_merge_advance automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_rejects_illegal_lifecycle_jump automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_accepts_a_merge_claiming_a_backlog_task automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_rejects_active_deletion_but_allows_archival automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_rejects_task_id_rename automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_admission_keeps_the_adoption_escape_for_a_first_task -v
test_task_admission_accepts_a_merge_inheriting_an_advanced_task (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_task_admission_still_rejects_a_merge_advance_past_a_sibling (automation.tests.test_reconcile_queue.ReconcileQueueTests)
The suppression matches the exact status, not merely the record. ... ok
test_task_admission_still_rejects_an_illegal_merge_advance (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_task_admission_rejects_illegal_lifecycle_jump (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_task_admission_accepts_a_merge_claiming_a_backlog_task (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_task_admission_rejects_active_deletion_but_allows_archival (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_task_admission_rejects_task_id_rename (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_task_admission_keeps_the_adoption_escape_for_a_first_task (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok

----------------------------------------------------------------------
Ran 8 tests in 7.657s

OK
```

`test_task_admission_rejects_illegal_lifecycle_jump` is the single-parent case: it still
reports, so linear strictness is unchanged.

## Repository checks on this branch

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
(exit 0)
```

```
$ python3 automation/check_core_scope.py
core-scope: pass (2 core path(s), task 2026-08-01-stop-merge-parent-transition-false-positives; independent review manual; not invoked)
```

```
$ python3 automation/run_tests.py 2>&1 | tail -20
[... elided: `tail -20` cut the per-shard progress lines above these; they were not captured ...]
----------------------------------------------------------------------
Ran 66 tests in 8.692s

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
test elapsed: 55.46s
```

The installed pre-commit hook ran `check_core_scope`, `reconcile --check`, and
`run_tests --staged` on every commit in this branch and printed `pre-commit: OK` each
time. No commit used `--no-verify`.

## Not verified

- **No push, so no CI run.** Everything above is local. The GitHub Actions job that runs
  the same checks over a real merge range has not executed for this branch.
- **The merge probe was never committed.** Every probe run above stopped at
  `--no-commit` and was aborted afterwards, so the reconciler evaluated a staged merge
  candidate rather than a merge commit. The pre-existing tests and the two new ones do
  cover committed two-parent merges built by `git merge --no-ff`.
- **The resolution used for the 0-finding probe is this session's judgement**, not the
  merge the branch owner will actually perform. It takes the branch's side of one task
  record and appends one queue path, both to satisfy findings the reconciler named
  explicitly; a different but equally valid resolution is possible, and the branch owner
  owns that call.
- **Only `origin/task/2026-07-31-finish-the-replacement-ref-boundary` was probed.** Other
  live branches were not merged, so their content conflicts with `main` are unknown. The
  `task-admission` false positive is a property of `main`'s own history, so it affected
  every branch and is now fixed for all of them, but each branch's other merge work is its
  own.
