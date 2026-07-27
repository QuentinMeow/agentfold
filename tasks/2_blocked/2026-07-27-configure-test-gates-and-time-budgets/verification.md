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
