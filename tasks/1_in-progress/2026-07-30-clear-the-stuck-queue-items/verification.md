# Verification — clear the four stuck queue items against real repository state

**Verified:** 2026-07-31 by claude

Only commands actually run and their real output. Every transcript below was taken in the
live worktree on branch task/2026-07-30-clear-the-stuck-queue-items, except the two sections
that say otherwise, which used a disposable clone under git-ignored `tmp/`. That clone was
deleted before any commit; nothing synthetic reached the repository.

## 1. The merged code-span repair really merged

```
$ git log -1 --format='%H %s' 6d4e337
6d4e337c3c3b3b795f4de6486198791023be7e83 fix: render code spans on both sides of the handover copy check
$ git log -1 --format='%(trailers:key=task)' 6d4e337
task: 2026-07-25-fix-handover-projection-code-span-copy

$ git merge-base --is-ancestor 6d4e337 main && echo "6d4e337 is an ancestor of main"
6d4e337 is an ancestor of main
```

```
$ git show --stat --format='%H%n%s' 6d4e337
6d4e337c3c3b3b795f4de6486198791023be7e83
fix: render code spans on both sides of the handover copy check

 automation/check_action_projection.py              |  13 +++
 automation/reconcile/reconcile.py                  |   7 +-
 .../design.md                                      | 109 +++++++++++++++++++++
 3 files changed, 127 insertions(+), 2 deletions(-)
```

The item's three `Done when` clauses, checked one at a time. The repaired comparison is in
the diff above. The six regression tests exist and pass today:

```
$ python3 -m unittest [the six ReconcileQueueTests code-span tests] -v
test_strict_handover_projects_backticked_context_field (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_strict_handover_projects_rendered_code_span_context (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_strict_handover_rejects_context_copying_neither_spelling (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_strict_handover_context_without_code_span_is_unchanged (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_strict_handover_projects_code_spanned_human_item_at_all (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_strict_handover_rejects_agent_entry_carrying_code_span (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.123s

OK
```

And the previously blocked handover is committed at a fresh conversation path, on main:

```
$ git log --oneline -1 -- history/conversations/2026-07-25-1140PDT-fold-edge-graph-decisions-and-ship-stage-0/handover.md
b0d0971 harness: record the blocked edge-graph Stage 0 handover
$ git merge-base --is-ancestor b0d0971 main && echo "b0d0971 (blocked handover) is an ancestor of main"
b0d0971 (blocked handover) is an ancestor of main
```

## 2. The live acceptance test

The real stuck item's deletion plus its reciprocal task backlink, staged in the live
worktree. Nothing else, and no evidence file.

```
$ git rm -q message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
$ git add -A
$ git status --porcelain
D  message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
M  tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
ACCEPTANCE_EXIT=0

$ git diff --cached --name-only -- automation/reconcile/reconcile.py | wc -l
       0
```

The whole reconciler is green on that deletion, and the declared evidence file is not in the
commit.

## 3. Negative control — the same edit before the widening

A full clone of this worktree, checked out at `bceb632`, the parent of the widening commit
`c5ab22c`, so the checker, the item, and the backlink are all the pre-widening versions. The
identical edit is staged there.

```
$ git clone -q . tmp/negative-control
$ cd tmp/negative-control && git checkout -q bceb632 && git log --oneline -1
bceb632 harness: claim the earlier-evidence admission task

$ rm message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
$ (rewrite that task's Queue actions to none) && git add -A && git status --porcelain
D  message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md
M  tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy/task.md
$ git diff --cached --name-only -- automation/reconcile/reconcile.py | wc -l
       0

$ python3 automation/reconcile/reconcile.py --check
[queue-resolution] message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md: deleted unresolved queue item: resolution evidence was not created or changed in the deletion commit: `automation/reconcile/reconcile.py`
    fix: commit the required claim/response evidence before deleting it
[link-check] tasks/1_in-progress/2026-07-30-admit-evidence-that-landed-earlier/task.md: `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md` does not exist
    fix: fix the path, create the target, or unquote if not a path
reconcile: 2 finding(s)
CONTROL_EXIT=1
```

The first finding is the one the widening removes. The second is an artifact of the control's
checkout point only: at `bceb632` the earlier-evidence task record still backticked that path,
and `767fd55` unquoted it. It does not appear in the live run in section 2.

## 4. The three merge boundaries were crossed

Every bound range head, and every merge that carried it, is already an ancestor of `main`.

```
$ git merge-base --is-ancestor d7eefcee521ad319bbf428c796c96740833f2a17 main && echo ...
first-class-message-queue END: ANCESTOR
$ git merge-base --is-ancestor 8ca62bc82bd11c5b59b27c35092eeb29ba1d5b7b main && echo ...
layered-workspace END: ANCESTOR
$ git merge-base --is-ancestor fd2374d99796300ed4325c2961e696092c17875e main && echo ...
test-isolation END: ANCESTOR
```

```
$ git log -1 --format='%h %s' 2372e48 && git merge-base --is-ancestor 2372e48 main && echo ...
2372e48 Merge pull request #7 from QuentinMeow/task/2026-07-23-first-class-message-queue
2372e48 ancestor of main
$ git log -1 --format='%h %s' d87b755 && git merge-base --is-ancestor d87b755 main && echo ...
d87b755 Merge pull request #11 from QuentinMeow/task/2026-07-24-isolate-test-git-environment
d87b755 ancestor of main
$ git log -1 --format='%h %s' c9f5244 && git merge-base --is-ancestor c9f5244 main && echo ...
c9f5244 Merge pull request #12 from QuentinMeow/task/2026-07-24-layered-development-workspace
c9f5244 ancestor of main
```

Replaying the crossing reports all three unresolved. Run in the clone, on a branch at this
task's commit `fdd521a`, with no edit staged:

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge
[queue-boundary] message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
reconcile: 3 finding(s)
MERGE_TRANSITION_EXIT=1
```

## 5. Neither answering nor deleting can close them now

**Deleting one is refused, twice over.** In the clone at `fdd521a`, staging the deletion of
the first-class-message-queue review together with its task backlink:

```
$ python3 automation/reconcile/reconcile.py --check
[queue-resolution] message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md: deleted unresolved queue item: human action was not committed as folding with a concrete response
    fix: commit the required claim/response evidence before deleting it
[task-action-origin] tasks/3_in-review/2026-07-23-first-class-message-queue/task.md: task artifact introduced an unqueued human action: Invalid human-action projection: After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
[link-check] tasks/1_in-progress/2026-07-30-clear-the-stuck-queue-items/task.md: `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md` does not exist
    fix: fix the path, create the target, or unquote if not a path
reconcile: 3 finding(s)
PROBE_EXIT=1
```

The second finding is the interesting one: removing the item does not remove the ask, it
turns the task's own acceptance criterion back into an unqueued human action. The third is
this task's record naming the item while it existed; the three paths were unquoted in that
record afterwards so it does not become a landmine.

**A full approval written today still does not satisfy the boundary.** In the clone only,
with synthetic text that was never committed to the repository, the test-runner review was
given a response while `waiting` and then claimed with a status-only folding edge — the exact
two-commit lifecycle the contract requires:

```
$ (commit 1: Reviewed revision := the reviewed range, Review outcome := approved,
             Your review := "SYNTHETIC PROBE TEXT, never committed to the repository.")
$ (commit 2: Status waiting -> folding, nothing else)
$ python3 automation/reconcile/reconcile.py --check --at-transition merge
[queue-boundary] message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md: unresolved future-blocking action reached transition:merge: the review has no committed folding claim
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
[queue-boundary] message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md: unresolved future-blocking action reached transition:merge: Git-range approval needs an explicit active base...head range
    fix: resolve the action with fresh boundary evidence or reclassify its timing before crossing the boundary
reconcile: 3 finding(s)
SIMULATED_APPROVAL_EXIT=1
```

The approved review's message changed from "no committed folding claim" to "Git-range
approval needs an explicit active base...head range". A merge-bound approval is only fresh at
a merge, so supplying that merge's exact range is the last thing to try:

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-07-24-isolate-test-git-environment \
    --range 25d03257b5ee61753fa9bada609722c4e84a8064...fd2374d99796300ed4325c2961e696092c17875e
reconcile: Git snapshot error: captured candidate is neither the --range head nor an exact base+head synthetic merge
EXIT=2
```

There is no candidate left for that approval to authorize, because the merge is already in
`main`'s history. This is the mechanical statement of "Git evidence cannot un-cross a
boundary", measured rather than asserted.

The first attempt at this probe also produced a useful refusal, recorded because it shows the
lifecycle is not bypassable in one step:

```
$ (single edit setting status, revision, outcome and response together)
$ python3 automation/reconcile/reconcile.py --check --at-transition merge
[queue-resolution] message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md: live queue action was rewritten: the waiting -> folding claim changed more than status
    fix: preserve the action and response identity; file a distinct successor action when the requested work changes
[...]
reconcile: 4 finding(s)
```

## 6. Reconciler and full suite at the final state

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
check exit=0
```

```
$ python3 automation/run_tests.py
[the runner's lane preamble, its nested inert probes, and the shard progress dots]
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
test elapsed: 35.70s
SUITE_EXIT=0
```

Every commit on this branch went through the pre-commit hook, which runs the core-scope gate,
the reconciler, and the staged-path test lane. No `--no-verify` bypass was used at any point.

## 7. One thing the scratch clone exposed

While the clone existed under `tmp/`, `--check` reported it:

```
[agents-budget] tmp/negative-control/AGENTS.md: 119 lines exceeds the 60-line budget
    fix: move depth into a linked doc (handbook/principles/progressive-disclosure.md)
reconcile: 1 finding(s)
```

`agents-budget` walks the filesystem rather than the Git index, so a git-ignored scratch
checkout is inside its scope. The clone was deleted and the finding disappeared. Backlog task
2026-07-30-exclude-scratch-paths-from-checks already owns this shape.

## Review verdicts (when a review was explicitly run)

No independent review was invoked for this change; `--require-review` was not selected.
