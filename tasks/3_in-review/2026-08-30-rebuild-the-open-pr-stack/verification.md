# Verification — recovered lower PR

**Verified:** 2026-08-31 by codex

The commands below ran on the complete lower code revision `5a9f044f84fbcc21597f7bf44466cab9b3694b42`. The worktree and true Git clone used Python 3.14.6 and system Python 3.9.6, on Darwin arm64 with Git 2.55.0. The clone contains tracked files and full Git history, with the normal installer; it does not depend on owner scratch files. Output is trimmed to command, candidate, result and elapsed time.

## worktree-314

```text
cwd: /Users/quentinmiao/code/agentfold/.git/agents/worktrees/2026-08-30-recover-useful-local-and-open-234a/_integration
command: python3 automation/run_tests.py --jobs 4 --verbose
candidate: 5a9f044f84fbcc21597f7bf44466cab9b3694b42
tests: 16/16 files passed
test elapsed: 36.75s
exit: 0; elapsed: 36.80s
```

## worktree-39

```text
cwd: /Users/quentinmiao/code/agentfold/.git/agents/worktrees/2026-08-30-recover-useful-local-and-open-234a/_integration
command: /usr/bin/python3 automation/run_tests.py --jobs 4 --verbose
candidate: 5a9f044f84fbcc21597f7bf44466cab9b3694b42
tests: 16/16 files passed
test elapsed: 41.09s
exit: 0; elapsed: 41.15s
```

## cold-314

```text
cwd: /private/tmp/agentfold-final-review-lower-r2
command: python3 automation/run_tests.py --jobs 4 --verbose
candidate: 5a9f044f84fbcc21597f7bf44466cab9b3694b42
tests: 16/16 files passed
test elapsed: 37.47s
exit: 0; elapsed: 37.52s
```

## cold-39

```text
cwd: /private/tmp/agentfold-final-review-lower-r2
command: /usr/bin/python3 automation/run_tests.py --jobs 4 --verbose
candidate: 5a9f044f84fbcc21597f7bf44466cab9b3694b42
tests: 16/16 files passed
test elapsed: 38.06s
exit: 0; elapsed: 38.10s
```

## corpus-314

```text
cwd: /private/tmp/agentfold-final-review-lower-r2
command: python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
candidate: 5a9f044f84fbcc21597f7bf44466cab9b3694b42
Ran 3 tests in 3.355s
OK
exit: 0; elapsed: 3.58s
```

## corpus-39

```text
cwd: /private/tmp/agentfold-final-review-lower-r2
command: /usr/bin/python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
candidate: 5a9f044f84fbcc21597f7bf44466cab9b3694b42
Ran 3 tests in 3.673s
OK
exit: 0; elapsed: 3.87s
```

The ordinary full suite reports five intentional skips: three real-repository corpus checks, one macOS non-UTF-8-name case, and one opt-in whole-suite record-free projection. The separate true-clone corpus commands above execute all three corpus methods with no skips. The combined upper layer records the opt-in projection checks separately; the platform-specific filename case remains skipped on macOS.

## Actual current-main PR range

```text
cwd: /private/tmp/agentfold-final-review-lower-r2
command: python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-30-rebuild-the-open-pr-stack --range 326d8ed5fa4f89eaa1402a54d8377dba5946be12...5a9f044f84fbcc21597f7bf44466cab9b3694b42
candidate: not pinned by this wrapper
reconcile: 0 blocking finding(s), 5 advisory (not blocking)
exit: 0; elapsed: 11.11s
```

## Published claim to lower push range

```text
cwd: /private/tmp/agentfold-final-review-lower-r2
command: python3 automation/reconcile/reconcile.py --check --at-transition push --branch task/2026-08-30-rebuild-the-open-pr-stack --range 99fc02c820b3e8063c5363283f35da36d47c55a0...5a9f044f84fbcc21597f7bf44466cab9b3694b42 --displaced-tip 99fc02c820b3e8063c5363283f35da36d47c55a0
candidate: not pinned by this wrapper
reconcile: 0 blocking finding(s), 5 advisory (not blocking)
exit: 0; elapsed: 9.32s
```

## Core admission before receipt publication

```text
cwd: /private/tmp/agentfold-final-review-lower-r2
command: python3 automation/check_core_scope.py --range 326d8ed5fa4f89eaa1402a54d8377dba5946be12...5a9f044f84fbcc21597f7bf44466cab9b3694b42 --branch task/2026-08-30-rebuild-the-open-pr-stack
candidate: not pinned by this wrapper
core-scope: pass (11 core path(s), task 2026-08-30-rebuild-the-open-pr-stack; independent review manual; not invoked)
exit: 0; elapsed: 0.13s
```

## Observed failing controls

The new portability methods were added before the predicate repair. The first command below therefore exercises the old interpreter-dependent predicate with the new tests; it is a recorded expected failure, not a clean-candidate result. The second command runs those same methods after the repair.

## Python 3.9 old-predicate control

```text
cwd: /Users/quentinmiao/code/agentfold/.git/agents/worktrees/2026-08-30-recover-useful-local-and-open-234a/_integration
command: /usr/bin/python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_retry_notes_freeze_format_controls_across_unicode_versions automation.tests.test_reconcile_queue.ReconcileQueueTests.test_mutable_fields_freeze_format_controls_across_unicode_versions
candidate: not pinned by this wrapper
Ran 2 tests in 2.045s
FAILED (failures=24)
exit: 1; elapsed: 2.25s
```

## Python 3.9 repaired predicate

```text
cwd: /Users/quentinmiao/code/agentfold/.git/agents/worktrees/2026-08-30-recover-useful-local-and-open-234a/_integration
command: /usr/bin/python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_retry_notes_freeze_format_controls_across_unicode_versions automation.tests.test_reconcile_queue.ReconcileQueueTests.test_mutable_fields_freeze_format_controls_across_unicode_versions
candidate: not pinned by this wrapper
Ran 2 tests in 1.954s
OK
exit: 0; elapsed: 2.09s
```

## Independent review evidence

Five distinct native reviewers independently used mechanically assembled criteria, the original request, plan and diff. They did not receive worker reasoning or one another’s verdicts. The findings from prior revisions were repaired before the bounded rechecks summarized here. The formal revision-bound receipt is added after closing task inputs receive their final review.

| Reviewer | Scope and executed evidence at the code pin | Verdict |
|---|---|---|
| final_correctness | Six independent Unicode/entity methods and both new regressions per Python; 21 behavioral baseline assertion failures | `approve` |
| final_history | Sixteen lifecycle/byte methods per Python, actual PR/push ranges, ancestry and append-only records | `approve` |
| final_portability | Forty-eight methods and fourteen real-Git boundaries per Python; exhaustive comparison of all 1,114,112 Unicode code points | `approve` |
| final_docs | Nine template cases, three budget cases, eight focused checks, and both Python-3.9 portability methods | `approve` |
| final_coverage | All 29 initial lower additions and both portability additions discovered and green; every new method observed failing under a relevant fault | `approve` |

The per-method green and failing-control results are retained in `regression-evidence.json`. The Unicode table contains exactly 170 Unicode 16 format controls; the old prose normalizer is unchanged. All five reviewers also judged the changes portable across agents, providers, and adopted repositories. This is native-panel evidence, not evidence from another vendor.

cross-vendor refuter: DID NOT RUN (auto-review denied external repository-code transmission). The execution refusal and its bounded authorization question are recorded in `review-limit.md`.

## Hosted code publication

The [recorded publication snapshot](publication-code-state.json) preserves the actual GitHub heads, synthetic merge candidates, base refs, latest required-check results and URLs, and the closure state of the originals. The native approval count is the parent’s acceptance of the five named reports, not a GitHub review result. This is the complete code milestone; subsequent record-only commits are checked and published separately.

## Captured reviewer reports

The files under `review-evidence/` are JSON captures of the independent reports, including each original UTF-8 text and its SHA-256. Their approval language and local execution paths are transcript data, not new human requests or repository path declarations. The table above summarizes the lower-specific verdicts; a report that also discusses an older upper checkpoint does not certify that upper checkpoint as final.

## Closing-record validation

The record snapshot `a202233c10705e544b2292734cacbe698218b9a5` received the following separate checks. No implementation files differ from the reviewed code pin. The normal record commit selected zero test files by the runner’s record-ownership rule; that empty selection is not runtime-test evidence. The complete-suite and real-Git commands below supply the separately executed checks.

### full-314

```text
cwd: /private/tmp/agentfold-final-review-lower-closing
command: python3 automation/run_tests.py --jobs 4 --verbose
candidate: a202233c10705e544b2292734cacbe698218b9a5
tests: 16/16 files passed
test elapsed: 36.20s
exit: 0; elapsed: 36.24s
```

### corpus-314

```text
cwd: /private/tmp/agentfold-final-review-lower-closing
command: python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
candidate: a202233c10705e544b2292734cacbe698218b9a5
Ran 3 tests in 3.049s
OK
exit: 0; elapsed: 3.27s
```

### full-39

```text
cwd: /private/tmp/agentfold-final-review-lower-closing
command: /usr/bin/python3 automation/run_tests.py --jobs 4 --verbose
candidate: a202233c10705e544b2292734cacbe698218b9a5
tests: 16/16 files passed
test elapsed: 37.78s
exit: 0; elapsed: 37.84s
```

### corpus-39

```text
cwd: /private/tmp/agentfold-final-review-lower-closing
command: /usr/bin/python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
candidate: a202233c10705e544b2292734cacbe698218b9a5
Ran 3 tests in 3.442s
OK
exit: 0; elapsed: 3.65s
```

### pr-range

```text
cwd: /private/tmp/agentfold-final-review-lower-closing
command: python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-30-rebuild-the-open-pr-stack --range 326d8ed5fa4f89eaa1402a54d8377dba5946be12...a202233c10705e544b2292734cacbe698218b9a5
candidate: a202233c10705e544b2292734cacbe698218b9a5
reconcile: 0 blocking finding(s), 5 advisory (not blocking)
exit: 0; elapsed: 9.55s
```

### push-range

```text
cwd: /private/tmp/agentfold-final-review-lower-closing
command: python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-30-rebuild-the-open-pr-stack --range 5a9f044f84fbcc21597f7bf44466cab9b3694b42...a202233c10705e544b2292734cacbe698218b9a5 --displaced-tip 5a9f044f84fbcc21597f7bf44466cab9b3694b42
candidate: a202233c10705e544b2292734cacbe698218b9a5
reconcile: 0 blocking finding(s), 5 advisory (not blocking)
exit: 0; elapsed: 2.94s
```

The full suite retains the same five deliberately skipped methods described above; the separate corpus commands cover all three real-history methods without skips. The code-candidate matrix records the opt-in projection result. The macOS filename limitation remains explicit.

## Closing record review evidence

Three independent reviewers examined the task input changes, unchanged implementation bytes, stable authorization evidence and captured verification records. Their full reports are preserved losslessly as JSON under `review-evidence/`; each records actual commands and the limits of its judgment. These are record-validation verdicts, not a second claim that the unexecuted external review ran.

## Review verdicts

**Reviewed revision:** a202233c10705e544b2292734cacbe698218b9a5

- core-fit / final_history: approve — Confirmed preserved history and legitimate task and queue transitions with unchanged repository mechanisms.
- core-fit / final_docs: approve — Confirmed stable evidence, canonical action projections and explicit verification limits across agents, providers and repositories.
- core-fit / final_coverage: approve — Confirmed unchanged implementation and test discovery, faithful regression evidence and bounded completion claims.
