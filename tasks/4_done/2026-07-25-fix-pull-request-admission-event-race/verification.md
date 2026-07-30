# Verification — pin admission candidates to the event head

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output.

## Both admission jobs succeed on the first trusted event

The failure this task removed was mechanical: every freshly opened pull request
arrived with both required jobs red, and only a hand-fired `edited` event cleared
them. The evidence that it is gone is the first `pull_request_target` run of pull
requests opened after the repair reached main.

Pull request 25:

```
$ gh run view 30571521687 --json jobs -q '.jobs[] | "\(.conclusion)\t\(.name)"'
success	Authoritative action projection from trusted workflow code
success	External source release admission
skipped	reconcile-and-test
skipped	Current review-state action projection
```

Pull request 27, opened separately about 27 minutes earlier:

```
$ gh run view 30569645380 --json jobs -q '.jobs[] | "\(.conclusion)\t\(.name)"'
success	External source release admission
success	Authoritative action projection from trusted workflow code
skipped	Current review-state action projection
skipped	reconcile-and-test
```

Both jobs report success on the arrival event itself. Pull requests 25, 26, 27, 28
and 29 each show the same pair of successes on their own first trusted run
(30571521687, 30571598976, 30569645380, 30571634652, 30571715493).

## The workflow projection tests pass

```
$ python3 -m unittest automation.tests.test_github_action_projection_workflow
...............
----------------------------------------------------------------------
Ran 15 tests in 3.198s

OK
```

## The complete suite passes on the merged result

```
$ python3 automation/run_tests.py --jobs 8
...
tests: 11/11 files passed
test elapsed: 46.41s
```
