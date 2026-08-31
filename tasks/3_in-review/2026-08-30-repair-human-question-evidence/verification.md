# Verification — exact source evidence and unanswered obligations

**Verified:** 2026-08-31 by codex

The complete upper code revision is `4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41`, above lower `5a9f044f84fbcc21597f7bf44466cab9b3694b42`. The commands below ran in the integration worktree and an independently installed full-history Git clone on Darwin arm64, Git 2.55.0, Python 3.14.6 and system Python 3.9.6. Output excerpts preserve the actual commands, candidates, counts and times. The cold clone does not depend on owner scratch or uncommitted files.

## worktree-314

```text
cwd: /Users/quentinmiao/code/agentfold/.git/agents/worktrees/2026-08-30-recover-useful-local-and-open-234a/_upper
command: python3 automation/run_tests.py --jobs 4 --verbose
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
tests: 16/16 files passed
test elapsed: 57.55s
exit: 0; elapsed: 57.59s
```

## worktree-39

```text
cwd: /Users/quentinmiao/code/agentfold/.git/agents/worktrees/2026-08-30-recover-useful-local-and-open-234a/_upper
command: /usr/bin/python3 automation/run_tests.py --jobs 4 --verbose
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
tests: 16/16 files passed
test elapsed: 69.63s
exit: 0; elapsed: 69.68s
```

## cold-314

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: python3 automation/run_tests.py --jobs 4 --verbose
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
tests: 16/16 files passed
test elapsed: 66.65s
exit: 0; elapsed: 66.70s
```

## cold-39

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: /usr/bin/python3 automation/run_tests.py --jobs 4 --verbose
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
tests: 16/16 files passed
test elapsed: 60.09s
exit: 0; elapsed: 60.14s
```

## corpus-314

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
Ran 3 tests in 3.250s
OK
exit: 0; elapsed: 3.49s
```

## corpus-39

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: /usr/bin/python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
Ran 3 tests in 3.563s
OK
exit: 0; elapsed: 3.77s
```

## inert-314

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: env AGENTFOLD_INERT_PROBE=1 python3 -m unittest -v automation.tests.test_run_tests.InputOwnershipTests.test_the_whole_suite_passes_against_a_record_free_projection
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
Ran 1 test in 151.914s
OK
exit: 0; elapsed: 151.99s
```

## inert-39

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: env AGENTFOLD_INERT_PROBE=1 /usr/bin/python3 -m unittest -v automation.tests.test_run_tests.InputOwnershipTests.test_the_whole_suite_passes_against_a_record_free_projection
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
Ran 1 test in 174.613s
OK
exit: 0; elapsed: 174.69s
```

The ordinary suite deliberately skips five methods: three real-repository corpus checks, one macOS non-UTF-8 filename case, and the opt-in whole-suite record-free projection. The separate corpus commands execute all three history-sensitive methods without skips. The separate inertness commands execute the opt-in method and its complete projected suite. Only the filesystem-specific filename case remains skipped on this macOS host; no cross-platform claim is made from that skip.

## pr-range

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-30-repair-human-question-evidence --range 5a9f044f84fbcc21597f7bf44466cab9b3694b42...4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
exit: 0; elapsed: 11.50s
```

## push-range

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-30-repair-human-question-evidence --range e34265086b94f709869530cbbb952cd45b7fca30...4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41 --displaced-tip e34265086b94f709869530cbbb952cd45b7fca30
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
exit: 0; elapsed: 3.89s
```

## synthetic-at-merge-checkout

```text
cwd: /private/tmp/agentfold-r4-upper-synthetic
command: python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-30-repair-human-question-evidence --range 5a9f044f84fbcc21597f7bf44466cab9b3694b42...4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
candidate: 13f80b6556594ca026abfc588499975e53cb9388
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
exit: 0; elapsed: 8.79s
```

## core

```text
cwd: /private/tmp/agentfold-final-review-upper-r4
command: python3 automation/check_core_scope.py --range 5a9f044f84fbcc21597f7bf44466cab9b3694b42...4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41 --branch task/2026-08-30-repair-human-question-evidence
candidate: 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
core-scope: pass (10 core path(s), task 2026-08-30-repair-human-question-evidence; independent review manual; not invoked)
exit: 0; elapsed: 0.15s
```

## Regression and independent-review evidence

The adjacent `regression-evidence.json` records every new recovery test method, its actual green run, and a relevant observed failing control. Original PR tests remain present. Failed historical candidates are controls, not represented as final passes.

Five independent native review lenses used mechanically assembled request, plan, criteria and Git diffs; they did not receive worker reasoning or each other’s verdicts. The final review reports are preserved in `review-evidence/`. The formal revision-bound receipt follows the final review of closing task inputs.

The code preserves captured regular-file source bytes, complete token and literal boundaries, and unanswered replacement-review obligations. It does not verify source truth or relevance, fetch external source content, normalize Unicode spelling, or rewrite existing frozen questions. A prose R-prefix/apostrophe sequence can resemble a raw literal; the authoring guide records the exact-spacing fallback. Identifier and decimal classifications agree across the supported interpreters through Unicode 16; later Unicode additions need a table update.

cross-vendor refuter: DID NOT RUN (auto-review denied external repository-code transmission). The parent task’s `review-limit.md` records the refusal and links the sole authorization question. No code was sent through the rejected launcher.

## Hosted code publication

The parent recovery task’s [recorded publication snapshot](../2026-08-30-rebuild-the-open-pr-stack/publication-code-state.json) preserves both code heads, actual GitHub synthetic merge candidates, base refs, required-check results and URLs, and the closure state of the originals. Subsequent closing-record changes are checked and published separately; the snapshot is not represented as evidence for an untested later revision.

## Captured reviewer reports

The files under `review-evidence/` are JSON captures of the independent reports, including each original UTF-8 text and its SHA-256. Approval language and local execution paths in those captures are transcript data, not new human requests or repository path declarations. Each final report identifies the exact upper code revision and the limits of that review lens.

## Closing-record validation

The record snapshot `87c398c091872314defb3e94062ed7310c0f83fd` received the following separate checks. No implementation files differ from the reviewed code pin. The normal record commit selected zero test files by the runner’s record-ownership rule; that empty selection is not runtime-test evidence. The complete-suite and real-Git commands below supply the separately executed checks.

### full-314

```text
cwd: /private/tmp/agentfold-final-review-upper-closing
command: python3 automation/run_tests.py --jobs 4 --verbose
candidate: 87c398c091872314defb3e94062ed7310c0f83fd
tests: 16/16 files passed
test elapsed: 55.37s
exit: 0; elapsed: 55.42s
```

### corpus-314

```text
cwd: /private/tmp/agentfold-final-review-upper-closing
command: python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
candidate: 87c398c091872314defb3e94062ed7310c0f83fd
Ran 3 tests in 3.333s
OK
exit: 0; elapsed: 3.57s
```

### full-39

```text
cwd: /private/tmp/agentfold-final-review-upper-closing
command: /usr/bin/python3 automation/run_tests.py --jobs 4 --verbose
candidate: 87c398c091872314defb3e94062ed7310c0f83fd
tests: 16/16 files passed
test elapsed: 61.83s
exit: 0; elapsed: 61.89s
```

### corpus-39

```text
cwd: /private/tmp/agentfold-final-review-upper-closing
command: /usr/bin/python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accounts_for_every_byte_of_the_file automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_files_no_new_refusal_on_real_history automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
candidate: 87c398c091872314defb3e94062ed7310c0f83fd
Ran 3 tests in 4.048s
OK
exit: 0; elapsed: 4.26s
```

### pr-range

```text
cwd: /private/tmp/agentfold-final-review-upper-closing
command: python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-30-repair-human-question-evidence --range a202233c10705e544b2292734cacbe698218b9a5...87c398c091872314defb3e94062ed7310c0f83fd
candidate: 87c398c091872314defb3e94062ed7310c0f83fd
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
exit: 0; elapsed: 9.31s
```

### push-range

```text
cwd: /private/tmp/agentfold-final-review-upper-closing
command: python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-30-repair-human-question-evidence --range 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41...87c398c091872314defb3e94062ed7310c0f83fd --displaced-tip 4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41
candidate: 87c398c091872314defb3e94062ed7310c0f83fd
reconcile: 0 blocking finding(s), 6 advisory (not blocking)
exit: 0; elapsed: 3.93s
```

The full suite retains the same five deliberately skipped methods described above; the separate corpus commands cover all three real-history methods without skips. The code-candidate matrix records the opt-in projection result. The macOS filename limitation remains explicit.

## Closing record review evidence

Three independent reviewers examined the task input changes, unchanged implementation bytes, stable authorization evidence and captured verification records. Their full reports are preserved losslessly as JSON under `review-evidence/`; each records actual commands and the limits of its judgment. These are record-validation verdicts, not a second claim that the unexecuted external review ran.

## Review verdicts

**Reviewed revision:** 87c398c091872314defb3e94062ed7310c0f83fd

- core-fit / final_history: approve — Confirmed preserved history and legitimate task and queue transitions with unchanged repository mechanisms.
- core-fit / final_docs: approve — Confirmed stable evidence, canonical action projections and explicit verification limits across agents, providers and repositories.
- core-fit / final_coverage: approve — Confirmed unchanged implementation and test discovery, faithful regression evidence and bounded completion claims.
