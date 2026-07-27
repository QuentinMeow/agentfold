# Verification — configurable test gates and time budgets

**Verified:** 2026-07-27 by codex and delegated test agents

Only commands actually run and their real reported output are recorded here.

## Complete isolated repository suite

```
$ python3 automation/run_tests.py
15/15 selected test files passed; 297 tests; exit 0
selected-test elapsed: 157.337s
runner elapsed: 226.39s
wall elapsed: 226.47s
```

An earlier converged run also passed 15/15 files in 222.87 seconds. The later run above is the
current pre-approval baseline.

## Python 3.7 compatibility

```
$ /usr/local/opt/python/bin/python3.7 -m unittest automation.tests.test_file_test_budget_task
Ran 23 tests — OK

$ /usr/local/opt/python/bin/python3.7 -m unittest automation.tests.test_test_gate_config
Ran 28 tests — OK

$ /usr/local/opt/python/bin/python3.7 -m unittest automation.tests.test_run_test_gate
Ran 40 tests — OK (skipped=2: restricted process-inspection capability)
```

The same gate tests passed under the current Python interpreter. The two capability-skipped
containment cases were then run in an allowed environment:

```
$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 2 tests in 0.857s — OK
```

## Representative routine gates

Each command ran in its own disposable exact-candidate checkout beneath
`/private/tmp/test-gate-snapshot.0lsg8n`; the shared task index was not changed.

```
$ python3 automation/run_test_gate.py routine --staged
service-only services/quote-api/quote_api.py: exit 0, deferred
selected 2 test files; deferred 13; elapsed 7.572s / maximum 60s; filing none

$ python3 automation/run_test_gate.py routine --staged
automation-only automation/tests/test_run_tests.py: exit 0, deferred
selected 1 test file; deferred 14; elapsed 9.062s / maximum 60s; filing none

$ python3 automation/run_test_gate.py routine --staged
cross-cutting handbook/testing-gates.md plus service change: exit 0, deferred
selected 2 test files; deferred 13; elapsed 7.432s / maximum 60s; filing none
```

All three ran core-scope admission, reconciliation, and their selected tests. Every report kept
`enforcement` as `unobserved`; invocation was not presented as provider enforcement.

## Critical prewarm, exact reuse, and changed-byte rejection

```
$ python3 automation/run_test_gate.py final --explicit --staged
critical category: external-publication (.github/workflows/harness.yml)
15 selected; 0 deferred; repository-tests/full passed in 244.719s
outcome pass; elapsed 251.234s / target 300s / maximum 900s; receipt written

$ python3 automation/run_test_gate.py routine --staged
unchanged semantic staged candidate: exit 0, pass
repository-tests/full evidence reused in 0.00s; whole interval 6.43s

$ python3 automation/run_test_gate.py routine --staged
one-byte-restaged critical candidate: exit 1, blocked-incomplete
stale receipt rejected; full component contained at 53.245s; whole interval 59.571s / 60s
```

An escalated process listing after the timeout cases found no surviving gate or runner process.
The receipt binds semantic staged object ids, modes, paths, base, tested-view digest, manifest,
policy, runner, and environment. Raw Git index serialization is retained only for within-run
drift checks because Git refreshes non-semantic stat/cache bytes before a commit hook.

## Structural checks

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --check
<no output; exit 0>

$ python3 -m py_compile automation/run_test_gate.py automation/test_manifest.py automation/test_gate_config.py automation/file_test_budget_task.py automation/run_tests.py
<no output; exit 0>
```

The alternate staged-index core-scope check passed across 24 current core paths. The frozen
candidate reconciliation regression reproduced 84 false findings before the topology repair,
passed after the deterministic empty-root sentinel repair, and still failed for a genuinely
missing referenced subtree.

## Pre-staging adversarial findings

These reviews inspected a mutable working tree and therefore are not final revision-bound
approvals. The first three independent lenses all blocked; their findings were repaired with
regressions. A later fresh reviewer blocked semantic receipt identity because raw Git index
bytes change at pre-commit; that finding was repaired afterward by the same agent and is not
counted as an approval. The mutable tree has no final revision-bound approval.

The remaining known boundary is explicit: the tracked `pull_request` workflow is candidate
controlled and cannot establish configured hard enforcement. A trusted split-job provider
adapter was not added without owner approval.

## Exact checkpoint prewarm and commit-hook reuse

```
$ python3 automation/run_test_gate.py final --explicit --staged
test gate: final
outcome: pass
evidence: executed
enforcement: unobserved
reason: every required check passed
candidate: 966014b8a09a6873818a4b9291a08fe9b745728044b71a21e23a580ad9785007
component timings:
  core-scope: pass (executed, 0.38s)
  reconcile: pass (executed, 5.35s)
  repository-tests/full: pass (executed, 212.83s)
coverage: 15 selected, 0 deferred, 0 incomplete
duration: 218.94s
machine report: tmp/test-gate-reports/latest-final.json
```

```
$ git commit -m "harness: checkpoint configurable test gates"
pre-commit: routine test gate
test gate: routine
outcome: pass
evidence: executed
enforcement: unobserved
reason: every required check passed
candidate: 966014b8a09a6873818a4b9291a08fe9b745728044b71a21e23a580ad9785007
component timings:
  core-scope: pass (executed, 0.46s)
  reconcile: pass (executed, 6.14s)
  repository-tests/full: pass (reused, 0.00s)
coverage: 15 selected, 0 deferred, 0 incomplete
duration: 6.93s
pre-commit: OK
[task/2026-07-27-configure-test-gates-and-time-budgets f2d220b] harness: checkpoint configurable test gates
```

## Blocking provider review and repairs

The post-checkpoint review blocked on five concrete findings:

1. Exact-pass receipts omitted the complete safe child execution environment, so a changed
   value such as `PYTHONPATH` could reuse evidence from different execution inputs.
2. Process-group and environment-marker cleanup could miss a double-forked, re-executed daemon
   after it scrubbed the marker.
3. Multiple test files ran from one writable materialized view, allowing an earlier test to
   replace a later test before it executed.
4. The credential-free GitHub job used `env -i`, which removed variables but did not isolate
   candidate code from the host filesystem, process space, or network.
5. The workflow-token check was attributable to GitHub Actions rather than a least-privilege
   dedicated publisher App, so protected-branch admission could not bind the result to the
   intended publisher identity.

The local repairs bind the safe environment digest into receipt identity, use Linux
child-subreaper containment for provider-hard execution, report portable cleanup as best-effort,
and materialize a fresh view per test file. The provider repair runs the trusted-base controller
inside a digest-pinned one-shot Docker container with no network or host mounts, a read-only root,
bounded tmpfs and resources, exact root capabilities, and UID 65532 candidate children. It kills
and reaps that UID after every file. The publisher has no candidate artifact or checkout and uses
a protected environment to mint a repository-scoped, statuses-only GitHub App token.

The final audit additionally removed an impossible CAP_CHOWN dependency from provider scratch,
restored sealed views only after candidate cleanup, and changed the provider child environment
from arbitrary `PYTHON*` passthrough to an exact allowlist.

## Final focused provider-boundary verification

```
$ python3 automation/tests/test_run_tests.py
Ran 46 tests in 1.577s — OK

$ python3 automation/run_tests.py --test-file automation/tests/test_run_test_gate.py --test-file automation/tests/test_run_tests.py --test-file automation/tests/test_github_action_projection_workflow.py
automation/tests/test_github_action_projection_workflow.py: 14 tests in 0.032s — OK
automation/tests/test_run_test_gate.py: 44 tests in 7.047s — OK (skipped=3)
automation/tests/test_run_tests.py: 46 tests in 1.781s — OK
3/3 test files passed; elapsed 10.64s

$ python3 automation/tests/test_reconcile_queue.py
Ran 297 tests in 113.574s — OK

$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_github_adapter_binds_event_merge_and_limits_push_to_reconciliation
Ran 1 test in 0.001s — OK

$ ruby -e "require 'yaml'; YAML.load_file('.github/workflows/harness.yml'); puts 'workflow YAML OK'"
workflow YAML OK

$ python3 -m py_compile automation/run_test_gate.py automation/run_tests.py automation/tests/test_run_test_gate.py automation/tests/test_run_tests.py automation/tests/test_github_action_projection_workflow.py automation/tests/test_reconcile_queue.py
<no output; exit 0>

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --check
<no output; exit 0>
```

The 297-test reconciler run preceded the final `run_tests.py`-only CAP_CHOWN, view-restoration,
and environment-allowlist repair; its focused integration test and the structural reconciler
check passed afterward. The final isolated three-file run includes that repair.

The local macOS Docker daemon was unavailable, so no live Linux Docker execution or provider
enforcement claim is made. The workflow includes a fail-closed Docker/platform preflight; a real
provider run remains distinct from the structural and unit evidence above.

## Pending external activation boundary

`message-queue/needs-human/decisions/future-blocking-activate-github-hard-test-gate.md` separately
owns the future one-time GitHub App, protected-environment, diagnostic-pull-request, and branch-
protection setup. Until that boundary is completed and verified, these results prove the local
implementation and workflow contract only; they do not prove that GitHub currently enforces the
status for merges.

## Human-readable activation request and commit-hook cache repair

The GitHub activation request was rewritten in ordinary language while retaining the current
v1 queue schema. It now leads with the practical choice: automatically block merges unless the
complete test passes, or keep that final test manual. The queue regression suite then passed all
297 tests and the structural reconciler reported zero findings.

An exact staged final run for candidate
`ba88c925597a4934f42a8790cbf264b9c840845d55ec290db827f575a7028657` passed all 15 test
files in 248.87 seconds. The subsequent real commit hook safely rejected the commit because it
missed that exact receipt and began a duplicate full run, which reached the routine limit after
59.90 seconds. A deliberately blocked diagnostic commit proved that Git prepended its verified
`GIT_EXEC_PATH` to `PATH` inside the hook: every other binding field matched, but the component
environment digest changed from `72222f1506e39cb98877602898ab3571ac02d470cbe15251e15214eba9eca285`
to `dc69cf2dc337e25d352f0d9e8f5fdfd080652a917260ef896ac09d879f174df3`.

The repair removes that one transient prefix from the environment actually passed to test
components and therefore from its receipt identity only after all of these checks succeed: the
prefix equals `GIT_EXEC_PATH`, the Git executable found on the remaining path reports that same
exec path with configuration disabled, and Git's supplied index resolves to the repository's
real index. A mismatched executable path, path prefix, or index stays unmodified and changes the
environment identity. An actual-commit regression covers an ordinary repository, and a blocked
diagnostic commit in this linked worktree computed the original `e518aced...` binding and found
the existing receipt.

```
$ python3 -m unittest automation.tests.test_run_test_gate
Ran 46 tests in 12.692s
OK (skipped=3)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

The first exact staged run after that repair used candidate
`42a75b0a7f6bf162730234b618d8b96dd842710629c7c96e71266b7435bfa716` and failed honestly:
14 of 15 test files passed, while the new path-normalization test incorrectly assumed its
metadata-free per-test projection was a Git checkout. The full component took 295.56 seconds
and the whole gate took 309.58 seconds, exceeding the 300-second target. The configured filer
created and preserved:

- `tasks/0_backlog/2026-07-27-investigate-final-test-budget-7631c3a1b1/task.md`
- `tasks/0_backlog/2026-07-27-investigate-final-test-budget-7631c3a1b1/timing-evidence.jsonl`
- `message-queue/needs-agent/requests/non-blocking-pick-up-investigate-final-test-budget-7631c3a1b1.md`

The recorded occurrence reports 309.531811406 seconds actual, including 295.555618 seconds for
the full test component. The unit fixture was then corrected to create and explicitly bind its
own temporary Git repository; production normalization behavior was not weakened. Final exact
verification after that fixture repair is recorded below when complete.
