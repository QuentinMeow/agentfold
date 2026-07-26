# Verification — Let a queue item resolve when its resolution evidence landed earlier

**Verified:** 2026-07-26 by codex

Only commands actually run and their real output are recorded. Long per-test output is
trimmed to the summary and any meaningful failure.

## Focused ordinary-request behavior

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue -k ordinary_request
Ran 14 tests in 5.039s

OK
```

## Deterministic 300-commit process budget

The test asserts exactly one `git rev-list --parents --topo-order`, exactly one persistent
`git cat-file --batch`, no per-revision `rev-list`/`ls-tree`/`show`/`cat-file` command, and
zero additional process calls for a repeated creation lookup.

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_creation_lookup_bounds_git_calls_across_300_unrelated_commits
test_creation_lookup_bounds_git_calls_across_300_unrelated_commits (...) ... ok

Ran 1 test in 8.292s

OK
```

## Representative staged-and-range timing

```
$ /usr/bin/time -p python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_accepts_surviving_change_before_claim_staged_and_range
test_ordinary_request_accepts_surviving_change_before_claim_staged_and_range (...) ... ok

Ran 1 test in 2.294s

OK
real 3.82
user 1.77
sys 1.25
```

## Compatibility failure and repair

The first full run identified one shared cause across 14 errors: the new cached historical
reader assumed a commit root, while task admission intentionally supplies Git's empty-tree
object. The reader was generalized to accept validated commit or tree roots.

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue
Ran 320 tests in 234.356s

FAILED (errors=14)
reconcile_queue.GitSnapshotError: captured object 4b825dc642cb6eb9a060e54bf8d69288fbee4904 is not a Git commit
```

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue -k task_admission
Ran 13 tests in 21.118s

OK
```

## Final queue reconciler suite

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 320 tests in 311.668s

OK
```

## Staged admission check

```
$ python3 automation/reconcile/reconcile.py --check
(no output; exit 0)
```

## Full repository suite

```
$ python3 automation/run_tests.py
Ran 118 tests in 100.568s — OK
Ran 55 tests in 2.710s — OK (skipped=1)
Ran 24 tests in 0.015s — OK
Ran 9 tests in 0.020s — OK
Ran 40 tests in 16.857s — OK (skipped=1)
Ran 28 tests in 11.670s — OK
Ran 320 tests in 253.838s — OK
Ran 9 tests in 0.007s — OK
Ran 19 tests in 3.727s — OK
Ran 5 tests in 0.264s — OK
Ran 3 tests in 0.651s — OK
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
```

## Review verdicts

**Reviewed revision:** ee0f36e9d384278ce75717ae282a6d69edb0d39e

- correctness / independent adversarial panel: block — the exact synthetic merge admission candidate was not checked for a restoration to creation bytes
- contract / independent adversarial panel: block — commit parsing crossed the raw header boundary and the established unchanged-evidence diagnostic phrase drifted
- blast radius / independent adversarial panel: block — creation lookup launched several Git processes per intervening commit and had no deterministic process-budget regression

The blocked revision was not published. Repair verification and a fresh revision-bound review
follow before this task crosses into review.

**Reviewed revision:** 6df60102b6fee66a2d5a0ef453d6f626bca617e2

- correctness / independent adversarial panel: block — replacement refs could make the parent graph and raw object snapshots describe different histories, changing the admission verdict
- contract / independent adversarial panel: block — replacement-ref nondeterminism violated fail-closed history semantics, and the required per-method pre-repair verdict matrix was missing
- blast radius / independent adversarial panel: block — the shared persistent object reader honored replacement refs, so repository-local state could affect every cached historical read

## Replacement-ref regression on the blocked revision

The new test was copied into an isolated detached worktree at `6df6010`; the blocked checker
changed a staged deletion from one unresolved finding to no findings when the replacement was
installed.

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_change_ordinary_request_resolution_verdict
test_replace_ref_cannot_change_ordinary_request_resolution_verdict (...) ... FAIL

AssertionError: Tuples differ: ('deleted unresolved queue item: resolution evidence was not created or changed; no surviving post-creation byte change: `docs/source.md`',) != ()
Ran 1 test in 0.679s
FAILED (failures=1)
```

## Replacement-ref repair and process budget

The replacement test completes staged deletion, direct-range, and exact synthetic-merge
subcases; each must retain the same rejection with and without the forged replacement.

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_change_ordinary_request_resolution_verdict automation.tests.test_reconcile_queue.ReconcileQueueTests.test_creation_lookup_bounds_git_calls_across_300_unrelated_commits
test_replace_ref_cannot_change_ordinary_request_resolution_verdict (...) ... ok
test_creation_lookup_bounds_git_calls_across_300_unrelated_commits (...) ... ok

Ran 2 tests in 11.813s
OK
```

## Replacement repair staged gates

```
$ python3 automation/check_core_scope.py --staged
core-scope: pass (2 core path(s), task 2026-07-26-resolve-queue-items-whose-evidence-already-merged; independent review manual; not invoked)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ git diff --cached --check
(no output; exit 0)

$ git diff --cached --stat
automation/reconcile/reconcile.py                  |   2 +-
automation/tests/test_reconcile_queue.py           | 115 ++++++++++++++++++++-
.../design.md                                      |   6 +-
.../plan.md                                        |   3 +-
.../verification.md                                | 107 +++++++++++++++++++
.../worklog.md                                     |  19 ++++
6 files changed, 247 insertions(+), 5 deletions(-)
```

## Every task-added test against the pre-repair checker

The current test file, including all 24 methods added by this task, was placed in an isolated
detached worktree at base checker `ab5a18e6c2c149be106f09968d309ae5f1fb0773`.
The task branch was not modified. `FAIL` means the old checker contradicted an assertion;
`ERROR` means the test exercised a helper that did not exist yet. Only those non-passing
verdicts distinguish the old checker; the five passing regressions are explicitly not claimed
as discriminating.

```
$ python3 -m unittest -v \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_accepts_surviving_change_before_claim_staged_and_range \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_accepts_surviving_change_after_claim \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_rejects_pre_creation_or_same_commit_evidence \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_rejects_change_reverted_to_creation_bytes \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_requires_every_evidence_path_to_change \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_accepts_evidence_absent_at_creation_then_created \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_follows_unambiguous_rename_to_creation \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_rejects_duplicate_creation_roots_across_merge \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_merge_rename_cannot_reset_creation_evidence_baseline \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_merge_collects_exact_and_renamed_parent_action_roots \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_range_rejects_evidence_reverted_after_deletion \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_range_rejects_evidence_changed_only_after_deletion \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_synthetic_merge_candidate_cannot_restore_creation_evidence \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_change_ordinary_request_resolution_verdict \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_rejects_mixed_valid_and_invalid_evidence_paths \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_creation_lineage_rejects_shallow_history_boundary \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_commit_parent_parser_ignores_body_bytes_and_parent_like_body \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_commit_parent_parser_fails_closed_on_malformed_headers \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_creation_lookup_bounds_git_calls_across_300_unrelated_commits \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_rejects_missing_or_nonregular_final_evidence \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_uses_staged_evidence_not_worktree_bytes \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_git_read_failure_fails_closed \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_ordinary_request_still_rejects_non_status_only_claim \
  automation.tests.test_reconcile_queue.ReconcileQueueTests.test_only_ordinary_requests_use_creation_baseline_evidence
Ran 24 tests in 24.467s
FAILED (failures=16, errors=10)
```

| Test method | Base verdict | Interpretation |
|---|---:|---|
| `test_ordinary_request_accepts_surviving_change_before_claim_staged_and_range` | FAIL | discriminating |
| `test_ordinary_request_accepts_surviving_change_after_claim` | FAIL | discriminating |
| `test_ordinary_request_rejects_pre_creation_or_same_commit_evidence` | FAIL | discriminating diagnostic contract |
| `test_ordinary_request_rejects_change_reverted_to_creation_bytes` | FAIL | discriminating |
| `test_ordinary_request_requires_every_evidence_path_to_change` | PASS | non-discriminating regression |
| `test_ordinary_request_accepts_evidence_absent_at_creation_then_created` | PASS | non-discriminating regression |
| `test_ordinary_request_follows_unambiguous_rename_to_creation` | PASS | non-discriminating regression |
| `test_ordinary_request_rejects_duplicate_creation_roots_across_merge` | FAIL | discriminating |
| `test_merge_rename_cannot_reset_creation_evidence_baseline` | FAIL | discriminating |
| `test_merge_collects_exact_and_renamed_parent_action_roots` | FAIL | discriminating |
| `test_range_rejects_evidence_reverted_after_deletion` | FAIL | discriminating diagnostic contract |
| `test_range_rejects_evidence_changed_only_after_deletion` | FAIL | discriminating diagnostic contract |
| `test_synthetic_merge_candidate_cannot_restore_creation_evidence` | FAIL | discriminating |
| `test_replace_ref_cannot_change_ordinary_request_resolution_verdict` | PASS | non-discriminating against the base checker; discriminates blocked `6df6010` above |
| `test_ordinary_request_rejects_mixed_valid_and_invalid_evidence_paths` | FAIL | discriminating |
| `test_creation_lineage_rejects_shallow_history_boundary` | ERROR | new helper absent; implementation-surface distinction |
| `test_commit_parent_parser_ignores_body_bytes_and_parent_like_body` | ERROR | new helper absent; implementation-surface distinction |
| `test_commit_parent_parser_fails_closed_on_malformed_headers` | ERROR | new helper absent; implementation-surface distinction |
| `test_creation_lookup_bounds_git_calls_across_300_unrelated_commits` | ERROR | new helper absent; implementation-surface distinction |
| `test_ordinary_request_rejects_missing_or_nonregular_final_evidence` | FAIL | discriminating diagnostic contract |
| `test_ordinary_request_uses_staged_evidence_not_worktree_bytes` | FAIL | discriminating diagnostic contract |
| `test_ordinary_request_git_read_failure_fails_closed` | ERROR | new helper absent; implementation-surface distinction |
| `test_ordinary_request_still_rejects_non_status_only_claim` | PASS | non-discriminating regression |
| `test_only_ordinary_requests_use_creation_baseline_evidence` | ERROR | new helper absent; implementation-surface distinction |

## Replacement repair queue suite

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 321 tests in 123.654s

OK
```

## Third review verdicts

**Reviewed revision:** e52cd9ee6c5c772c74595d142651a76f4bd0fb90

- correctness / independent adversarial panel: block — replacement-aware candidate-parent discovery could forge a raw one-parent checkout into an apparent exact base-plus-head synthetic merge
- contract / independent adversarial panel: block — candidate provenance honored replacement refs; two commits lacked the task trailer, the first message contained literal `\n\n`, and no final repaired full-suite result was durably recorded
- blast radius / independent adversarial panel: block — the shared range-candidate validation path could admit an out-of-range checkout under repository-local replacement state

## Non-destructive audit-linkage rebuild

The checked-out branch was renamed to backup codex/pre-audit-linkage-e52cd9e before any new
objects were created. The canonical task branch was recreated at the rebuilt head; the backup
continues to point to old `e52cd9e` and was not pushed.

| Old commit | Rebuilt commit | Tree object (identical) |
|---|---|---|
| `ee0f36e9d384278ce75717ae282a6d69edb0d39e` | `af4474358edbc2c4807dd64aba227f945fd006b3` | `0c253e6ec3ebd565398f79134d66eaf23f2fa8b2` |
| `6df60102b6fee66a2d5a0ef453d6f626bca617e2` | `e5bf650f7cd1abe1b9d4cfecf9e708763b07389d` | `8501fdd029969cdf71baf4f5ceeb0dc207b5db41` |
| `e52cd9ee6c5c772c74595d142651a76f4bd0fb90` | `6dc7d49617fe5314aeed0310ee1fbd794d7b30d8` | `d35aa0ada1826074a2a50381f3c893eac6a893fd` |

```
$ git rev-list --parents -n 1 af4474358edbc2c4807dd64aba227f945fd006b3
af4474358edbc2c4807dd64aba227f945fd006b3 ab5a18e6c2c149be106f09968d309ae5f1fb0773
$ git rev-list --parents -n 1 e5bf650f7cd1abe1b9d4cfecf9e708763b07389d
e5bf650f7cd1abe1b9d4cfecf9e708763b07389d af4474358edbc2c4807dd64aba227f945fd006b3
$ git rev-list --parents -n 1 6dc7d49617fe5314aeed0310ee1fbd794d7b30d8
6dc7d49617fe5314aeed0310ee1fbd794d7b30d8 e5bf650f7cd1abe1b9d4cfecf9e708763b07389d
```

## Forged candidate-parent regression

The new test was copied into an isolated old-checker worktree. Without a replacement, the raw
one-parent candidate is rejected; with a forged replacement object claiming `{base, head}`
parents, the old checker incorrectly admits it.

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_synthetic_candidate_parents
test_replace_ref_cannot_forge_synthetic_candidate_parents (...) ... FAIL
AssertionError: (2, 'reconcile: Git snapshot error: captured candidate is neither the --range head nor an exact base+head synthetic merge\n') != (0, '')
Ran 1 test in 0.396s
FAILED (failures=1)
```

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_synthetic_candidate_parents automation.tests.test_reconcile_queue.ReconcileQueueTests.test_range_rejects_checkout_that_is_not_head_or_synthetic_merge automation.tests.test_reconcile_queue.ReconcileQueueTests.test_range_accepts_exact_synthetic_merge_candidate automation.tests.test_reconcile_queue.ReconcileQueueTests.test_non_task_branch_infers_scope_from_range_task_evidence automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_change_ordinary_request_resolution_verdict
Ran 5 tests in 2.700s
OK
```

The 25th task-added method also fails against base checker
`ab5a18e6c2c149be106f09968d309ae5f1fb0773`; this is a behavioral discriminator. Combined
with the 24-method matrix above, the base verdict count is 5 PASS/non-discriminating,
14 method-level FAIL, and 6 helper-absent ERROR.

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_synthetic_candidate_parents
Ran 1 test in 0.406s
FAILED (failures=1)
```

## Candidate-provenance full-suite iteration

The first run found a stale command-shape assertion after HEAD tree reads gained the audited
Git flag; the implementation result was otherwise green. The assertion was corrected and the
focused pair passed before the complete rerun.

```
$ python3 automation/run_tests.py
FAIL: test_main_caches_repeated_git_snapshot_reads
Ran 322 tests in 140.271s
FAILED (failures=1)
FAIL automation/tests/test_reconcile_queue.py
tests: 10/11 files passed
```

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_main_caches_repeated_git_snapshot_reads automation.tests.test_reconcile_queue.ReconcileQueueTests.test_replace_ref_cannot_forge_synthetic_candidate_parents
Ran 2 tests in 0.467s
OK
```

```
$ python3 automation/run_tests.py
Ran 118 tests in 30.461s — OK
Ran 55 tests in 1.251s — OK (skipped=1)
Ran 24 tests in 0.013s — OK
Ran 9 tests in 0.012s — OK
Ran 40 tests in 9.841s — OK (skipped=1)
Ran 28 tests in 6.773s — OK
Ran 322 tests in 140.851s — OK
Ran 9 tests in 0.003s — OK
Ran 19 tests in 1.388s — OK
Ran 5 tests in 0.109s — OK
Ran 3 tests in 0.258s — OK
tests: 11/11 files passed
```
