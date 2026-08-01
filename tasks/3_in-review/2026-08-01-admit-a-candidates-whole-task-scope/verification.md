# Verification — let a candidate carry more than one task

**Verified:** 2026-08-01 by claude

Only commands actually run and their real output. Every elision is marked
`[... N lines elided ...]` on its own line; nothing else is trimmed or paraphrased.

## 1. The contradiction, reproduced from real repository state

### 1a. The projection gate refuses a real pull-request candidate (before the change)

Pull request 41's own Actions run printed this. Reproduced locally against the same
immutable merge candidate GitHub pinned for that event, with the same arguments the
workflow used:

```
$ git fetch origin refs/pull/41/merge:refs/agentfold-probe/pr41merge
From github.com:QuentinMeow/agentfold
 * [new ref]         refs/pull/41/merge -> refs/agentfold-probe/pr41merge

$ ACTION_PROJECTION_BODY=... ACTION_PROJECTION_TITLE=... \
  python3 automation/check_action_projection.py \
    --from-env ACTION_PROJECTION_BODY \
    --additional-summary-env ACTION_PROJECTION_TITLE \
    --external-assignment-env ACTION_PROJECTION_ASSIGNMENTS \
    --action-section "What to review" --queue-actor any \
    --required-queue-actor needs-human \
    --branch task/2026-07-30-clear-the-stuck-queue-items \
    --base-revision 3d4dba3e3c73f5407c3c57cdd0e72d5d01853fd4 \
    --candidate-revision 402809ea069b6e2dc142cde3a64aed5bdcb82871 \
    --allowed-url-prefix https://github.com/QuentinMeow/agentfold/blob/402809ea069b6e2dc142cde3a64aed5bdcb82871 \
    --label github-pull-request-description
action-projection: input error: candidate maps to multiple task scopes: 2026-07-23-first-class-message-queue, 2026-07-24-isolate-test-git-environment, 2026-07-24-layered-development-workspace, 2026-07-25-fix-handover-projection-code-span-copy, 2026-07-30-clear-the-stuck-queue-items
exit=2
```

That is byte-identical to the line the hosted job printed at 2026-08-01T21:30:39 in
actions/runs/30719279471/job/91420219255.

### 1b. The reconciler requires the cross-task edit that produces it

Removing the reciprocal backlink from the *other* task's record and staging the removal,
on the repository as it stood at `025de49`:

```
$ # remove two paths from tasks/3_in-review/2026-07-23-first-class-message-queue/task.md Queue actions
$ git add tasks/3_in-review/2026-07-23-first-class-message-queue/task.md
$ python3 automation/reconcile/reconcile.py --check
[queue-task-reciprocity] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: task:2026-07-23-first-class-message-queue does not link this live queue action
    fix: add `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md` to that task's Queue actions
[queue-task-reciprocity] message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md: task:2026-07-23-first-class-message-queue does not link this live queue action
    fix: add `message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md` to that task's Queue actions
[task-action-origin] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: task artifact introduced an unqueued human action: - [ ] [After the repair is published as one exact revision, judge whether every human-attention file is understandable and answerable on its own, and approve it, name the remaining ambiguity, or reject the format.](../../../message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md) A fresh final independent adversarial review also completes before merge.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
[task-action-origin] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: task artifact introduced an unqueued human action: Invalid human-action projection: After the repair is published as one exact revision, judge whether every human-attention file is understandable and answerable on its own, and approve it, name the remaining ambiguity, or reject the format.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
reconcile: 4 finding(s)
```

The probe was reverted (`git checkout --` plus `git reset`) and the tree returned to
`reconcile: 0 finding(s)` before any work began.

Both halves therefore hold at the same time: the reconciler refuses the commit without the
second task's record, and the projection gate refuses the candidate with it.

### 1c. The merge boundary, reproduced with the arguments CI used

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch harness/2026-07-31-fold-answered-queue-review \
    --range f3c8330ca6448e39adba6d0ccbf77294d8ddece7...025de49cbd6cf11adaa54d70590870f3bf17cdab
[queue-boundary] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: unresolved future-blocking action reached transition:merge: the action still needs its recorded actor
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
reconcile: 2 finding(s)
```

Byte-identical to actions/runs/30719165397/job/91419915222 at 2026-08-01T21:27:32.

Both items are created *inside* that range. At its base only their predecessor existed:

```
$ git ls-tree -r --name-only f3c8330ca6448e39adba6d0ccbf77294d8ddece7 -- message-queue | grep -E "redesign-human-action-files|rereview-human-action-files|review-first-class"
message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md
```

## 2. The new tests fail before the change and pass after

Six tests, run on the unmodified gates:

```
$ python3 -m unittest \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_cli_task_branch_binds_every_task_the_candidate_carries \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_cli_non_task_branch_binds_every_task_the_candidate_carries \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_changed_task_record_infers_scope_without_commit_tag \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_boundary_ignores_an_action_the_range_itself_introduced \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_boundary_still_reports_an_action_live_at_the_range_base \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_escalating_an_action_inside_the_range_still_reaches_it
======================================================================
ERROR: test_cli_task_branch_binds_every_task_the_candidate_carries (automation.tests.test_check_action_projection.ActionProjectionTests)
A second task record in the candidate widens the scope, not refuses it.
----------------------------------------------------------------------
Traceback (most recent call last):
[... 2 traceback lines elided ...]
AttributeError: module 'check_action_projection' has no attribute 'inferred_changed_task_ids'

======================================================================
ERROR: test_changed_task_record_infers_scope_without_commit_tag (automation.tests.test_check_action_projection.ActionProjectionTests)
----------------------------------------------------------------------
Traceback (most recent call last):
[... 2 traceback lines elided ...]
AttributeError: module 'check_action_projection' has no attribute 'inferred_changed_task_ids'

======================================================================
FAIL: test_cli_non_task_branch_binds_every_task_the_candidate_carries (automation.tests.test_check_action_projection.ActionProjectionTests)
----------------------------------------------------------------------
Traceback (most recent call last):
[... 2 traceback lines elided ...]
AssertionError: 1 != 2

======================================================================
FAIL: test_boundary_ignores_an_action_the_range_itself_introduced (automation.tests.test_reconcile_queue.ReconcileQueueTests)
Filing a future blocker is not crossing its boundary.
----------------------------------------------------------------------
Traceback (most recent call last):
[... 2 traceback lines elided ...]
AssertionError: Lists differ: [] != [<reconcile_queue.Finding object at 0x10ebc0990>]

Second list contains 1 additional elements.
First extra element 0:
<reconcile_queue.Finding object at 0x10ebc0990>

- []
+ [<reconcile_queue.Finding object at 0x10ebc0990>]

----------------------------------------------------------------------
Ran 6 tests in 0.706s

FAILED (failures=2, errors=2)
```

Two of the six — `..._live_at_the_range_base` and `test_escalating_...` — pass before and
after by design: they are the guards that the change did not widen past its stated rule.

The same six after the change:

```
$ python3 -m unittest [the same six test ids]
......
----------------------------------------------------------------------
Ran 6 tests in 4.077s

OK
```

### 2a. The answered-review guard is load-bearing, not decorative

With the two lines `if not unanswered_review(fields(item)): return False` deleted from
`unanswered_action_filed_inside_change_range`:

```
$ python3 -m unittest \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_an_answered_review_filed_in_the_range_still_reaches_it \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_git_range_approval_satisfies_merge_only_for_queue_only_tail
FF
======================================================================
FAIL: test_an_answered_review_filed_in_the_range_still_reaches_it (automation.tests.test_reconcile_queue.ReconcileQueueTests)
A committed human response is the boundary's receipt, never a filing.
----------------------------------------------------------------------
Traceback (most recent call last):
[... 2 traceback lines elided ...]
AssertionError: 1 != 0 : []

======================================================================
FAIL: test_git_range_approval_satisfies_merge_only_for_queue_only_tail (automation.tests.test_reconcile_queue.ReconcileQueueTests)
----------------------------------------------------------------------
Traceback (most recent call last):
[... 2 traceback lines elided ...]
AssertionError: 1 != 0

----------------------------------------------------------------------
Ran 2 tests in 0.884s

FAILED (failures=2)
```

`test_git_range_approval_satisfies_merge_only_for_queue_only_tail` is a pre-existing test.
It is how the missing guard was found: the first version of this change had no
`unanswered_review` condition and broke it. Restoring the two lines:

```
$ python3 -m unittest [the same two test ids]
..
----------------------------------------------------------------------
Ran 2 tests in 1.164s

OK
```

## 3. The merge boundary, isolated on real repository data

Same two live items, same task scope, same transition. The only variable is whether the
range filed them.

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --task-id 2026-07-23-first-class-message-queue \
    --range 025de49cbd6cf11adaa54d70590870f3bf17cdab...6bcf90120b550b8c762f783bf522a706b66b41b1
[queue-boundary] message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md: unresolved future-blocking action reached transition:merge: the action still needs its recorded actor
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
reconcile: 2 finding(s)

$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --task-id 2026-07-23-first-class-message-queue \
    --range f3c8330ca6448e39adba6d0ccbf77294d8ddece7...6bcf90120b550b8c762f783bf522a706b66b41b1
reconcile: 0 finding(s)
```

Pull request 45's own failing command, re-run against the repaired reconciler:

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch harness/2026-07-31-fold-answered-queue-review \
    --range f3c8330ca6448e39adba6d0ccbf77294d8ddece7...6bcf90120b550b8c762f783bf522a706b66b41b1
reconcile: 0 finding(s)
```

## 4. All six blocked pull requests, replayed against the repaired gate

Each command is that pull request's own workflow invocation, with its real base and the
immutable merge candidate GitHub pinned (pull request 36's merge ref no longer exists — the
branch has since gone `CONFLICTING` — so its recorded head and base are used, and its base
is still an ancestor of its head).

```
$ zsh replay.sh
=== PR #36  branch=task/2026-07-30-report-check-failures-honestly
action-projection: 0 finding(s)
exit=0
=== PR #41  branch=task/2026-07-30-clear-the-stuck-queue-items
[action-projection] github-pull-request-description: action section 1 claims no queued action but scoped live queue item(s) exist: message-queue/needs-human/decisions/future-blocking-dispose-merge-reviews-whose-boundary-already-passed.md, message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md, message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md, message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md
action-projection: 1 finding(s)
exit=1
=== PR #42  branch=task/2026-07-31-collapse-restated-contract-rules
action-projection: 0 finding(s)
exit=0
=== PR #45  branch=harness/2026-07-31-fold-answered-queue-review
[action-projection] github-pull-request-description: action section 1 claims no queued action but scoped live queue item(s) exist: message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md
action-projection: 1 finding(s)
exit=1
=== PR #46  branch=task/2026-07-31-redo-stranded-review-disposition
action-projection: input error: task branch is absent from the immutable candidate scope: 2026-07-31-redo-stranded-review-disposition is not in 2026-07-24-isolate-test-git-environment, 2026-07-24-layered-development-workspace
exit=2
=== PR #48  branch=task/2026-07-31-redesign-human-action-files
action-projection: 0 finding(s)
exit=0
```

Three pass outright. Two now reach the real check and report a *finding* about their own
description rather than refusing the candidate. One is still refused, correctly: its task
record exists in no commit on any branch —

```
$ git log --oneline --all -- 'tasks/*/2026-07-31-redo-stranded-review-disposition/*'
$ git ls-tree -r --name-only 025de49cbd6cf11adaa54d70590870f3bf17cdab -- tasks | grep redo-stranded || echo "(absent at base)"
(absent at base)
```

Both are filed in
`message-queue/needs-agent/requests/non-blocking-repair-three-branches-the-repaired-scope-gate-still-refuses.md`.

## 5. Repository invariants and the full suite

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

```
$ python3 automation/run_tests.py
[... 22 lines of per-shard lane/selection output elided ...]
Ran 65 tests in 9.911s

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
test elapsed: 66.70s
```

```
$ python3 automation/check_core_scope.py
core-scope: pass (5 core path(s), task 2026-08-01-admit-a-candidates-whole-task-scope; independent review manual; not invoked)
```

```
$ wc -l automation/AGENTS.md
      60 automation/AGENTS.md
```

## 6. Re-run on the finished tree

Section 5 was recorded at `6bcf9012`, the commit that carries the code change. Repeated at
`373ed00b`, after the records, the roadmap entry and the handover were added — only record
paths changed between the two:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ python3 automation/check_core_scope.py \
    --range 025de49cbd6cf11adaa54d70590870f3bf17cdab...373ed00b426786604d82bc27838e6d66cd9e8a36 \
    --branch task/2026-08-01-admit-a-candidates-whole-task-scope
core-scope: pass (6 core path(s), task 2026-08-01-admit-a-candidates-whole-task-scope; independent review manual; not invoked)

$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-08-01-admit-a-candidates-whole-task-scope \
    --range 025de49cbd6cf11adaa54d70590870f3bf17cdab...373ed00b426786604d82bc27838e6d66cd9e8a36
reconcile: 0 finding(s)

$ python3 automation/run_tests.py
[... 22 lines of per-shard lane/selection output elided ...]
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
test elapsed: 53.41s
```

The commit that adds this section is the only one after `373ed00b`, and it touches this file
alone.

## Not verified

- The hosted workflow was not re-run. Every replay above runs the same gate with the same
  arguments the failing jobs printed, on this machine, against the same immutable
  candidates — but a green Actions run for any of these six pull requests requires this
  change to be in their base first.
- Pull request 36's merge candidate `6a62357c...` is no longer fetchable, so its replay uses
  its recorded base and head rather than the merge commit the failing job saw. Its scope set
  is the same two ids the failing job named.
- No independent core-fit review was invoked; `--require-review` was not selected.

## Review verdicts (when a review was explicitly run)

None. No adversarial or core-fit review was run for this task.
