# Verification — Stop the merge-ref recompute race from failing every stacked pull request

**Verified:** 2026-08-02 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## What these tests do and do not exercise

Every run below drives the workflow step's **literal `run:` block** — the same bytes CI
executes — through `bash -e` against a local bare Git repository whose `refs/pull/N/merge`
entries are built to the shapes GitHub produces. That is the existing
`MergeRefFixture` harness the two sibling candidate steps already use.

What it exercises for real: the shell control flow, the `git fetch` of a pull merge ref,
the parent-shape binding, the ancestry check, the bound, the exit codes, and the
`GITHUB_OUTPUT` the step writes.

What it does **not** exercise: GitHub itself. No fixture run here touches a real pull
request, a real Actions runner, or the real timing of a merge-ref recompute. The recompute
is *simulated* by pointing the fixture's `refs/pull/2/merge` at a merge of the same head
onto an advanced base — the observable end state of a recompute — not by racing a live
provider. Nothing in the fixture runs is evidence about how long GitHub actually takes to
recompute.

One real CI run is recorded at the end of this file. It proves the rewritten step runs on a
real runner and admits a real candidate; it exercised the **equality fast path**, not the
re-resolution branch. Making a live GitHub run take the recompute branch requires merging a
parent pull request underneath this one while its check is in flight, which no command here
can stage on demand.

## Full test suite

```
$ python3 automation/run_tests.py
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.01s
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 12/12 files passed
test elapsed: 109.96s
```

The task's acceptance criterion asks for `11/11 files passed`. The suite has 12 test files
as of this revision; the criterion's number was written when it had 11 and is stale. Every
file passes.

## Reconciler and the core-scope boundary

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
$ echo $?
0
```

```
$ python3 automation/check_core_scope.py --range "origin/main...HEAD" --branch task/2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack
core-scope: pass (2 core path(s), task 2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack; independent review manual; not invoked)
```

## The three new tests

```
$ python3 -m unittest -v \
    automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests.test_review_state_candidate_survives_a_merge_ref_recompute \
    automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests.test_review_state_candidate_still_fails_a_genuine_mismatch \
    automation.tests.test_github_action_projection_workflow.GitHubActionProjectionWorkflowTests.test_review_state_merge_ref_resolution_is_bounded
test_review_state_candidate_survives_a_merge_ref_recompute (...)
A recomputed merge ref is still this event's code, so it passes. ... ok
test_review_state_candidate_still_fails_a_genuine_mismatch (...)
Re-resolution admits a moved base and nothing else. ... ok
test_review_state_merge_ref_resolution_is_bounded (...)
The retry is a bound, not a wait until the two values agree. ... ok

----------------------------------------------------------------------
Ran 3 tests in 6.764s

OK
```

## The guard bites — shown, not asserted

A passing assertion only proves the assertion ran. The script below is throwaway evidence
(it lives in the session scratchpad, not the repository) that runs the step directly and
prints raw exit codes, then deletes the head binding from a *copy* of the workflow and
re-runs the genuine-mismatch test against that copy. Its four blocks are: the pre-fix step
losing the recompute, the fixed step winning it, the fixed step still failing a genuine
mismatch, and the same test going red the moment the binding is removed.

`0d6df0a` is the pre-fix revision of `.github/workflows/harness.yml` (this task's claim
commit on `main`).

```
$ python3 <scratchpad>/prove_guard.py . 0d6df0a
=== A. pre-fix step, merge ref recomputed onto a moved base (PR 2) ===
exit=1 output=''
 * branch            refs/pull/2/merge -> FETCH_HEAD

=== A2. fixed step, same recomputed merge ref (PR 2) ===
exit=0 output='revision=dfa08c0845e883ef096a1fd5845464afac1f3c12\n'

=== B. fixed step, merge ref names a different head (PR 3) ===
exit=1 output=''
merge candidate does not merge this event's head
merge candidate does not merge this event's head
merge ref stayed unbound across 2 resolutions

=== C. head binding deleted from a copy, same test re-run ===
test_review_state_candidate_still_fails_a_genuine_mismatch (workflow_tests.GitHubActionProjectionWorkflowTests)
Re-resolution admits a moved base and nothing else. ...
======================================================================
FAIL: test_review_state_candidate_still_fails_a_genuine_mismatch (workflow_tests.GitHubActionProjectionWorkflowTests) (rejected='head raced ahead of the event')
Re-resolution admits a moved base and nothing else.
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../automation/tests/test_github_action_projection_workflow.py", line 866, in test_review_state_candidate_still_fails_a_genuine_mismatch
    self.assertNotEqual(code, 0, output)
AssertionError: 0 == 0 : revision=1113925bbcd8b99a81daf8d17afdc624d5e336b1

----------------------------------------------------------------------
Ran 1 test in 3.665s

FAILED (failures=1)
weakened-copy result: failures=1 errors=0
```

Reading it: **A** is the defect this task exists for — the shipped step exits 1 on a
recompute it should accept. **A2** is the same fixture through the new step, exiting 0 and
emitting the recomputed revision. **B** is a merge ref that names a *different* head; the
new step rejects it on every attempt and exits 1 when the bound is spent, so re-resolution
never converts a real mismatch into a pass. **C** removes the head comparison from a copy
of the workflow and the genuine-mismatch test fails on the `head raced ahead of the event`
case, which is what proves that test is load-bearing rather than vacuous.

Block B also shows the bound behaving: two attempts requested, two rejections printed, then
the exhaustion message. The production bound declared in the step's `env:` is 5 attempts 5
seconds apart; the runs above use 0-second delays so the suite does not sleep.

## The rewritten step on a real runner

Pull request #65 carries this change, so its own `pull_request` event ran the new step from
the candidate's workflow code.

```
$ gh pr checks 65 --json name,state -q '[.[]|select(.state!="SKIPPED")]|map(.name+"="+.state)|join(" ")'
External source release admission=SUCCESS reconcile-and-test=SUCCESS Current review-state action projection=SUCCESS Authoritative action projection from trusted workflow code=SUCCESS reconcile-and-test=SUCCESS
```

```
$ gh api "repos/QuentinMeow/agentfold/actions/jobs/91492855375" -q '.name, .conclusion, (.steps[]|.name+" -> "+.conclusion)'
Current review-state action projection
success
Set up job -> success
Checkout PR-base projection gate for review state -> success
Fetch event-bound PR merge candidate without checking it out -> success
Collect current formal reviews and unresolved diff threads -> success
Action projection — current review state -> success
Collect current PR conversation comments -> success
Action projection — current PR conversation state -> success
Post Checkout PR-base projection gate for review state -> success
Complete job -> success
```

Which branch that run took, from the job's own log:

```
$ gh api "repos/QuentinMeow/agentfold/actions/jobs/91492855375/logs" | grep -i "merge ref\|FETCH_HEAD\|recomputed\|branch  *refs/pull"
2026-08-02T11:48:20.1372984Z # merge ref, and the two revisions stop being equal for a reason
2026-08-02T11:48:20.1435920Z         "FETCH_HEAD^{commit}"
2026-08-02T11:48:20.1442244Z     ACTION_PROJECTION_REJECTION="merge ref resolves to no commit"
2026-08-02T11:48:20.1479825Z     echo "merge ref was recomputed after this event;" \
2026-08-02T11:48:20.1491039Z     echo "merge ref stayed unbound across" \
2026-08-02T11:48:20.5646312Z  * branch            refs/pull/65/merge -> FETCH_HEAD
```

The first five matches are Actions echoing the script source, not output. The only runtime
line is the fetch. `merge ref was recomputed after this event` does **not** appear, so the
candidate equalled `github.sha` and the run took the fast path. The re-resolution branch has
not run on GitHub; it has only run in the fixture.

## Review verdicts (when a review was explicitly run)

None run. `automation/check_core_scope.py --require-review` was not selected, and no
adversarial panel was convened: `handbook/collaboration-modes.md` sets the `async` gate at
tests plus reconciler, and this change opens no one-way door.
