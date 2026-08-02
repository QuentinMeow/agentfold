# Verification — Report the structurally visible readability rules as advisory findings

**Verified:** 2026-08-02 by claude (session 2026-08-02, branch
`task/2026-08-02-advise-on-explanation-shape`)

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## The tree as it stands stays clean

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

No advisory line either: the new check reports nothing about any live queue item. How the
fifty-four of them split between checked and skipped, from a one-off probe of the same
functions the check calls:

```
$ python3 -c "<count live items and call current_queue_template_governs on each>"
total live items: 54
governed: 43  earlier-generation: 11
  ('needs-agent', 'requests') governed 40 legacy 1
  ('needs-human', 'decisions') governed 1 legacy 2
  ('needs-human', 'reviews') governed 2 legacy 8
```

The eleven skipped items are the ones written under the pre-rename field spelling, which
records-are-immutable puts outside today's templates. The other forty-three are checked
and every one of them passes as written — no correct file had to be edited to keep the
tree quiet.

## One deliberate violation: exit 0, printed as advisory

A `needs-agent` request with everything the blocking checks require and no
`## What you need to know` section was staged, run, and then deleted.

```
$ python3 automation/reconcile/reconcile.py --check
[explanation-shape] message-queue/needs-agent/requests/non-blocking-probe-the-advisory-shape-rule.md: missing section `## What you need to know`  (advisory)
    fix: copy the sections and their order from `templates/queue/request.md`
reconcile: 0 blocking finding(s), 1 advisory (not blocking)
```

Exit code: `0`.

## The same tree with `--fail-on-advisory`: exit 1

```
$ python3 automation/reconcile/reconcile.py --check --fail-on-advisory
[explanation-shape] message-queue/needs-agent/requests/non-blocking-probe-the-advisory-shape-rule.md: missing section `## What you need to know`  (advisory)
    fix: copy the sections and their order from `templates/queue/request.md`
reconcile: 0 blocking finding(s), 1 advisory (also failing)
```

Exit code: `1`.

## The boundary gate on a malformed pull-request body

A body missing `## Verification`, carrying `## Changes` before `## What changed and why`,
and holding two summary items:

```
$ BODY='...' python3 automation/check_action_projection.py \
    --from-env BODY --action-section "What to review" --queue-actor any \
    --unscoped --pull-request-body-shape --label probe-body
action-projection: 0 finding(s)
[explanation-shape] probe-body: missing section `## Verification`; `templates/pull-request.md` is the skeleton to copy  (advisory)
[explanation-shape] probe-body: section `## Changes` comes before `## What changed and why`; a reader scans these in one order and `templates/pull-request.md` sets it  (advisory)
[explanation-shape] probe-body: `## TL;DR` carries 2 numbered item(s); the schema asks for 3 to 6, each naming a state before and a state after  (advisory)
explanation-shape: 3 advisory finding(s) (not blocking)
```

Exit code: `0`. All three rule families reported; the gate's own verdict
(`action-projection: 0 finding(s)`) and its exit status are unchanged.

## Full test suite

```
$ python3 automation/run_tests.py
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
test elapsed: 106.38s
```

## New tests, run on their own

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests -k explanation_shape
............
----------------------------------------------------------------------
Ran 12 tests in 0.450s

OK
```

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests -k body_shape
..........
----------------------------------------------------------------------
Ran 10 tests in 0.718s

OK
```

```
$ python3 -m unittest automation.tests.test_pull_request_schema
............
----------------------------------------------------------------------
Ran 12 tests in 3.361s

OK
```

## CI on pull request #66

```
$ gh pr checks 66
Authoritative action projection from trusted workflow code   pass   7s
Current review-state action projection                       pass   7s
External source release admission                            pass   7s
reconcile-and-test                                           pass  34s
```

One thing that run does **not** prove, and the reason is structural: a
`pull_request_target` job runs the workflow file and checks out the gate from the *base*
branch, which is `main`. `main` does not carry `--pull-request-body-shape` yet, so this
pull request's own description was checked by the old gate and the CI log holds no
`explanation-shape:` line for it. The workflow change and the gate change land in the same
commit, so the flag and the code that reads it arrive together and the first body the
deployed rule sees is the one after this merges. The rule itself was exercised locally
against this pull request's body before it was opened:

```
$ python3 automation/check_action_projection.py --file <this PR body> \
    --action-section "What to review" --queue-actor any \
    --task-id 2026-08-02-advise-on-explanation-shape --pull-request-body-shape \
    --label draft-body
action-projection: 0 finding(s)
explanation-shape: 0 advisory finding(s) (not blocking)
```

## Review verdicts (when a review was explicitly run)

None. No adversarial panel and no independent core-fit review were run:
`automation/check_core_scope.py --require-review` was not invoked, and the repository's
`async` mode gates this change on tests plus the reconciler, both recorded above.
