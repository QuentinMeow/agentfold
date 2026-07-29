# Verification — configurable test gates and time budgets

**Verified:** 2026-07-28 by codex and delegated test and review agents

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

## Records-only stopping package structural verification

The final staged package contains task, queue, design, plan, worklog, verification, and generated
timing-investigation records only. It contains no staged change to `agentfold.toml`, the GitHub
workflow, the gate runner, or the repository test runner. The two pre-existing waiting human
items remain byte-for-byte unchanged.

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --cached --check
<no output; exit 0>

$ git diff --cached --name-only | rg '^(agentfold\.toml|\.github/workflows/harness\.yml|automation/run_test_gate\.py|automation/run_tests\.py)$' || true
<no output; exit 0>

$ shasum -a 256 message-queue/needs-human/decisions/future-blocking-activate-github-hard-test-gate.md message-queue/needs-human/clarifications/future-blocking-confirm-hard-gate-source-branch-protection.md
ddb331a800826a460051b60875c9f8caff384612722f930ea105a97415e3c7ec  message-queue/needs-human/decisions/future-blocking-activate-github-hard-test-gate.md
d71e91da105378da82ca95ffc5662b087e7d045db0fc088feee2ef6b009a0aff  message-queue/needs-human/clarifications/future-blocking-confirm-hard-gate-source-branch-protection.md
```

## Manual-only replan stopping evidence

Two later P1 findings invalidate an automatic-enforcement claim without erasing the historical
results above:

1. The base-pinned floor prevents candidate deletion of trusted tests, but a candidate test can
   call `os._exit(0)` in the same interpreter before the assertion driver reaches a later marker.
   A zero process result therefore does not prove controlled completion.
2. The included publisher consumes that same uncontrolled result and has no external completion
   oracle. It cannot safely turn the result into a merge-authorizing status, even when its App
   credential, event identities, and source history are otherwise restricted.

The test-only migration floor was reviewed repeatedly before production work. Its current
literal-fragment cases reject a partial hard-job triad, renamed or moved known authority,
known authority duplicated outside the triad, duplicate known token/status authority inside the
publisher, and contradictory absent-regime events. A later canary still bypasses its absent
classifier with a renamed generic job using job-level `statuses: write`, the default GitHub token,
and a direct status API call. Commit `499b0e2` is therefore not a complete migration floor and
must be replaced by a closed absence rule rather than another list of literals.

```
$ python3 automation/tests/test_github_action_projection_workflow.py
Ran 17 tests in 0.094s
OK

$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_github_adapter_binds_event_merge_and_limits_push_to_reconciliation automation.tests.test_reconcile_queue.ReconcileQueueTests.test_trusted_gate_migration_never_mixes_provider_regimes
Ran 2 tests in 0.058s
OK
```

The managed safety layer refused the attempted `agentfold.toml` change from hard to manual
because the human has not authorized that persistent security-policy change. The tentative
runner/report edits were reverted immediately. No production policy, workflow, publisher,
receipt, or report schema change remains in the working tree.

The normal amend hook for test-only commit `499b0e2` passed. Its isolated candidate reconciliation
passed, while the selected queue suite reached the routine interval and was honestly deferred:

```
$ git commit --amend --no-edit
pre-commit: routine test gate
outcome: deferred
core-scope: pass (executed, 0.37s)
reconcile: pass (executed, 10.95s)
repository-tests/selected: incomplete (executed, 48.13s)
duration: 60.16s
pre-commit: OK
[task/2026-07-27-configure-test-gates-and-time-budgets 499b0e2] test: admit manual hard-gate removal floor
```

The first records-only commit attempt then stopped safely in the normal hook. Reconciliation
passed, but the required trusted-floor test component did not complete within the bounded
routine interval. No commit was created, the result was not cached as a pass, and the hook was
not bypassed.

```
$ git commit -m "harness: file manual-only test-gate replan"
pre-commit: routine test gate
outcome: blocked-incomplete
reason: required critical checks did not complete successfully: repository-tests/full
core-scope: pass (executed, 0.25s)
reconcile: pass (executed, 6.81s)
repository-tests/trusted-floor: incomplete (executed, 51.94s)
coverage: 15 selected, 0 deferred, 1 incomplete
duration: 59.87s
```

## Restacked repair focused verification

After the transitional base-test commit and the historical implementation stack were replayed,
the staged repair was applied unchanged and the focused checks were rerun against that exact
restacked working state. All checks passed. The workflow suite now contains one additional
migration-boundary test, so its current count is 17 rather than the earlier repair checkpoint's
16.

```
$ python3 -m unittest automation.tests.test_run_test_gate
Ran 49 tests in 8.162s — OK (skipped=3: platform containment)

$ python3 automation/tests/test_github_action_projection_workflow.py
Ran 17 tests in 0.031s — OK

$ python3 automation/run_tests.py --test-file automation/tests/test_run_test_gate.py --test-file automation/tests/test_run_tests.py --test-file automation/tests/test_github_action_projection_workflow.py
49 gate tests, 46 runner tests, and 17 workflow tests passed
3/3 test files passed; elapsed 13.48s

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ ruby -e "require 'yaml'; YAML.load_file('.github/workflows/harness.yml'); puts 'workflow YAML OK'"
workflow YAML OK

$ python3 -m py_compile automation/run_test_gate.py automation/tests/test_run_test_gate.py automation/tests/test_github_action_projection_workflow.py
<no output; exit 0>

$ git diff --cached --check
<no output; exit 0>

$ git diff --check
<no output; exit 0>
```

## Composite-floor integration result

The exact staged candidate `32597887788914a9f06dd1ddeedf225cac2f2e76c7684744ea764efa10dc81d1`
did not pass, and no receipt was written. Core scope passed in 0.31 seconds and reconciliation
passed in 8.84 seconds. The trusted floor ran for 387.96 seconds and failed 2 of 15 files, so the
whole gate blocked after 398.22 seconds and refreshed the existing timing investigation.

The failure is deterministic compatibility evidence. The base workflow tests contain three
assertions for the old broad `pull_request_target`/merge-group behavior, and the base reconciler
test contains one matching assertion. Those exact base tests correctly reject the repaired
workflow's narrower event/source/history boundary. Adding misleading text or dead workflow
steps merely to satisfy the old assertions would weaken the evidence, so it was not done.

The provider base is the pull request's target revision, not an earlier commit on the same head
branch. Therefore the honest migration needs a two-pull-request stack: first merge transitional
tests that accept both old and new behavior; then target the production security repair and
strict tests at that revision. Two commits inside one pull request do not advance its trusted
base and cannot solve this incompatibility.

The 297-test reconciler run preceded the final `run_tests.py`-only CAP_CHOWN, view-restoration,
and environment-allowlist repair; its focused integration test and the structural reconciler
check passed afterward. The final isolated three-file run includes that repair.

The local macOS Docker daemon was unavailable, so no live Linux Docker execution or provider
enforcement claim is made. The workflow includes a fail-closed Docker/platform preflight; a real
provider run remains distinct from the structural and unit evidence above.

## Pending external activation boundary

message-queue/needs-human/decisions/future-blocking-activate-github-hard-test-gate.md separately
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

## Immutable-checkpoint adversarial review blockers

The fresh revision-bound panel reviewed checkpoint `78a5ba2` and blocked it on two P1
findings. These verdicts supersede the earlier completion posture; this task stays in progress
until both repairs are implemented, verified, committed, and reviewed again.

1. The provider-hard final lane treated tests and helpers from the pull-request candidate as
   the complete test oracle. A candidate could delete, rename, empty, or replace those files
   and still produce the sole success evidence. The repair must run an immutable test/support
   floor from the trusted base against the exact candidate product, then run candidate-added or
   changed tests as supplemental evidence, with receipts binding both lanes and their overlays.
2. Every `pull_request_target` metadata event could reach the stable success publisher, and a
   force-pushed/non-fast-forward history could replace prior evidence. The repair must share one
   restrictive event/source-branch condition across preparation, execution, and publication,
   allow only opened or same-repository fast-forward synchronize events, and document matching
   branch-protection requirements.

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

## P1 repair focused verification

The immutable-base floor regressions cover deleted, renamed, emptied, added, and helper-shadowed
candidate tests; exact candidate product deletion remains visible beneath the floor. They also
cover an empty trusted floor failing closed and v1 receipts becoming unusable after the v2
composite identity was introduced. The workflow matrix rejects edited, ready-for-review,
review, reopened, fork, wrong-source, wrong-base, zero-before, unchanged-head, and
non-fast-forward inputs; opened and strict fast-forward synchronize inputs remain eligible.

```
$ python3 -m unittest automation.tests.test_run_test_gate
Ran 49 tests in 9.978s — OK (skipped=3: platform containment)

$ python3 automation/tests/test_github_action_projection_workflow.py
Ran 16 tests in 0.036s — OK

$ python3 automation/run_tests.py --test-file automation/tests/test_run_test_gate.py --test-file automation/tests/test_run_tests.py --test-file automation/tests/test_github_action_projection_workflow.py
49 gate tests, 46 runner tests, and 16 workflow tests passed
3/3 test files passed; elapsed 16.59s

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ ruby -e "require 'yaml'; YAML.load_file('.github/workflows/harness.yml'); puts 'workflow YAML OK'"
workflow YAML OK

$ python3 -m py_compile automation/run_test_gate.py automation/tests/test_run_test_gate.py automation/tests/test_github_action_projection_workflow.py
<no output; exit 0>

$ git diff --check
<no output; exit 0>
```

## Records-only replan checkpoint and handover

Two independent reviewers approved test-only migration snapshot `21d5a24`. This approval does
not authorize a production-policy change: the current hard workflow and policy remain unchanged
while the manual-only replan clarification is waiting.

The exact staged records candidate was prewarmed before committing. It passed all required
coverage and wrote receipt `4cc6c4a986628b2e3cc26c355bd7ac7cf2f19300b35c33a1c3a07b5e9a324951` for
candidate `aa1815f2d5fbd81d63becdc08101cca9621bae1948b1ec9f53b593b642a68242`. The 300-second
target was exceeded, so the generated final-budget evidence recorded occurrence 6; that
append-only journal is intentionally unstaged.

```
$ python3 automation/run_test_gate.py final --explicit --staged
test gate: final
outcome: pass
evidence: executed
enforcement: unobserved
candidate: aa1815f2d5fbd81d63becdc08101cca9621bae1948b1ec9f53b593b642a68242
component timings:
  core-scope: pass (executed, 0.35s)
  reconcile: pass (executed, 14.00s)
  repository-tests/trusted-floor: pass (executed, 452.26s)
  repository-tests/full: pass (executed, 0.00s)
coverage: 15 selected, 0 deferred, 0 incomplete
duration: 468.19s
target: exceeded 300.00s; budget filing updated
```

```
$ git commit -m "harness: stop unsafe automatic test-gate activation"
pre-commit: routine test gate
outcome: pass
candidate: aa1815f2d5fbd81d63becdc08101cca9621bae1948b1ec9f53b593b642a68242
repository-tests/full: pass (reused, 0.00s)
duration: 15.17s
pre-commit: OK
[task/2026-07-27-configure-test-gates-and-time-budgets 13a60b8] harness: stop unsafe automatic test-gate activation
```

## Manual-only replan response lifecycle

The owner's `yes` response was recorded in commit `bed486c` and the answered action's
`waiting` to `folding` claim was committed as `a789631`. This resolving change creates the
named ADR, updates the task-owned authorization records, and deletes the folded queue item.
It contains no production policy, configuration, workflow, publisher, or runner change.

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_human_deletion_requires_folding_and_response
Ran 1 test in 0.488s
OK

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --cached --check
<no output; exit 0>

$ python3 -m py_compile automation/reconcile/reconcile.py automation/tests/test_reconcile_queue.py
<no output; exit 0>
```

## Staged cleanup bridge: focused evidence and pre-repair final failures

This bridge invalidates the earlier test-only approval. It is the bootstrap step before the full
manual-v3 production pivot, not that production pivot, and it changes no ADR. Its classifier
admits exactly cleanup-fixed hard-v2 and manual-v3; original hard and every unlisted state fail
closed.

The first pre-repair exact staged candidate `53213fc…` did not pass. The retained evidence records
core scope passing in 0.36 seconds, reconciliation passing in 11.70 seconds, and the trusted floor
failing after 469.53 seconds at
`TestGateTests.test_maximum_terminates_the_whole_component_process_group` when `os.killpg` raised
`EPERM`. Fourteen of 15 files passed and the full gate took 483.20 seconds. Because the gate
failed, it wrote no receipt; no commit was created.

One explicitly bounded byte-identical pre-repair retry also did not pass. The retained machine
report records 499.307663 seconds (about 499.31 seconds), while the append-only timing journal
records 499.207190 seconds (about 499.21 seconds). The evidence records core scope passing in
0.35 seconds, reconciliation passing in 12.35 seconds, and the trusted floor failing after
484.97 seconds at the different test
`TestGateTests.test_index_drift_during_selected_test_timeout_blocks`, again when `os.killpg`
raised `EPERM`. Fourteen of 15 files passed. The failed gate wrote no receipt, no commit was
created, and no third retry was run.

The differing failing tests and the common `EPERM` identify a real legacy Darwin/macOS cleanup
portability defect. The staged repair covers that path in focused checks and catches
`PermissionError` only around process-group and owned-descendant signals. Direct-child
`PermissionError` and unrelated `OSError` still propagate and therefore remain fail-closed;
existing real tests are unchanged. No exact post-repair final gate has run, so its result is
unverified rather than presently proven blocked.

Focused staged implementation evidence passed: deterministic cases 4/4, real timeout cases 2/2,
classifier cases 5 direct plus 5 package, configuration cases 28 direct plus 28 package, selected
gate checks, `reconcile: 0 finding(s)`, compilation, and whitespace/diff checks. The actual
composite plan is 15 base-floor tests and 3 supplemental tests.

Independent revision-bound cleanup-semantics and migration/provider reviews both APPROVE
implementation diff `4ab89f5c…`. Their closure testing rejected 14 crossed combinations,
original hard, 8 unknown states, and 8 one-byte mutations. The reviewed implementation scope was
four files: `automation/run_test_gate.py`, the then-tracked migration snapshot helper,
`automation/tests/test_run_test_gate.py`, and `automation/tests/test_test_gate_config.py`; there
was no authority, configuration, workflow, or `automation/run_tests.py` drift. At that
cleanup-bridge checkpoint, the staged revision also included this task's `plan.md`, `worklog.md`,
and `verification.md`, for seven staged files total.

## Authorized manual-only production pivot

The first combined focused invocation did not pass: configuration had two stale hard-starter
expectations, and the gate suite exposed a macOS process-group `PermissionError` during timeout
cleanup. The expectations were corrected for the manual starter, and cleanup now proceeds to
the individually owned process when a group signal is not permitted. No full-suite result is
claimed for this checkpoint.

Historical checkpoint summary, not retained command output: the recorded invocations were
`python3 -m unittest automation.tests.test_test_gate_config` (28 tests passed),
`python3 -m unittest automation.tests.test_run_test_gate` (53 tests passed, one skipped),
`python3 -m unittest automation.tests.test_run_tests` (49 tests passed),
`python3 -m unittest automation.tests.test_github_action_projection_workflow` (18 tests passed,
six skipped), and
`python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_trusted_gate_migration_never_mixes_provider_regimes`
(one test passed). The checkpoint notes also record reconciliation with zero findings, successful
compilation and YAML parsing, and byte equality between the workflow and manual fixture. The
recorded SHA-256 for both files was
`a07b4751a93e11534586ffebe33e5a34af47f4900568493eea57bcd350a66cf1`. These sentences are result
summaries, not a reconstruction of `unittest` stdout.

During this record repair, the actual successful negative assertion
`! rg -n 'AGENTFOLD_PUBLISHER|create-github-app-token|statuses: write|api.github.com/repos/.*/statuses|prepare-trusted-final-test-gate|trusted-final-test-runner|publish-trusted-final-test-check' .github/workflows/harness.yml`
completed with exit 0 and no output against the current staged production files.

The single required normal commit attempt was not bypassed or rerun:

```
$ git commit -m "harness: make final verification manual and fail closed"
pre-commit: routine test gate
outcome: blocked-incomplete
evidence_authority: cooperative-same-interpreter
controlled_completion: false
enforcement_eligible: false
enforcement: not-enforced
reason: required critical checks did not complete successfully: repository-tests/full
core-scope: pass (executed, 0.58s)
reconcile: pass (executed, 15.29s)
repository-tests/base-pinned-floor: incomplete (executed, 42.44s)
duration: 60.19s
target: exceeded 60.00s; budget filing updated
<exit 1; no commit created>
```

## Manual-boundary documentation repair

Provider review P2 found that the staged handbook and automation contract still implied a live
configured final adapter and hard admission boundary. The repair makes final evidence
explicit-only, describes `hard` plus its pull-request trigger as reserved future-compatible
syntax, and states that the cooperative floor cannot admit or reject a protected transition.
No full suite was run for this documentation-only repair.

```
$ ! rg -n -i 'configured final adapter|base hard boundary|boundary that admits it|This deliberately enforces backwards-compatible|is rejected because the older base-pinned' handbook/testing-gates.md automation/AGENTS.md tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/plan.md
<no matches; exit 0>

$ rg -n -i 'explicit final command|fail closed before candidate execution|future policy intent|checks cooperatively|not a live provider boundary|cannot reject or admit a protected transition' handbook/testing-gates.md automation/AGENTS.md tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/plan.md
<matching manual-boundary statements; exit 0>

$ python3 -m unittest automation.tests.test_test_gate_config automation.tests.test_github_action_projection_workflow
Ran 46 tests in 0.213s
OK (skipped=6)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --check
<no output; exit 0>

$ git diff --cached --check
<no output; exit 0>
```

## Portable cleanup snapshot repair

The non-`/proc` path now takes one bounded `ps eww` snapshot for ancestry and exact same-UID
ownership-token discovery. It preserves 100 ms before cleanup deadline, 50 ms for `SIGTERM`, and
50 ms for unconditional final `SIGKILL`/reap. This is focused verification only; no complete gate
or full repository suite is claimed.

```
$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_discovers_ancestry_and_exact_same_user_token_once automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_is_capped_at_300ms automation.tests.test_run_test_gate.TestGateTests.test_linux_discovery_does_not_use_portable_snapshot automation.tests.test_run_test_gate.TestGateTests.test_cleanup_kills_first_owned_snapshot_before_rescanning automation.tests.test_run_test_gate.TestGateTests.test_cleanup_reserves_snapshot_and_final_kill_time
Ran 5 tests in 0.008s
OK

$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_maximum_terminates_the_whole_component_process_group automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 3 tests in 1.374s
OK

$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_maximum_terminates_the_whole_component_process_group automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 3 tests in 1.382s
OK

$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_maximum_terminates_the_whole_component_process_group automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 3 tests in 1.384s
OK

$ python3 -m unittest automation.tests.test_run_test_gate
Ran 63 tests in 16.599s
OK (skipped=1)

$ python3 -m unittest automation.tests.test_test_gate_config
Ran 28 tests in 0.204s
OK

$ python3 -m unittest automation.tests.test_run_tests
Ran 49 tests in 3.198s
OK

$ python3 -m unittest automation.tests.test_github_action_projection_workflow
Ran 18 tests in 0.043s
OK (skipped=6)

$ python3 -m py_compile automation/run_test_gate.py automation/tests/test_run_test_gate.py
<no output; exit 0>

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --check
<no output; exit 0>
```

An additional package-form rerun also passed. The record does not establish which direct-script
run, if any, immediately preceded it. Its expected parser diagnostics and a subprocess
`ResourceWarning` did not fail a test.

```
$ python3 -m unittest automation.tests.test_run_test_gate
Ran 63 tests in 17.106s
OK (skipped=1)
```

## Manual-boundary line-budget repair

The first post-repair review found one line-budget finding. The working file was compressed from
61 to 60 lines without changing the explicit-only/manual-boundary meaning. The rerun below is
against the staged repaired candidate; no full suite was run.

```
$ wc -l automation/AGENTS.md
61 automation/AGENTS.md

$ python3 automation/reconcile/reconcile.py --check
[agents-budget] automation/AGENTS.md: 61 lines exceeds the 60-line budget
reconcile: 1 finding(s)

$ wc -l automation/AGENTS.md
60 automation/AGENTS.md

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --check
<no output; exit 0>

$ git diff --cached --check
<no output; exit 0>
```

## Cleanup bootstrap completion and phase-2 boundary

The cleanup-only bootstrap candidate subsequently passed its exact final gate and was committed
as `c78a8d6`. This evidence belongs to the cleanup bridge, not to the re-applied production pivot.

```
$ python3 automation/run_test_gate.py final --explicit --staged
outcome: pass
candidate: 2c7bcc1366ea9611976de5989d3e3fcc079a9870ecb6072a7d9e1b6c1d7e0af6
core-scope: pass (executed, 0.44s)
reconcile: pass (executed, 14.76s)
repository-tests/base-pinned-floor: pass (executed, 484.83s)
repository-tests/supplemental: pass (executed, 23.91s)
coverage: 16 selected, 0 deferred, 0 incomplete
duration: 525.67s

$ git commit -m "fix: stabilize gate cleanup during migration"
pre-commit: routine test gate
repository-tests/full: pass (reused)
duration: 16.63s
[task/2026-07-27-configure-test-gates-and-time-budgets c78a8d6] fix: stabilize gate cleanup during migration
```

The phase-2 manual-v3 production pivot has not received an exact final or full-suite pass. Only
the focused checks recorded after this section apply to it; no production commit, push, or hard
enforcement claim is made.

## Phase-2 focused reapplication checks

The first direct gate run found one synthetic-fixture ordering mismatch after the retired
migration-helper filename was replaced; changing the generic fixture name restored the asserted
lexicographic order. The first reconciler run then found one historical backticked path to that
deleted helper; describing it as the then-tracked helper removed the stale live-path claim. The
record-repair results below supersede that summary.

`python3 automation/tests/test_test_gate_config.py` passed 28 tests in 0.425 seconds, and
`python3 -m unittest automation.tests.test_test_gate_config` passed 28 tests in 0.398 seconds.
`python3 automation/tests/test_run_tests.py` passed 49 tests in 4.620 seconds, and
`python3 -m unittest automation.tests.test_run_tests` passed 49 tests in 5.616 seconds.
`python3 automation/tests/test_github_action_projection_workflow.py` passed 18 tests in 0.088
seconds with six skipped, and
`python3 -m unittest automation.tests.test_github_action_projection_workflow` passed 18 tests in
0.106 seconds with six skipped. The focused queue command
`python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_trusted_gate_migration_never_mixes_provider_regimes`
passed one test in 0.024 seconds.

The six-test command covering cleanup error handling and the two automatic-transition
pre-execution boundaries passed six tests in 0.021 seconds. Its exact invocation was
`python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_group_permission_error_continues_root_and_owned_signals automation.tests.test_run_test_gate.TestGateTests.test_owned_permission_error_is_tolerated_and_cleanup_continues automation.tests.test_run_test_gate.TestGateTests.test_direct_root_permission_error_propagates automation.tests.test_run_test_gate.TestGateTests.test_unrelated_group_signal_error_propagates automation.tests.test_run_test_gate.TestGateTests.test_automatic_transition_blocks_before_candidate_execution_or_receipt automation.tests.test_run_test_gate.TestGateTests.test_provider_hard_blocks_at_the_same_pre_execution_boundary`.
The exact runner command
`python3 -m unittest automation.tests.test_run_tests.StagedTestSelectionTests.test_provider_hard_fails_closed_before_discovery_or_preflight automation.tests.test_run_tests.RunTestsIsolationTests.test_same_interpreter_test_can_exit_zero_before_a_completion_marker`
passed two tests in 0.260 seconds.

The wider gate module did not pass during this record repair. The first two invocations were
launched concurrently, so they are retained as interference-prone evidence rather than as a
readiness result. `python3 automation/tests/test_run_test_gate.py` ran 58 tests in 24.335 seconds
and exited 1 with one failure, `test_reparented_daemon_is_found_by_gate_ownership_token`, and one
skip. `python3 -m unittest automation.tests.test_run_test_gate` ran 58 tests in 24.906 seconds and
exited 1 with the same failure and one skip. A subsequent sequential retry of
`python3 automation/tests/test_run_test_gate.py` ran 58 tests in 20.849 seconds and exited 1 with
two failures, `test_reparented_daemon_is_found_by_gate_ownership_token` and
`test_setsid_escaped_child_holding_output_cannot_block_cleanup`, and one skip. There was no
sequential package retry. These actual failures supersede the earlier pseudo-pass summary and
mean phase 2 is not ready for complete verification.

The structural commands and negative assertions run after this record edit are recorded in the
next section with their real exit status and output.

An actual staged composite-plan inspection against base `c78a8d6` found 16 base-floor tests and
four supplemental tests: the workflow, gate, runner, and configuration suites. The retired
migration snapshot remains only in the immutable base floor for this transition; it is deleted
from the candidate and no candidate production assertion imports it or conditionally admits the
hard-v2 regime. Phase 2 remains without a full-suite or exact-final result.

## Record-repair structural checks

The exact command `python3 automation/reconcile/reconcile.py --check` completed with exit 0 and
printed `reconcile: 0 finding(s)`. Both `git diff --cached --check` and `git diff --check`
completed with exit 0 and no output. Compilation of the gate, runner, configuration, and their
focused test modules completed with exit 0 and no output. YAML parsing and
`cmp -s .github/workflows/harness.yml automation/tests/fixtures/manual-harness.yml` also completed
with exit 0 and no output. `shasum -a 256 .github/workflows/harness.yml` printed
`a07b4751a93e11534586ffebe33e5a34af47f4900568493eea57bcd350a66cf1  .github/workflows/harness.yml`,
and `wc -l automation/AGENTS.md` printed `60 automation/AGENTS.md` with leading spacing before 60.

Both actual negative assertions completed with exit 0 and no output:
`! rg -n 'AGENTFOLD_PUBLISHER|create-github-app-token|statuses: write|api.github.com/repos/.*/statuses|prepare-trusted-final-test-gate|trusted-final-test-runner|publish-trusted-final-test-check' .github/workflows/harness.yml`
and
`! rg -n 'test_gate_migration_snapshots|MIGRATION_EXPECTATIONS|MIGRATION_REGIME' automation/tests/test_run_test_gate.py automation/tests/test_test_gate_config.py`.

## Portable cleanup late-discovery repair

Blocking review reproduced a PID-discovery race: the old rescan loop could discover a late PID
in `live_owned` and exit without merging or killing it. The repaired loop performs exactly one
discover/merge/kill/reap sequence per iteration. The first focused run had one test-only Python
3.7 mock-call accessor error; the corrected command and all later commands passed. No exact-final
gate or full repository suite was run.

```
$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_discovers_ancestry_and_exact_same_user_token_once automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_is_capped_at_300ms automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_accepts_delayed_completion_within_budget automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_timeout_returns_no_unbounded_discovery automation.tests.test_run_test_gate.TestGateTests.test_linux_discovery_does_not_use_portable_snapshot automation.tests.test_run_test_gate.TestGateTests.test_cleanup_kills_first_owned_snapshot_before_rescanning automation.tests.test_run_test_gate.TestGateTests.test_cleanup_reserves_snapshot_and_final_kill_time
Ran 7 tests in 0.174s
OK

$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 2 tests in 1.211s
OK

$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 2 tests in 1.022s
OK

$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 2 tests in 1.021s
OK

$ python3 automation/tests/test_run_test_gate.py
Ran 65 tests in 16.789s
OK (skipped=1)

$ python3 -m unittest automation.tests.test_run_test_gate
Ran 65 tests in 18.430s
OK (skipped=1)

$ python3 -m unittest automation.tests.test_test_gate_config
Ran 28 tests in 0.237s
OK

$ python3 -m unittest automation.tests.test_run_tests
Ran 49 tests in 3.585s
OK

$ python3 -m unittest automation.tests.test_github_action_projection_workflow
Ran 18 tests in 0.052s
OK (skipped=6)

$ python3 -m py_compile automation/run_test_gate.py automation/tests/test_run_test_gate.py
<no output; exit 0>

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --check
<no output; exit 0>

$ git diff --cached --check
<no output; exit 0>
```

## Completed-snapshot deadline repair

The deadline now gates only portable snapshot acquisition. A snapshot that has already returned
is parsed even when its completion advances the clock exactly to the scan deadline. No exact-final
gate or full repository suite was run.

```
$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_discovers_ancestry_and_exact_same_user_token_once automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_is_capped_at_300ms automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_accepts_delayed_completion_within_budget automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_timeout_returns_no_unbounded_discovery automation.tests.test_run_test_gate.TestGateTests.test_completed_portable_snapshot_is_consumed_at_exact_deadline automation.tests.test_run_test_gate.TestGateTests.test_linux_discovery_does_not_use_portable_snapshot automation.tests.test_run_test_gate.TestGateTests.test_cleanup_kills_first_owned_snapshot_before_rescanning automation.tests.test_run_test_gate.TestGateTests.test_cleanup_reserves_snapshot_and_final_kill_time
Ran 8 tests in 0.174s
OK

$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 2 tests in 1.013s
OK

$ python3 automation/tests/test_run_test_gate.py
Ran 66 tests in 16.548s
OK (skipped=1)

$ python3 -m unittest automation.tests.test_run_test_gate
Ran 66 tests in 16.716s
OK (skipped=1)

$ python3 -m unittest automation.tests.test_test_gate_config
Ran 28 tests in 0.235s
OK

$ python3 -m unittest automation.tests.test_run_tests
Ran 49 tests in 3.444s
OK

$ python3 -m unittest automation.tests.test_github_action_projection_workflow
Ran 18 tests in 0.051s
OK (skipped=6)

$ python3 -m py_compile automation/run_test_gate.py automation/tests/test_run_test_gate.py
<no output; exit 0>

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --check
<no output; exit 0>

$ git diff --cached --check
<no output; exit 0>
```

## Refreshed compatibility-floor bootstrap

Commit `7d580d3` resolved the immutable-floor compatibility blocker with one refreshed helper file
(14 additions, one deletion). This exact evidence covers that test-only refresh candidate, not
the subsequently re-applied production pivot.

```
$ python3 automation/run_test_gate.py final --explicit --staged
outcome: pass
candidate: ac6b07653007b516efaabb23f78e91ca3dcb25e9ad082681b2cc37b9b317d094
core-scope: pass (executed, 0.49s)
reconcile: pass (executed, 16.49s)
repository-tests/trusted-floor: pass (executed, 477.62s)
repository-tests/candidate-supplemental: pass (executed, 0.86s)
repository-tests/full: pass (executed, 0.00s)
coverage: 16 selected, 0 deferred, 0 incomplete
duration: 497.64s

$ git commit -m "test: refresh manual gate migration floor"
pre-commit: routine test gate
repository-tests/full: pass (reused, 0.00s)
duration: 15.28s
[task/2026-07-27-configure-test-gates-and-time-budgets 7d580d3] test: refresh manual gate migration floor
```

The protected manual-v3 production candidate was re-applied only after this commit. It has no
exact-final or full-suite result; focused checks below do not upgrade the refresh evidence into a
production verification claim, and the task remains in progress.

## Protected production reapplication focused checks

The actual staged composite plan used base `7d580d3`, contained 16 immutable-floor tests, and
selected exactly four supplemental suites: workflow, gate, runner, and configuration. The
refreshed migration helper was absent from candidate bytes but present in the immutable floor;
running that exact floor helper against the repaired manual tuple passed six tests. Its
classifier therefore accepts gate hash `a27b85…` at the intended transition. The plan reported
no support-changed namespace.

```
$ python3 automation/tests/test_run_test_gate.py
Ran 66 tests in 18.380s
OK (skipped=1)

$ python3 -m unittest automation.tests.test_run_test_gate
Ran 66 tests in 18.866s
OK (skipped=1)

$ python3 automation/tests/test_test_gate_config.py
Ran 28 tests in 0.261s
OK
$ python3 -m unittest automation.tests.test_test_gate_config
Ran 28 tests in 0.200s
OK

$ python3 automation/tests/test_run_tests.py
Ran 49 tests in 3.349s
OK
$ python3 -m unittest automation.tests.test_run_tests
Ran 49 tests in 3.327s
OK

$ python3 automation/tests/test_github_action_projection_workflow.py
Ran 18 tests in 0.056s
OK (skipped=6)
$ python3 -m unittest automation.tests.test_github_action_projection_workflow
Ran 18 tests in 0.043s
OK (skipped=6)

$ python3 automation/run_tests.py --test-file automation/tests/test_github_action_projection_workflow.py --test-file automation/tests/test_run_test_gate.py --test-file automation/tests/test_run_tests.py --test-file automation/tests/test_test_gate_config.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_run_test_gate.py
PASS automation/tests/test_run_tests.py
PASS automation/tests/test_test_gate_config.py
tests: 4/4 files passed
test elapsed: 28.47s

$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_discovers_ancestry_and_exact_same_user_token_once automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_is_capped_at_300ms automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_accepts_delayed_completion_within_budget automation.tests.test_run_test_gate.TestGateTests.test_portable_snapshot_timeout_returns_no_unbounded_discovery automation.tests.test_run_test_gate.TestGateTests.test_completed_portable_snapshot_is_consumed_at_exact_deadline automation.tests.test_run_test_gate.TestGateTests.test_linux_discovery_does_not_use_portable_snapshot automation.tests.test_run_test_gate.TestGateTests.test_cleanup_kills_first_owned_snapshot_before_rescanning automation.tests.test_run_test_gate.TestGateTests.test_cleanup_reserves_snapshot_and_final_kill_time
Ran 8 tests in 0.171s
OK
$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_setsid_escaped_child_holding_output_cannot_block_cleanup automation.tests.test_run_test_gate.TestGateTests.test_reparented_daemon_is_found_by_gate_ownership_token
Ran 2 tests in 0.790s
OK
```

The first reconciler invocation after adding the refresh record found only a newly backticked
component label that looked like a missing path. Rendering repository-tests/full as plain prose
fixed that record-only issue. Phase 2 still has no exact-final or full repository-suite run.

## Unanimous merge-review blockers

The revision-bound panel reviewed Git range `e530c428..64490ab5`. Majority result: 0 approve, 5 block.

- `panel_correctness` — correctness — BLOCK: terminal accounting can contradict the reported terminal outcome.
- `panel_authority` — authority — BLOCK: the authority guard is not pre-import, and the obsolete pull-request check remains live.
- `panel_evidence` — cache/migration — BLOCK: unstaged drift can escape receipt identity, and candidate-only namespaces can escape complete coverage.
- `panel_contract` — contract — BLOCK: cache semantics, pull-request admission, and obsolete human asks do not match the stated contract.
- `panel_blast_radius` — blast-radius — BLOCK: pull-request admission and working-state drift leave a wider unsafe impact than claimed.

## Superseded hard-gate ask lifecycle

The response-transcription commit `b826df7` changed only the two blank human response fields.
Its normal hook passed the routine gate in 17.69 seconds with cooperative, non-enforcing
evidence. The status-only claim commit `d5aefe3` changed only `waiting` to `folding`; its normal
hook passed the same gate in 15.54 seconds. The resolving candidate creates the predeclared ADR,
removes both claimed items, and regenerates `memory/index.md`.

## Current implementation — focused executable evidence

```
$ set -o pipefail
$ python3 automation/tests/test_run_test_gate.py 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 102 tests in 37.456s

OK (skipped=1)

$ set -o pipefail
$ python3 -m unittest automation.tests.test_run_test_gate 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 102 tests in 37.466s

OK (skipped=1)
```

```
$ set -o pipefail
$ python3 -m unittest automation.tests.test_run_test_gate.TestGateTests.test_stdout_is_outside_the_frozen_measured_interval automation.tests.test_run_test_gate.TestGateTests.test_projection_is_single_and_outside_terminal_accounting automation.tests.test_run_test_gate.TestGateTests.test_gate_interval_start_requires_valid_handoff_monotonic_time automation.tests.test_run_test_gate.TestGateTests.test_cross_process_clock_fallback_survives_different_monotonic_epochs automation.tests.test_run_test_gate.TestGateTests.test_cross_process_clock_mismatch_and_unavailability_block automation.tests.test_run_test_gate.TestGateTests.test_bootstrap_elapsed_counts_toward_maximum_before_components automation.tests.test_run_test_gate.TestGateTests.test_receipt_projects_only_after_terminal_full_composite_pass automation.tests.test_run_test_gate.TestGateTests.test_broken_stdout_never_commits_receipt_even_if_cleanup_and_rewrite_fail automation.tests.test_run_test_gate.TestGateTests.test_marker_write_failure_invalidates_receipt_and_reports_command_error automation.tests.test_run_test_gate.TestGateTests.test_marker_directory_fsync_failure_after_rename_keeps_committed_pass automation.tests.test_run_test_gate.TestGateTests.test_marker_file_fsync_failure_before_rename_fails_publication automation.tests.test_run_test_gate.TestGateTests.test_marker_directory_close_failure_after_rename_keeps_committed_pass automation.tests.test_run_test_gate.TestGateTests.test_marker_file_close_failure_before_rename_fails_publication automation.tests.test_run_test_gate.TestGateTests.test_receipt_requires_matching_publication_commit_marker 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 14 tests in 3.291s

OK
```

```
$ set -o pipefail
$ python3 automation/tests/test_run_tests.py 2>&1 | tail -n 12
test_run_tests.py: error: --provider-hard requires an explicit view and test manifest
.usage: test_run_tests.py [-h] [--staged] [--view-root VIEW_ROOT]
                         [--test-file TEST_FILE]
test_run_tests.py: error: --staged cannot be combined with --view-root or --test-file
...
----------------------------------------------------------------------
Ran 52 tests in 2.284s

OK
PASS automation/tests/test_early_exit.py
tests: 1/1 files passed
test elapsed: 0.13s

$ set -o pipefail
$ python3 -m unittest automation.tests.test_run_tests 2>&1 | tail -n 12
python3.7 -m unittest: error: --provider-hard requires an explicit view and test manifest
.usage: python3.7 -m unittest [-h] [--staged] [--view-root VIEW_ROOT]
                             [--test-file TEST_FILE]
python3.7 -m unittest: error: --staged cannot be combined with --view-root or --test-file
...
----------------------------------------------------------------------
Ran 52 tests in 2.232s

OK
PASS automation/tests/test_early_exit.py
tests: 1/1 files passed
test elapsed: 0.13s
```

```
$ set -o pipefail
$ python3 automation/tests/test_test_gate_config.py 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 28 tests in 0.093s

OK

$ set -o pipefail
$ python3 -m unittest automation.tests.test_test_gate_config 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 28 tests in 0.093s

OK
```

```
$ set -o pipefail
$ python3 automation/tests/test_github_action_projection_workflow.py 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 18 tests in 0.032s

OK (skipped=6)

$ set -o pipefail
$ python3 automation/tests/test_harness_workflow.py 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 8 tests in 0.214s

OK

$ set -o pipefail
$ python3 -m unittest automation.tests.test_github_action_projection_workflow automation.tests.test_harness_workflow 2>&1 | tail -n 4
----------------------------------------------------------------------
Ran 26 tests in 0.249s

OK (skipped=6)
```

The two standalone selector commands below intentionally supplied the same files in opposite
argument orders. Their retained output is recorded in full.

```
$ python3 automation/run_tests.py --test-file services/quote-cli/tests/test_quote_cli.py --test-file services/quote-api/tests/test_quote_api.py
test lane: explicit-view
test reason: gate supplied an exact tested view and manifest
evidence authority: cooperative-same-interpreter
controlled completion: false
enforcement eligible: false
selected test files:
  services/quote-api/tests/test_quote_api.py
  services/quote-cli/tests/test_quote_cli.py
.....
----------------------------------------------------------------------
Ran 5 tests in 0.111s

OK
...
----------------------------------------------------------------------
Ran 3 tests in 0.308s

OK
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 2/2 files passed
test elapsed: 1.70s

$ python3 automation/run_tests.py --test-file services/quote-api/tests/test_quote_api.py --test-file services/quote-cli/tests/test_quote_cli.py
test lane: explicit-view
test reason: gate supplied an exact tested view and manifest
evidence authority: cooperative-same-interpreter
controlled completion: false
enforcement eligible: false
selected test files:
  services/quote-api/tests/test_quote_api.py
  services/quote-cli/tests/test_quote_cli.py
.....
----------------------------------------------------------------------
Ran 5 tests in 0.117s

OK
...
----------------------------------------------------------------------
Ran 3 tests in 0.286s

OK
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 2/2 files passed
test elapsed: 1.62s
```

## Current provider read-only evidence

```
$ date -u '+%Y-%m-%dT%H:%M:%SZ'
2026-07-28T22:46:44Z
```

```
$ gh api repos/QuentinMeow/agentfold/branches/main/protection --jq '{required_status_checks: .required_status_checks}'
gh: Branch not protected (HTTP 404)
{"message":"Branch not protected","documentation_url":"https://docs.github.com/rest/branches/branch-protection#get-branch-protection","status":"404"}
```

Exit status: `1`.

```
$ gh api repos/QuentinMeow/agentfold/branches/main/protection/required_status_checks --jq '{strict: .strict, contexts: .contexts, checks: .checks}'
gh: Branch not protected (HTTP 404)
{"message":"Branch not protected","documentation_url":"https://docs.github.com/rest/branches/branch-protection#get-status-checks-protection","status":"404"}
```

Exit status: `1`.

```
$ gh api repos/QuentinMeow/agentfold/rulesets/19582703 --jq '{id, name, enforcement, target, conditions, rules: [.rules[] | {type, parameters: (.parameters // null)}]}'
{"conditions":{"ref_name":{"exclude":[],"include":["~DEFAULT_BRANCH"]}},"enforcement":"disabled","id":19582703,"name":"main-projection","rules":[{"parameters":null,"type":"deletion"},{"parameters":null,"type":"non_fast_forward"}],"target":"branch"}

$ gh api repos/QuentinMeow/agentfold/rules/branches/main --jq 'map({type, ruleset_source_type, ruleset_source, ruleset_id})'
[]

$ gh pr list --repo QuentinMeow/agentfold --head task/2026-07-27-configure-test-gates-and-time-budgets --state open --json number,url --jq '.'
[]
```

## Current structural evidence

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ wc -l automation/AGENTS.md
      60 automation/AGENTS.md
```

`git diff --check` and `git diff --cached --check` each exited 0 with empty output.

The active-contract stale search was run exactly as follows and exited 0 with empty output:

```
$ if rg -n 'receipt schema v4|Version 4 receipts|v4 receipt|POSIX and Windows|Windows clones|including (report|reporting)|reporting (inside|within)|end-to-end budget|report persistence.*interval|projection.*measured interval|whole gate.*report' automation/AGENTS.md handbook/testing-gates.md tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/task.md tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/design.md tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/plan.md; then exit 1; fi

$ if rg -n 'Ran 9(2|8) tests' tasks/1_in-progress/2026-07-27-configure-test-gates-and-time-budgets/verification.md; then exit 1; fi
```

## Remaining verification boundary

No exact final gate, full repository suite, production commit hook, or fresh revision-bound merge
review has run after the unanimous-blocker repairs. Those steps remain required before completion
or merge. The focused commands above are not complete-suite or commit evidence.

## Failed exact-final core-scope admission

The actual attempted command was:

```
$ python3 -I -S automation/run_test_gate.py final --explicit --staged
```

It exited 1. Its retained machine report is
`tmp/test-gate-reports/latest-final.json`. The following read-only extraction was then run against
that report; the output is retained verbatim.

```
$ jq '{schema,gate_id,outcome,gate_exit_code,command_outcome,exit_code,reason,candidate:.candidate.digest,core_scope:(.components[0] | {component_id,outcome,evidence,duration_seconds:((.duration_seconds*100|round)/100),detail}),coverage:{selected:(.selected|length),deferred:(.deferred|length),incomplete:(.incomplete|length),incomplete_ids:.incomplete},duration_seconds:((.duration_seconds*100|round)/100),report_write,receipt:(.receipt // null),publication_commit_marker:(.publication_commit_marker // null)}' tmp/test-gate-reports/latest-final.json
{
  "schema": "agentfold.test-gate-report/v3",
  "gate_id": "final",
  "outcome": "blocked-failed",
  "gate_exit_code": 1,
  "command_outcome": "blocked-failed",
  "exit_code": 1,
  "reason": "core-scope failed",
  "candidate": "e5283a0356dc656805bc925a6bbc6190f6bb38c6f66df2c6b7c6b9145dcc04c6",
  "core_scope": {
    "component_id": "core-scope",
    "outcome": "failed",
    "evidence": "executed",
    "duration_seconds": 0.77,
    "detail": "[core-scope] Core fit requires `**User-global writes:** none`\n[core-scope] `**Thin adapter:**` must be `none` or exact nonempty canonical=, optional=yes, policy=none, writes=repo-only pairs\n    fix: complete templates/task/design.md, route external setup outside core, or record review when --require-review is selected"
  },
  "coverage": {
    "selected": 16,
    "deferred": 0,
    "incomplete": 3,
    "incomplete_ids": [
      "core-scope",
      "reconcile",
      "repository-tests/full"
    ]
  },
  "duration_seconds": 4.63,
  "report_write": {
    "disposition": "written"
  },
  "receipt": null,
  "publication_commit_marker": null
}
```

No commit or new retry was created. This is failed admission evidence, not an exact-final or full
repository-suite pass.

## Core-scope receipt repair checks

```
$ python3 automation/check_core_scope.py --staged
core-scope: pass (12 core path(s), task 2026-07-27-configure-test-gates-and-time-budgets; independent review manual; not invoked)

$ python3 -m unittest automation.tests.test_check_core_scope.CoreScopeTests.test_user_global_write_declaration_must_be_none automation.tests.test_check_core_scope.CoreScopeTests.test_thin_adapter_contract_is_structured automation.tests.test_check_core_scope.CoreScopeTests.test_thin_adapter_values_are_exact_and_nonempty
...
----------------------------------------------------------------------
Ran 3 tests in 0.021s

OK
```

These focused checks repair only the core-scope receipt failure. They are not an exact-final or
full repository-suite pass, and the independent revision-bound review was not invoked.

## Exact-final attempt reached incompatible trusted tests

The next actual invocation was:

```
$ python3 -I -S automation/run_test_gate.py final --explicit --staged
```

Candidate `a6bd61f918885c703a201b63062372528b01103825783bdaa81efb9c6e9303a1`
exited 1 after 544.18 seconds. Core scope passed in 0.75 seconds and reconciliation passed in
16.41 seconds. The base-pinned floor then failed after 521.05 seconds: 11 of its 15 files passed,
while these four files failed against the new production contract:

- `automation/tests/test_github_action_projection_workflow.py`
- `automation/tests/test_reconcile_queue.py`
- `automation/tests/test_run_test_gate.py`
- `automation/tests/test_run_tests.py`

The attempt selected 16 files, deferred none, and left the full repository check incomplete. It
created no receipt, publication marker, or commit. The failure showed that the trusted tests
needed an exact compatibility bridge; rerunning the unchanged candidate would not have helped.

## First compatibility-bridge attempt exceeded the final maximum

After adding the first version of that bridge, the same actual command ran against candidate
`11bd3c5c7927aeb99798f4cfa370a94d4582f95791b76244526dd398a027696c`:

```
$ python3 -I -S automation/run_test_gate.py final --explicit --staged
```

It exited 1 after 900.039886 seconds (900.04 seconds rounded). Core scope passed in 0.45 seconds,
reconciliation passed in 16.74 seconds, and all 15 base-floor files passed in 535.98 seconds. The
candidate supplemental lane was still incomplete after 344.70 seconds. The run selected 16 files
and created no receipt, publication marker, or commit.

The bridge behavior was correct, but its file layout made the run much larger than intended. The
helper name accidentally matched the migration critical glob, and the changed shared support
file caused all 14 automation test modules to run again in the supplemental lane. The repair was
to give the bridge a normal test-module name and keep its shared support byte-identical.

## Committed compatibility bridge

The repaired bridge was checked directly before commit `fcc8d8dee7923d54c2ce15abd2de4a1ca678e85f`.
The retained command evidence is below. Lines labeled `result summary` summarize the observed
exit, case count, and wall time; they are not claimed as literal program output. The reconciler's
zero-finding line is labeled separately as emitted output.

```
$ python3 -m unittest automation.tests.test_gate_generations
[result summary] exit 0; 5/5 passed; command elapsed: 0.08s

$ python3 -m unittest automation.tests.test_github_action_projection_workflow
[result summary] exit 0; 18/18 passed with 6 pre-existing skips; command elapsed: 0.11s

$ python3 -m unittest -q automation.tests.test_reconcile_queue
[result summary] clean exit 0; loader count: 298 cases; the quiet command emitted no final
summary; command elapsed: about 28.6s

$ python3 -m unittest automation.tests.test_run_test_gate
[result summary] exit 0; 66/66 passed with 1 pre-existing skip; command elapsed: 11.04s

$ python3 -m unittest automation.tests.test_run_tests
[result summary] exit 0; 49/49 passed; command elapsed: 2.04s

$ python3 automation/reconcile/reconcile.py --check
[emitted output] reconcile: 0 finding(s)
[result summary] exit 0; command elapsed: 8.14s
```

The staged and unstaged diff checks were clean for the intended bridge scope. Its normal commit
hook also succeeded without claiming complete coverage:

```
gate_id="routine"
outcome="deferred"
reason="reversible remainder deferred after repository-tests/selected"
duration_seconds=59.758121
```

The hook passed core scope and reconciliation, then stopped the reversible selected-test
remainder at the routine boundary. Commit `fcc8d8d` was created. This is successful routine-gate
deferral evidence, not a complete final-gate pass for the staged production change.

## Historical exact-final pass and production commit — reconstructed record

The command below actually ran before the product commit:

```
$ python3 -I -S automation/run_test_gate.py final --explicit --staged
```

Its byte-exact stdout was not retained. The fixed `latest-final.json` path was later overwritten
by another diagnostic run, so the complete original final report and the original three-file
receipt/report/marker set are not recoverable. The following lines are explicitly reconstructed
facts, not literal command output. They come from the append-only final-budget journal, the
surviving v5 receipt and v1 publication marker, the retained routine report, and Git metadata:

```
[reconstructed fact] candidate digest:
843a44a38f328ebde40d34f759d8592847175bd4e9d65f27301f5c6d9b710b53
[reconstructed fact] candidate closure digest:
e975972cfa87f4f470c548a7d7c743688ea5f0add01ea4196d767cfc0a13a855
[reconstructed fact] gate result: pass; actual duration: 432.51825652701s;
configured final target: 300.0s
[reconstructed fact] component durations: core-scope 0.6799s; reconcile 17.329837s;
repository-tests/base-pinned-floor 372.917033s;
repository-tests/candidate-supplemental 34.905171s; repository-tests/full 0.0s
[reconstructed fact] coverage reviewed by the panel: 17 test files; 0 deferred; 0 incomplete
[reconstructed fact] v5 receipt binding digest:
aa49e2e680bcc4cc7cc6fdfe1d854a28de81cf69cfb5d9f76310fcd492d20d4b
[reconstructed fact] receipt controller-closure digest:
cd54e785a62fdbe08846b13a9bce5579b6db9793283ec1839586dea78057d973
[reconstructed fact] publication id:
6a8300a56f679dad5da7d35c39608a288b18d0b0f3d2e175286fa16fa8c3f2f9
[reconstructed fact] publication marker receipt digest:
4a6d49f138a9e0fe15f94b836430f69ea2477417d7215de9a78e81d953dc4104
[reconstructed fact] publication marker report digest:
454d5b5d08f34ec0ec9db2c3428630ac165856cddedb6cd08db73478570f0a0a
[reconstructed fact] timing-filer receipt field:
05e9db92f8393233881d796a4d0c15e0392f11d1e655ac0571c5bdbbf4ebebb9
```

The final target breach was durably appended as occurrence 5 in
`tasks/0_backlog/2026-07-27-investigate-final-test-budget-7631c3a1b1/timing-evidence.jsonl`.
The receipt labels the result `cooperative-same-interpreter`, with
`controlled_completion: false` and `enforcement_eligible: false`; this was never automatic
enforcement evidence.

The normal hook for the product commit used the exact same candidate and closure. The retained
routine report records a pass in 14.980103 seconds: core scope passed in 0.462415 seconds,
reconciliation passed in 11.34329 seconds, and repository-tests/full took 0 seconds because it
reused receipt binding
`aa49e2e680bcc4cc7cc6fdfe1d854a28de81cf69cfb5d9f76310fcd492d20d4b`.
The report lists 17 selected files, none deferred, and none incomplete. The hook created commit
`3a342013063f37516b8f65e707e26e4f0c655e0a` (`feat: configure manual test gates and time
budgets`). These are historical result summaries from retained machine artifacts, not recreated
terminal output.

## Fresh revision-bound merge review

**Reviewed revision:** `3a342013063f37516b8f65e707e26e4f0c655e0a`

- `final_panel_security` / security and authority — verdict: approval. Basis: raw hard guard; immutable
  closure; isolated environment and cleanup; receipt/marker binding; cooperative
  non-enforcement. No blocker.
- `final_panel_gate_semantics` / gate semantics, timing, cache, and publication: BLOCK — P1:
  unbounded Git/materialization/controller planning can occur before the configured absolute
  deadline exists; P2: exact final and commit evidence were absent from durable records.
- `final_panel_provider_core` / provider, core portability, and workflow — verdict: approval. Basis:
  manual-only closed config; six critical categories; read-only base diagnostics; cooperative PR
  lane; core portability. No blocker.
- `final_panel_migration_tests` / immutable floor and test completeness — verdict: approval. Basis: exact
  base floor; candidate supplement; isolation; cleanup; 17 test files; 0 deferred; 0 incomplete.
  No blocker.
- `final_panel_records_contract` / records and contracts: BLOCK — task, plan, verification, and
  worklog were stale; the fixed latest-report path had been overwritten, so the current
  receipt/report/marker set could not reconstruct the original final publication; the retry also
  said `Unclaimed` despite status `in-repair`.

Panel result: 3 APPROVE, 2 BLOCK. The valid P1 deadline finding keeps merge blocked regardless of
the numerical majority. This records the surviving historical evidence and corrects the stale
task descriptions, but cannot recreate the lost report/stdout. A product repair, new exact final
run, new commit, and fresh revision-bound panel are still required.
