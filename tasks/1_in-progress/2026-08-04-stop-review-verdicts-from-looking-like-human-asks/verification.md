# Verification — stop completed review verdicts from looking like human asks

**Verified:** 2026-08-04 by codex sol-high implementer

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Focused receipt, hostile-tail, task-origin, and core-scope regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_normalize_receipt_near_misses automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_accepts_receipt_but_rejects_its_hostile_finding automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict automation.tests.test_check_core_scope.CoreScopeTests.test_blocking_review_without_approve_majority_fails automation.tests.test_check_core_scope.CoreScopeTests.test_approve_majority_preserves_historical_block
.......
----------------------------------------------------------------------
Ran 7 tests in 0.256s

OK
```

## Final repair owning modules

```
$ python3 -m unittest automation.tests.test_markdown_semantics automation.tests.test_check_action_projection automation.tests.test_check_core_scope
----------------------------------------------------------------------
Ran 325 tests in 49.411s

OK (skipped=1)
```

```
$ python3 -m unittest automation.tests.test_reconcile_queue
----------------------------------------------------------------------
Ran 458 tests in 189.007s

OK
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
```

```
$ python3 -m unittest automation.tests.test_run_tests
----------------------------------------------------------------------
Ran 67 tests in 11.905s

OK (skipped=1)
```

The first broad owning-module attempt was interrupted after the `block` command changed
from the unambiguous to the guarded ambiguous vocabulary. It is not verification evidence;
the three completed commands above are clean reruns of every affected owner.

## Final repair full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 142.99s
```

## Final repair staged gates

```
$ git diff --cached --check
```

```
$ python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Full action-projection and core-scope modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope
...........................................................................................................................................................................................s..............
----------------------------------------------------------------------
Ran 202 tests in 17.611s

OK (skipped=1)
```

## Full repository suite

```
$ python3 automation/run_tests.py --jobs 4
test lane: full
test reason: full suite requested
selected test files:
  automation/tests/test_check_action_projection.py
  automation/tests/test_check_core_scope.py
  automation/tests/test_collect_github_review_actions.py
  automation/tests/test_github_action_projection_workflow.py
  automation/tests/test_inspect_workspace_boundaries.py
  automation/tests/test_integrate.py
  automation/tests/test_markdown_semantics.py
  automation/tests/test_mine_cochange.py
  automation/tests/test_pull_request_schema.py
  automation/tests/test_reconcile_open_actions.py
  automation/tests/test_reconcile_queue.py
  automation/tests/test_resolve_github_external_sources.py
  automation/tests/test_run_tests.py
  services/quote-api/tests/test_quote_api.py
  services/quote-cli/tests/test_quote_cli.py
test workers: 4
test shards: 29
  serial tail: automation/tests/test_run_tests.py -> not concurrency-safe, its tests re-run this whole runner, so a shard of it would nest a second worker pool inside the first
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 68.19s
```

## Repaired exact-path and formal-region regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_normalize_receipt_near_misses automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_the_exact_receipt_path_and_region automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_accepts_receipt_but_rejects_its_hostile_finding automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_ignores_verdicts_before_the_revision_field automation.tests.test_check_core_scope.CoreScopeTests.test_blocking_review_without_approve_majority_fails automation.tests.test_check_core_scope.CoreScopeTests.test_approve_majority_preserves_historical_block
.........
----------------------------------------------------------------------
Ran 9 tests in 0.411s

OK
```

## Repaired action-projection and core-scope modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope
.............................................................................................................................................................................................s..............
----------------------------------------------------------------------
Ran 204 tests in 16.194s

OK (skipped=1)
```

## Staged diff and core-scope gate

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (5 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Adversarial panel on 85a044e6

**Reviewed revision:** 85a044e67c725cf03d918432514c76ba1655c984

Panel result: 0 approve, 3 block.

- adversarial panel / reviewer 1: block — basename-only matching lets nested notes/verification.md and case-variant Verification.md files hide approval-like prose that the core gate never accepts as a receipt.
- adversarial panel / reviewer 2: block — a matching line outside the one real Review verdicts section, or before its one valid full-commit field, receives an exception the formal gate never grants.
- adversarial panel / reviewer 3: block — duplicate or missing sections and revision fields leave receipt lookalikes unbound, so neutralizing their verdict token can hide a real human ask.

This adversarial panel reviewed the prior revision. `--require-review` was not invoked;
the repaired commit still needs its own independent revision-bound review.

## Repaired staged diff and core-scope gate

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (6 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Repaired reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Heading-boundary regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_the_exact_receipt_path_and_region automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_end_receipts_at_real_h1_and_h2_boundaries automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_keep_h3_content_inside_review_verdicts automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_accepts_receipt_but_rejects_its_hostile_finding automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_ends_at_real_h1_and_h2_boundaries automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_a_revision_like_setext_heading automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_keeps_h3_content_inside_the_section
..........
----------------------------------------------------------------------
Ran 10 tests in 0.389s

OK
```

## Heading-boundary owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
..................................................................................................................................................................................................s......................................................
----------------------------------------------------------------------
Ran 249 tests in 16.463s

OK (skipped=1)
```

## Heading-boundary full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 68.07s
```

## Adversarial panel on 12a1f32

**Reviewed revision:** 12a1f320a9916dd2223a6fe81fd5464ddc611aae

Panel result: 2 approve, 1 block.

- adversarial panel / reviewer 1: no blocking finding recorded.
- adversarial panel / reviewer 2: no blocking finding recorded.
- adversarial panel / reviewer 3: block — the Review verdicts H2 ends only at another ATX H2, so ATX H1 and setext H1/H2 content can remain inside the receipt region and hide a later approval-like human action.

The block is valid and this session repairs it. `--require-review` was not invoked against
`12a1f320a9916dd2223a6fe81fd5464ddc611aae`.

## Review verdicts (when a review was explicitly run)

No independent core-fit review has been run against the heading-boundary repair commit;
that requires the new immutable revision produced after these changes.

## Heading-boundary staged diff and core-scope gate

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (3 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Heading-boundary reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Owner-authorized closed grammar regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_normalize_receipt_near_misses automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_the_exact_receipt_path_and_region automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_end_receipts_at_first_nonreceipt_content automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_container_and_decorated_headings automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_allow_blank_separated_contiguous_verdicts automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_closes_when_a_verdict_precedes_the_revision_field automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_ends_at_first_nonreceipt_content automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_a_revision_like_setext_heading automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_container_and_decorated_headings automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_blank_separated_contiguous_verdicts automation.tests.test_check_core_scope.CoreScopeTests.test_historical_revision_fields_outside_formal_block_are_allowed automation.tests.test_check_core_scope.CoreScopeTests.test_duplicate_revision_inside_formal_block_fails_closed automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_noncanonical_verdict_lines automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_accepts_receipt_but_rejects_its_hostile_finding
.................
----------------------------------------------------------------------
Ran 17 tests in 0.301s

OK
```

## Owner-authorized full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 70.88s
```

## Owner-authorized reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Owner-authorized staged core-scope gate

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (4 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Adversarial panel on 25b75c3

**Reviewed revision:** 25b75c3cdd7fcb17626a79135c1b4b787fe41f0c

Panel result: 1 approve, 2 block.

- adversarial panel / reviewer 1: no blocking finding reported.
- adversarial panel / security reviewer: block — semantic blanking lets a nonblank raw comment, HTML block, fence, or indented code bridge the receipt to a later verdict that is then wrongly counted and neutralized.
- adversarial panel / correctness reviewer: block — punctuation-only and self reviewers can have their verdict token neutralized by action projection even though the core gate rejects those identities as independent evidence.

Both blockers were accepted and repaired in the next implementation revision. This panel
does not approve that repair, and `--require-review` was not invoked against it.

## Raw-contiguity and reviewer-authority regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_normalize_receipt_near_misses automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_the_exact_receipt_path_and_region automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_end_receipts_at_first_nonreceipt_content automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_container_and_decorated_headings automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_allow_blank_separated_contiguous_verdicts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_an_independent_real_reviewer automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_read_claimant_from_candidate_revision automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_end_receipts_at_raw_hidden_or_code_content automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_punctuation_reviewer_and_unclaimed_task automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_stops_at_raw_hidden_or_code_content
.............
----------------------------------------------------------------------
Ran 13 tests in 0.784s

OK
```

## Raw-contiguity and reviewer-authority owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
............................................................................................................................................................................................................s......................................................
----------------------------------------------------------------------
Ran 259 tests in 14.920s

OK (skipped=1)
```

## Raw-contiguity and reviewer-authority full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 56.85s
```

## Raw-contiguity and reviewer-authority range core-scope gate

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (7 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Raw-contiguity and reviewer-authority reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Adversarial panel on e073358

**Reviewed revision:** e073358dec0a4f7c119597f94c61ed6adb02f0de

Panel result: 0 approve, 3 block.

- adversarial panel / grammar reviewer: block — Python `.strip()` treats NBSP, form-feed, vertical-tab, Unicode separators, controls, and default-ignorables as blank, so hostile raw content can bridge a later verdict.
- adversarial panel / line-ending reviewer: block — removing only one trailing character does not define LF and CRLF bodies safely enough for the closed structural grammar.
- adversarial panel / identity reviewer: block — source-shaped identity tokens make zero-width or inline-HTML self reviewers appear distinct, leave markup-only names nonempty, and treat repository placeholders as identities.

All three blockers were accepted and repaired in the next implementation revision. This
panel does not approve that repair, and `--require-review` was not invoked against it.

## Whitespace, CRLF, and rendered-identity regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_compare_rendered_human_identities automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_reviewer_and_claimant_placeholders automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_end_receipts_at_raw_hidden_or_code_content automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_accept_a_crlf_receipt automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_read_claimant_from_candidate_revision automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_compares_rendered_human_identities automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_reviewer_and_claimant_placeholders automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_stops_at_raw_hidden_or_code_content automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_a_crlf_receipt automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict
...........
----------------------------------------------------------------------
Ran 11 tests in 0.954s

OK
```

## Whitespace, CRLF, and rendered-identity owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
..................................................................................................................................................................................................................................................s......................................................
----------------------------------------------------------------------
Ran 265 tests in 33.069s

OK (skipped=1)
```

## Whitespace, CRLF, and rendered-identity full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 133.77s
```

## Whitespace, CRLF, and rendered-identity range core-scope gate

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (7 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Whitespace, CRLF, and rendered-identity reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Adversarial panel on 788bd4c

**Reviewed revision:** 788bd4cb709c4ea4f20099013eb9ea598a39c289

Panel result: 0 approve, 3 block.

- adversarial panel / identity-alias reviewer: block — Markdown link, reference,
  emphasis, and inline-code aliases can make a self reviewer appear distinct, while
  link destinations can mint apparent voters.
- adversarial panel / placeholder reviewer: block — rendered placeholders such as
  linked or emphasized TBD can retain source-shaped tokens and enter the voter set.
- adversarial panel / finding reviewer: block — decorated finding text can render as an
  approval request while source-shaped classification misses it after verdict
  neutralization.

All three blockers were accepted and repaired in the next implementation revision. This
panel does not approve that repair, and `--require-review` was not invoked against it.

## Markdown identity and decorated-component regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.InlineIdentityRenderingTests automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_compare_rendered_human_identities automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_reviewer_and_claimant_placeholders automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_fail_closed_on_decorated_receipt_components automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_neutralize_duplicate_vote_aliases automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_compares_rendered_human_identities automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_reviewer_and_claimant_placeholders automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_decorated_reviewer_and_finding_components automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_does_not_count_duplicate_vote_aliases automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict
..............
----------------------------------------------------------------------
Ran 14 tests in 1.617s

OK
```

## Markdown identity and decorated-component owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
.........................................................................................................................................................................................................................................................s......................................................
----------------------------------------------------------------------
Ran 272 tests in 43.525s

OK (skipped=1)
```

## Markdown identity and decorated-component full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 139.55s
```

## Markdown identity and decorated-component pre-commit lane

```
$ git commit -m "fix: fail closed on decorated review receipts" -m "task: 2026-08-04-stop-review-verdicts-from-looking-like-human-asks"
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 109.47s
pre-commit: OK
[task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks 073b3d8] fix: fail closed on decorated review receipts
 6 files changed, 206 insertions(+), 4 deletions(-)
```

## Markdown identity and decorated-component range core-scope gate

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Markdown identity and decorated-component reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Adversarial panel on 5c31f50

**Reviewed revision:** 5c31f508b1166573b8f1b04c5f7410d033c0bace

Panel result: 0 approve; 2 completed block verdicts. The security reviewer independently
reproduced the third blocker before its review tool errored, so no security vote is
invented here.

- adversarial panel / identity reviewer: block — Markdown image labels can display the
  claimant while their destinations alter identity tokens or create apparent voters.
- adversarial panel / source-grammar reviewer: block — backslash escapes such as
  `cod\_ex` remain source-decorated even when the partial renderer does not change them.
- adversarial panel / security reproduction: an image-form finding can keep release-
  command wording human-visible after the structural verdict token is neutralized. The
  reproduction completed; the review tool failed before returning a final verdict.

Both completed blockers and the concrete security reproduction were accepted and repaired
in the next implementation revision. This panel does not approve that repair, and
`--require-review` was not invoked against it.

## Source-whitelist regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_allowlisted_source_identities automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_reviewer_and_claimant_placeholders automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_accept_allowlisted_unicode_receipt automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_fail_closed_on_decorated_receipt_components automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_neutralize_decorated_vote_aliases automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_requires_allowlisted_source_identities automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_reviewer_and_claimant_placeholders automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_allowlisted_unicode_receipt automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_decorated_reviewer_and_finding_components automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_does_not_count_decorated_vote_aliases automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict
.................
----------------------------------------------------------------------
Ran 17 tests in 0.840s

OK
```

## Source-whitelist owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
........................................................................................................................................................................................................................s..........................................................
----------------------------------------------------------------------
Ran 275 tests in 19.623s

OK (skipped=1)
```

## Source-whitelist full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 68.69s
```

## Source-whitelist pre-commit lane

```
$ git commit -m "fix: whitelist formal review receipt text" -m "task: 2026-08-04-stop-review-verdicts-from-looking-like-human-asks"
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 52.85s
pre-commit: OK
[task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks d1a6802] fix: whitelist formal review receipt text
 8 files changed, 204 insertions(+), 114 deletions(-)
```

## Source-whitelist range core-scope gate

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Source-whitelist reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Adversarial panel on 2ba968f

**Reviewed revision:** 2ba968faf027df5874de8847948568102513a497

Panel result: 0 approve, 3 block.

- adversarial panel / raw-source reviewer: block — claimant identity was derived from a
  semantic view, so inline or trailing HTML comments could disappear before the source
  whitelist saw the claimant suffix.
- adversarial panel / identity reviewer: block — NFKC preserved Unicode category-M marks,
  so visually equivalent reviewer spellings could become distinct voter keys and
  mark-decorated placeholders could remain identities.
- adversarial panel / action reviewer: block — the human-action normalizer also preserved
  combining marks, so approval or blocking keywords could evade ordinary detection.

These are three completed block verdicts. The security agent's earlier tool error on
`5c31f508b1166573b8f1b04c5f7410d033c0bace` was not a vote and is not counted here.
All three blockers were accepted and repaired in the next implementation revision. This
panel does not approve that repair, and `--require-review` was not invoked against it.

## Raw claimant and Unicode-mark regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_normalize_receipt_near_misses automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_allowlisted_source_identities automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_validate_claimant_from_unchanged_raw_source automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_fold_combining_marks_in_reviewer_identity automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_reviewer_and_claimant_placeholders automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_accept_allowlisted_unicode_receipt automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_noncanonical_verdict_lines automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_requires_allowlisted_source_identities automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_validates_claimant_from_unchanged_raw_source automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_folds_combining_marks_in_reviewer_identity automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_combining_mark_aliases_do_not_stuff_votes automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_reviewer_and_claimant_placeholders automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_allowlisted_unicode_receipt automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict
......................
----------------------------------------------------------------------
Ran 22 tests in 0.661s

OK
```

## Raw claimant and Unicode-mark owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
.............................................................................................................................................................................................................................s............................................................
----------------------------------------------------------------------
Ran 282 tests in 16.335s

OK (skipped=1)
```

## Raw claimant and Unicode-mark full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 62.24s
```

## Raw claimant and Unicode-mark pre-commit lane

```
$ git commit -m "fix: bind review identity to raw source" -m "task: 2026-08-04-stop-review-verdicts-from-looking-like-human-asks"
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 59.53s
pre-commit: OK
[task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks 69d37a2] fix: bind review identity to raw source
 7 files changed, 305 insertions(+), 27 deletions(-)
```

## Raw claimant and Unicode-mark exact-range core-scope gate

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Raw claimant and Unicode-mark exact-range reconciler

```
$ python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...69d37a25fd1459b8384bf255b8a181fdcda6652d --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
reconcile: 0 blocking finding(s)
```

## Adversarial panel on 97c35ed

**Reviewed revision:** 97c35ede09d045f63a45be13ba6452cd3aa13764

Panel result: 0 approve, 3 block.

- adversarial panel / input-grammar reviewer: block — punctuation-decorated placeholders
  could become voters, and a raw claimant line after prose or a blockquote could remain a
  CommonMark lazy continuation rather than top-level authority.
- adversarial panel / identity reviewer: block — Cyrillic and mixed-script homoglyphs
  could make a claimant and reviewer appear equal to a human while comparing as independent.
- adversarial panel / action reviewer: block — a Cyrillic first character in `approve`
  inside a formal finding could evade ordinary human-action detection.

All three blockers were accepted and repaired in implementation revision
`0326174c33d6ca35c266854235c4c7239d3f2a2d`. A follow-up design debate also closed ASCII
punctuation-boundary, word-order, duplicate-voter, and immediate Setext claimant aliases
before that commit. This panel does not approve the repair, and `--require-review` was not
invoked against it.

## ASCII authority and identity-alias focused regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_allowlisted_source_identities automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_ascii_boundary_and_order_self_aliases automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_validate_claimant_from_unchanged_raw_source automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_non_ascii_reviewer_identity automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_reviewer_and_claimant_placeholders automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_accept_ascii_authority_receipt automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_keep_non_ascii_finding_actionable automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_fail_closed_on_decorated_receipt_components automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_requires_allowlisted_source_identities automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_ascii_boundary_and_word_order_self_aliases automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_deduplicates_ascii_boundary_and_order_alias_votes automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_validates_claimant_from_unchanged_raw_source automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_non_ascii_reviewer_identity automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_combining_mark_aliases_do_not_stuff_votes automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_reviewer_and_claimant_placeholders automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_ascii_authority_receipt automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_non_ascii_finding_source automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_decorated_reviewer_and_finding_components automation.tests.test_check_core_scope.CoreScopeTests.test_manual_independent_review_accepts_valid_verdict
............................
----------------------------------------------------------------------
Ran 28 tests in 1.038s

OK
```

## ASCII authority and identity-alias owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
..................................................................................................................................................................................................................................s.............................................................
----------------------------------------------------------------------
Ran 288 tests in 17.349s

OK (skipped=1)
```

## ASCII authority and identity-alias full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 64.21s
```

## ASCII authority and identity-alias staged lane

```
$ python3 automation/run_tests.py --staged
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 56.87s
```

## ASCII authority and identity-alias exact-range core-scope gate

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## ASCII authority and identity-alias exact-range reconciler

```
$ python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...0326174c33d6ca35c266854235c4c7239d3f2a2d --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
reconcile: 0 blocking finding(s)
```

## ASCII authority and identity-alias diff check

```
$ git diff --check 97c35ede09d045f63a45be13ba6452cd3aa13764..0326174c33d6ca35c266854235c4c7239d3f2a2d
```

## Adversarial panel on 7cd22e7

**Reviewed revision:** 7cd22e79fc6d4ec3e3c151f0093a6ef4c251c344

Panel result: 0 approve, 3 block.

- adversarial panel / identity-key reviewer: block — placeholder rejection used compact
  alphanumeric order while authority used a sorted character multiset, so reordered or
  anagram spellings such as `yet none` and `D B T` could become voters.
- adversarial panel / grammar reviewer: block — the shared source predicate allowed colon
  in claimant identity even though colon terminates reviewer identity in the receipt line.
- adversarial panel / visibility reviewer: block — an open hidden HTML container could
  cross a blank line, leave a claimant structurally visible, and still hide it from a human.

All three blockers were accepted and repaired in implementation revision
`d27c44174db0f1bb8d13b632be3c6f307d568707`. Finite-model preflight extended the HTML
finding to receipt headings under every still-open container and verified closed/container-
in-code compatibility. Its initial global revision-field proposal was retracted because
the accepted contiguous grammar and immutable verification history make later exact fields
ordinary history. The final audit found no remaining blocker in scope. This panel does not
supply acceptance evidence for the repair, and `--require-review` was not invoked against it.

## Placeholder, colon, and open-container focused regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_the_exact_receipt_path_and_region automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_allowlisted_source_identities automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_validate_claimant_from_unchanged_raw_source automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_reviewer_and_claimant_placeholders automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_embedded_colon_reviewer automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_accept_ascii_authority_receipt automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_neutralize_receipts_in_open_html automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_ignore_historical_revision_after_terminator automation.tests.test_check_core_scope.CoreScopeTests.test_historical_revision_fields_outside_formal_block_are_allowed automation.tests.test_check_core_scope.CoreScopeTests.test_revision_fields_inside_code_or_html_do_not_duplicate_receipt automation.tests.test_check_core_scope.CoreScopeTests.test_duplicate_revision_inside_formal_block_fails_closed automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_requires_allowlisted_source_identities automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_validates_claimant_from_unchanged_raw_source automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_visible_canonical_claimant_lf_and_crlf automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_claimant_after_closed_or_code_html automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_reviewer_and_claimant_placeholders automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_embedded_colon_reviewer automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_receipt_nested_in_open_html automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_receipt_after_closed_or_code_html automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_ascii_authority_receipt
............................
----------------------------------------------------------------------
Ran 28 tests in 0.768s

OK
```

## Placeholder, colon, and open-container owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
...........................................................................................................................................................................................................................................s..............................................................
----------------------------------------------------------------------
Ran 298 tests in 16.171s

OK (skipped=1)
```

## Placeholder, colon, and open-container full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 53.63s
```

## Placeholder, colon, and open-container pre-commit lane

```
$ git commit -m "fix: close review authority container gaps" -m "task: 2026-08-04-stop-review-verdicts-from-looking-like-human-asks"
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 46.25s
pre-commit: OK
[task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks d27c441] fix: close review authority container gaps
```

## Placeholder, colon, and open-container exact-range core-scope gate

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Placeholder, colon, and open-container exact-range reconciler

```
$ python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...d27c44174db0f1bb8d13b632be3c6f307d568707 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
reconcile: 0 blocking finding(s)
```

## Placeholder, colon, and open-container diff check

```
$ git diff --check 7cd22e79fc6d4ec3e3c151f0093a6ef4c251c344..d27c44174db0f1bb8d13b632be3c6f307d568707
```

## Adversarial panel on aa0a111

**Reviewed revision:** aa0a111d73da9807c8473848ed2dbf2f5c9828b5

Panel result: 0 approve, 3 block.

- adversarial panel / correctness reviewer: block — incomplete multiline raw HTML markers
  could leave the HTML parser stack empty while pending input still nested a later claimant
  or receipt, including a marker completed only after the authority line.
- adversarial panel / visibility reviewer: block — receipt heading, revision, and verdict
  lines were compared with structural Markdown but not with the rendered-human view, so
  invisible evidence could retain formal meaning.
- adversarial panel / complexity reviewer: block — each exact heading candidate reparsed
  its entire source prefix, making duplicate-heading rejection quadratic.

All three blockers were accepted and repaired in implementation revision
`5b738fb1157fbdb53c2b3be9d9813d93d3eedd89`. Finite-model preflight also found malformed
HTML parser inputs that raised `NotImplementedError`; the rendered view now falls back to
action-visible code-masked source, while the authority helper fails closed. The final audit
found no remaining blocker in scope. This panel supplies no acceptance evidence for the
repair, and `--require-review` was not invoked against it.

## Pending-HTML, rendered-evidence, and linear-scan focused regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_validate_claimant_from_unchanged_raw_source automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_do_not_neutralize_receipts_in_open_html automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_accept_ascii_authority_receipt automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_the_exact_receipt_path_and_region automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_validates_claimant_from_unchanged_raw_source automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_receipt_nested_in_open_html automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_receipt_after_closed_or_code_html automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_ascii_authority_receipt automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_accepts_a_crlf_receipt automation.tests.test_check_core_scope.CoreScopeTests.test_duplicate_revision_inside_formal_block_fails_closed automation.tests.test_check_core_scope.CoreScopeTests.test_historical_revision_fields_outside_formal_block_are_allowed
......................
----------------------------------------------------------------------
Ran 22 tests in 0.603s

OK
```

## Pending-HTML, rendered-evidence, and linear-scan owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
...........................................................................................................................................................................................................................................s.................................................................
----------------------------------------------------------------------
Ran 301 tests in 16.270s

OK (skipped=1)
```

## Pending-HTML, rendered-evidence, and linear-scan full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 56.66s
```

## Pending-HTML, rendered-evidence, and linear-scan pre-commit lane

```
$ git commit -m "fix: reject invisible review receipt evidence" -m "task: 2026-08-04-stop-review-verdicts-from-looking-like-human-asks"
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 44.77s
pre-commit: OK
[task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks 5b738fb] fix: reject invisible review receipt evidence
```

## Pending-HTML, rendered-evidence, and linear-scan exact-range core-scope gate

```
$ python3 automation/check_core_scope.py --range origin/main...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Pending-HTML, rendered-evidence, and linear-scan exact-range reconciler

```
$ python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...5b738fb1157fbdb53c2b3be9d9813d93d3eedd89 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
reconcile: 0 blocking finding(s)
```

## Pending-HTML, rendered-evidence, and linear-scan diff check

```
$ git diff --check aa0a111d73da9807c8473848ed2dbf2f5c9828b5..5b738fb1157fbdb53c2b3be9d9813d93d3eedd89
```

## Adversarial panel on 9e9dfa2

**Reviewed revision:** 9e9dfa2218a71135c8e6ae3e638c26d92d42f5cf

Panel result: 1 approve, 2 block.

- adversarial panel / correctness reviewer: block — an exact revision field after an
  already accepted verdict still reset the receipt, although any non-verdict at that
  point should terminate and preserve the evidence already collected.
- adversarial panel / complexity reviewer: block — verdict neutralization called
  `semantic.count` and `semantic.rfind` on the growing prefix for every matched verdict,
  making a k-verdict document O(k*n).
- adversarial panel / boundary reviewer: clear — pending-HTML, three-view visibility, and
  duplicate-heading repairs held in the reviewed revision; no blocker was reported.

Both blockers were accepted and repaired in implementation revision
`189fd7ee27faef510a461678eb27fc854f77eb84`. The finite-model preflight independently
exercised pre-verdict and post-verdict revision fields, large receipts, actual history,
and the earlier HTML boundaries, then reported no remaining blocker in scope. This panel
supplies no acceptance evidence for the repair, and `--require-review` was not invoked
against it.

## Revision-terminator and verdict-mapping focused regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_revision_duplicate_only_invalidates_the_preverdict_prologue automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_verdict_mapping_never_scans_the_semantic_prefix_per_match automation.tests.test_check_core_scope.CoreScopeTests.test_duplicate_revision_inside_formal_block_fails_closed automation.tests.test_check_core_scope.CoreScopeTests.test_revision_after_valid_verdict_terminates_and_preserves_receipt automation.tests.test_check_core_scope.CoreScopeTests.test_historical_revision_fields_outside_formal_block_are_allowed automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_require_the_exact_receipt_path_and_region automation.tests.test_check_action_projection.ActionProjectionTests.test_revision_immediately_after_verdict_terminates_receipt automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_ignore_historical_revision_after_terminator
........
----------------------------------------------------------------------
Ran 8 tests in 4.693s

OK
```

## Revision-terminator and verdict-mapping owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
.............................................................................................................................................................................................................................................s...........................................................................
----------------------------------------------------------------------
Ran 305 tests in 32.740s

OK (skipped=1)
```

## Complete-neutralizer before-and-after observation

```
$ python3 - <<'PY'
import subprocess
import time
import types
from automation import markdown_semantics as current

source_code = subprocess.check_output(
    ["git", "show", "9e9dfa2218a71135c8e6ae3e638c26d92d42f5cf:automation/markdown_semantics.py"],
    text=True,
)
old = types.ModuleType("old_markdown_semantics")
exec(compile(source_code, "old_markdown_semantics.py", "exec"), old.__dict__)

def receipt(count, revision):
    return (
        "history\n\n## Review verdicts\n\n"
        f"**Reviewed revision:** {revision * 40}\n\n"
        + "".join(
            "- core-fit / reviewer: approve — accepted verdict\n"
            for _ in range(count)
        )
    )

for count, revision in ((4000, "a"), (8000, "b")):
    text = receipt(count, revision)
    for label, module in (("before", old), ("after", current)):
        started = time.perf_counter()
        output = module.neutralize_core_fit_review_verdict_tokens(text, claimant="author")
        elapsed = time.perf_counter() - started
        assert output.count("reviewer: approve") == 0
        assert output.count("accepted verdict") == count
        print(f"{label} {count}: {elapsed:.3f}s")
PY
before 4000: 1.090s
after 4000: 0.657s
before 8000: 2.975s
after 8000: 1.357s
```

These single-run observations are diagnostic evidence; the regression gate is the
deterministic 16,000-verdict test that raises on any `count` or `rfind` prefix scan.

## Revision-terminator and verdict-mapping full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 119.43s
```

## Revision-terminator and verdict-mapping pre-commit lane

```
$ git commit -m "fix: make review receipt neutralization linear" -m "task: 2026-08-04-stop-review-verdicts-from-looking-like-human-asks"
core-scope: pass (5 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
reconcile: 0 blocking finding(s)
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 110.18s
pre-commit: OK
[task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks 189fd7e] fix: make review receipt neutralization linear
```

## Revision-terminator and verdict-mapping exact-range core-scope gate

```
$ python3 automation/check_core_scope.py --range 4b467924b5832489829538164306439667e97aa0...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Revision-terminator and verdict-mapping exact-range reconciler

```
$ python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...189fd7ee27faef510a461678eb27fc854f77eb84 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
reconcile: 0 blocking finding(s)
```

## Revision-terminator and verdict-mapping diff check

```
$ git diff --check 9e9dfa2218a71135c8e6ae3e638c26d92d42f5cf..189fd7ee27faef510a461678eb27fc854f77eb84
```

## Adversarial panel on 7e3c8d2

**Reviewed revision:** 7e3c8d2b9ea082b9289509fe64132eaaa545b272

Panel result: 1 approve, 2 block.

- adversarial panel / composite-identity reviewer: block — the actual claimant `codex
  planner / sol-high implementer` was represented only by its combined key, so either
  component could appear to be a different reviewer.
- adversarial panel / alias reviewer: block — equality-only comparison admitted
  conservative prefix and suffix aliases such as a claimant component plus `reviewer`.
- adversarial panel / parser reviewer: clear — revision termination and linear token
  mapping held in the reviewed revision; no blocker was reported.

Both blockers were accepted and repaired in implementation revision
`984af3602d171ee3b66cfbf0bdcc646330911e6f`. Finite-model preflight additionally found
separator-dependent whole keys and one-balanced-substitution aliases; the implementation
now closes both and records the deliberate display-label false-collision tradeoff. Its
final audit reported no remaining blocker in scope. This panel supplies no acceptance
evidence for the repair, and `--require-review` was not invoked against it.

## Composite-claimant focused regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_composite_claimant_keys_include_whole_and_every_component automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_one_bad_composite_component_invalidates_claimant_authority automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_composite_claimants_reject_component_and_multiset_aliases automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_composite_claimant_aliases automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_splits_every_explicit_coclaimant_separator automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_invalidates_one_bad_coclaimant_component automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_keeps_distinct_reviewer_role_keys_distinct automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_deduplicates_ascii_boundary_and_order_alias_votes automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_composite_claimant_aliases automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_invalidate_bad_composite_claimants automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_split_every_coclaimant_separator automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_ascii_boundary_and_order_self_aliases
............
----------------------------------------------------------------------
Ran 12 tests in 0.225s

OK
```

## Composite-claimant owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
....................................................................................................................................................................................................................................................s......................................................................
----------------------------------------------------------------------
Ran 315 tests in 30.539s

OK (skipped=1)
```

## Composite-claimant full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 144.97s
```

## Composite-claimant pre-commit lane

```
$ git commit -m "fix: reject composite claimant self-review aliases" -m "task: 2026-08-04-stop-review-verdicts-from-looking-like-human-asks"
core-scope: pass (5 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
reconcile: 0 blocking finding(s)
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 112.63s
pre-commit: OK
[task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks 984af36] fix: reject composite claimant self-review aliases
```

## Composite-claimant exact-range core-scope gate

```
$ python3 automation/check_core_scope.py --range 4b467924b5832489829538164306439667e97aa0...HEAD --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Composite-claimant exact-range reconciler

```
$ python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...984af3602d171ee3b66cfbf0bdcc646330911e6f --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
reconcile: 0 blocking finding(s)
```

## Composite-claimant diff check

```
$ git diff --check 7e3c8d2b9ea082b9289509fe64132eaaa545b272..984af3602d171ee3b66cfbf0bdcc646330911e6f
```

## Eleventh-panel wrap-up checkpoint

**Reviewed revision:** ea4bb732e2e4c1d0d4c2a3733298d40652fb9215

Panel result: 2 approve, 1 block. The accepted performance finding was repeated composite
claimant derivation inside both verdict loops. Two reviewers reported no other blocker.
This checkpoint supplies no acceptance evidence for its repair, and `--require-review`
was not invoked against it.

## Claimant-precompute focused regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_neutralizer_derives_claimant_keys_once_for_many_verdicts automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_derives_claimant_keys_once_for_many_verdicts automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_composite_claimants_reject_component_and_multiset_aliases automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_composite_claimant_aliases automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_composite_claimant_aliases
.....
----------------------------------------------------------------------
Ran 5 tests in 0.221s

OK
```

## Claimant-precompute staged checkpoint

```
$ git commit -m "perf: derive claimant authority once per receipt" -m "task: 2026-08-04-stop-review-verdicts-from-looking-like-human-asks"
core-scope: pass (4 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
reconcile: 0 blocking finding(s)
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
tests: 13/13 files passed
test elapsed: 79.74s
pre-commit: OK
[task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks 1abfc8d] perf: derive claimant authority once per receipt
```

Manual owning/full/exact-range lanes were deliberately deferred at the owner's wrap-up
request and remain plan step 20.

## Resumed verification of claimant precomputation

The resumed session verified exact checkpoint revision
`d39aedcf3b5c84e3b4ba411d0802f90c54f0ef2d`, which contains implementation revision
`1abfc8d2d2e9f1baf184398f0591cb7e8632eef9` plus its checkpoint records. This evidence
completes plan step 20 only; it is not an independent review receipt.

### Focused claimant-precompute regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_neutralizer_derives_claimant_keys_once_for_many_verdicts automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_derives_claimant_keys_once_for_many_verdicts automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_composite_claimants_reject_component_and_multiset_aliases automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_composite_claimant_aliases automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_reject_composite_claimant_aliases
.....
----------------------------------------------------------------------
Ran 5 tests in 0.370s

OK
```

### Owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_markdown_semantics
317 tests passed, 1 skipped
test elapsed: 37.062s
```

### Full repository suite

```
$ python3 automation/run_tests.py --jobs 4
tests: 15/15 files passed
test elapsed: 123.93s
```

### Exact-range core-scope gate

```
$ python3 automation/check_core_scope.py --range 4b467924b5832489829538164306439667e97aa0...d39aedcf3b5c84e3b4ba411d0802f90c54f0ef2d --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (8 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

### Sandbox index recovery and exact-range reconciler

The first sandboxed reconciler attempt did not produce a valid verification result. Git
recovered a stale index stat-cache difference, then the sandbox could not create the
linked worktree's `index.lock`. The coordinating root session refreshed that shared index
with escalated filesystem access before retrying:

```
$ git update-index --refresh --really-refresh
```

The retry against the exact checkpoint range passed:

```
$ python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...d39aedcf3b5c84e3b4ba411d0802f90c54f0ef2d --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
reconcile: 0 blocking finding(s)
```

### Exact-range diff and tracking status

```
$ git diff --check 4b467924b5832489829538164306439667e97aa0...d39aedcf3b5c84e3b4ba411d0802f90c54f0ef2d
```

```
$ git status --short --branch
## task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks...origin/task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
```

## Twelfth adversarial panel on 1f79e480

**Reviewed revision:** 1f79e4802b5d492d7388022eab453795155e3651

Panel result: 0 approve, 3 block.

- adversarial panel / performance reviewer: block — claimant-component independence remains quadratic for a composite claimant and many distinct reviewer keys because every verdict scans every claimant key with an unbounded component count.
- adversarial panel / detection reviewer: block — a canonical receipt prefix can hide a start-anchored command in reviewer or finding text because the detector classifies the whole verdict line instead of each component.
- adversarial panel / identity reviewer: block — global combining-mark folding collapses distinct accented and ASCII action identities in projection and origin Counter keys.

All three blockers were accepted and repaired. This panel supplies no acceptance evidence
for the repair, and `--require-review` was not invoked against it.

## Bounded independence, component detection, and Unicode identity regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_neutralizer_derives_claimant_keys_once_for_many_verdicts automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_composite_claimant_component_count_is_bounded automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_derives_claimant_keys_once_for_many_verdicts automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_too_many_claimant_components automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_unit_keys_preserve_accented_identities automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_accepts_receipt_but_rejects_its_hostile_finding automation.tests.test_reconcile_queue.ReconcileQueueTests.test_handover_action_identity_preserves_accent_marks
........
----------------------------------------------------------------------
Ran 8 tests in 2.708s

OK
```

## Repaired owning modules

```
$ python3 -m unittest automation.tests.test_markdown_semantics automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_reconcile_queue
----------------------------------------------------------------------
Ran 777 tests in 241.185s

OK (skipped=1)
```

## Repaired full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 141.90s
```

## Repaired staged core-scope gate, reconciler, and diff check

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks && python3 automation/reconcile/reconcile.py --check
core-scope: pass (7 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
reconcile: 0 blocking finding(s)
```

## Independent takeover rerun on committed repair 9fd8c258

The interrupted implementation session completed commit
`9fd8c2581ac7aec5e89bb397917df73aae931705` while the takeover verification was
running. The tested tree did not change during either test command; this entry records
the takeover session's independently observed output rather than replacing the earlier
implementation evidence.

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_neutralizer_derives_claimant_keys_once_for_many_verdicts automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_composite_claimant_component_count_is_bounded automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_derives_claimant_keys_once_for_many_verdicts automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_too_many_claimant_components automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_unit_keys_preserve_accented_identities automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_accepts_receipt_but_rejects_its_hostile_finding automation.tests.test_reconcile_queue.ReconcileQueueTests.test_handover_action_identity_preserves_accent_marks
........
----------------------------------------------------------------------
Ran 8 tests in 4.928s

OK
```

```
$ python3 -m unittest automation.tests.test_markdown_semantics automation.tests.test_check_action_projection automation.tests.test_check_core_scope automation.tests.test_reconcile_queue
----------------------------------------------------------------------
Ran 777 tests in 260.371s

OK (skipped=1)
```

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 146.75s
```

## Final adversarial panel on a87701c

**Reviewed revision:** a87701ccbb493c561eece7691997703f0ec394cb

Panel result: 0 approve, 3 block.

- contract reviewer finding — The canonical verification template omits the enforced maximum claimant-component count and its fail-closed consequence.
- complexity reviewer finding — Unbounded claimant and reviewer key strings keep each independence comparison proportional to identity length, preserving quadratic total-input work for long identities and unique reviewers.
- detection reviewer finding — Accepted reviewer and finding units miss an addressed `block` command such as `Owner, block this release.` even though the structural receipt verdict itself must remain inert.

All three blockers were accepted and repaired after this exact revision. This panel supplies
no acceptance evidence for the repair, and `--require-review` was not invoked against it.

## Fixed-key, template-contract, and addressed-block focused regressions

```
$ python3 -m unittest automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_canonical_template_pins_claimant_and_key_bounds automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_long_authority_keys_have_one_fixed_size_representation automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_fixed_histograms_match_legacy_sorted_multiset_decisions automation.tests.test_markdown_semantics.ReviewReceiptSourceAllowlistTests.test_unique_long_reviewers_use_only_fixed_size_comparisons automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_provider_summary_allows_change_verbs_but_not_authority_asks automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_rejects_addressed_block_in_receipt_finding automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_bounds_unique_long_reviewer_comparisons automation.tests.test_check_core_scope.CoreScopeTests.test_review_parser_rejects_too_many_claimant_components
..........
----------------------------------------------------------------------
Ran 10 tests in 4.166s

OK
```

## Historical-panel compatibility repair

The first committed exact-range reconciler on `e0ea3c0602b031c3dd75fab87ea297726f5fd296`
reported 33 `task-action-origin` findings. Every finding was a historical completed panel
line shaped as `reviewer: block — finding`; the new general command token had
retroactively treated those records as asks. This was a failed verification attempt, not
a passing result. The guarded ambiguous form now excludes that completed-evidence
continuation while retaining addressed commands and malformed ASCII-hyphen near-misses.

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_provider_summary_allows_change_verbs_but_not_authority_asks automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_rejects_addressed_block_in_receipt_finding
....
----------------------------------------------------------------------
Ran 4 tests in 0.904s

OK
```

The amended commit hook selected all six owners of the changed action grammar:

```
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
tests: 6/6 files passed
test elapsed: 70.38s
pre-commit: OK
```

## Final compatibility full suite and exact committed range

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 139.65s
```

```
$ python3 automation/check_core_scope.py --range 4b467924b5832489829538164306439667e97aa0...6c9568b6833a2f3b77eaa6b8581b6e920c0bbc27 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (9 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

```
$ python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...6c9568b6833a2f3b77eaa6b8581b6e920c0bbc27 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
reconcile: 0 blocking finding(s)
```

```
$ git diff --check 4b467924b5832489829538164306439667e97aa0...6c9568b6833a2f3b77eaa6b8581b6e920c0bbc27
```

## Final3 adversarial panel on c5d6769

**Reviewed revision:** c5d676988eabb248f66000ecb2f3b72c47ef46b1

Panel result: 1 approve, 2 block.

```
- adversarial panel / correctness reviewer: block — An addressed block command using an em dash is silently missed outside receipts.
- adversarial panel / boundary reviewer: block — A global block em dash exception hides real owner directives outside completed verdict records.
- adversarial panel / core fit reviewer: approve — Core admission stays provider neutral, the canonical template pins the sixteen claimant limit, and accented action identities remain distinct.
```

Both blockers were accepted and repaired after this exact revision. This panel supplies no
acceptance evidence for the repair, and `--require-review` was not invoked against it.

## Historical-panel failure reproduction and regex path

After removing both generic `block(?![ \t]*—)` lookaheads and before adding the narrow
classification view, the task-action detector reported exactly 33 historical records:

```
$ python3 -c 'from pathlib import Path; import automation.check_action_projection as p; f=Path("tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md"); c=p.task_action_unit_counts(f.read_text(), f.as_posix()); print(sum(c.values()), len(c)); [print(n, repr(k)) for k,n in c.items()]'
33 33
1 '- adversarial panel / reviewer 1: block — basename-only matching lets nested notes/verification.md and case-variant Verification.md files hide approval-like prose that the core gate never accepts as a receipt.'
1 '- adversarial panel / reviewer 2: block — a matching line outside the one real Review verdicts section, or before its one valid full-commit field, receives an exception the formal gate never grants.'
1 '- adversarial panel / reviewer 3: block — duplicate or missing sections and revision fields leave receipt lookalikes unbound, so neutralizing their verdict token can hide a real human ask.'
1 '- adversarial panel / reviewer 3: block — the Review verdicts H2 ends only at another ATX H2, so ATX H1 and setext H1/H2 content can remain inside the receipt region and hide a later approval-like human action.'
1 '- adversarial panel / security reviewer: block — semantic blanking lets a nonblank raw comment, HTML block, fence, or indented code bridge the receipt to a later verdict that is then wrongly counted and neutralized.'
1 '- adversarial panel / correctness reviewer: block — punctuation-only and self reviewers can have their verdict token neutralized by action projection even though the core gate rejects those identities as independent evidence.'
1 '- adversarial panel / grammar reviewer: block — Python `.strip()` treats NBSP, form-feed, vertical-tab, Unicode separators, controls, and default-ignorables as blank, so hostile raw content can bridge a later verdict.'
1 '- adversarial panel / line-ending reviewer: block — removing only one trailing character does not define LF and CRLF bodies safely enough for the closed structural grammar.'
1 '- adversarial panel / identity reviewer: block — source-shaped identity tokens make zero-width or inline-HTML self reviewers appear distinct, leave markup-only names nonempty, and treat repository placeholders as identities.'
1 '- adversarial panel / identity-alias reviewer: block — Markdown link, reference, emphasis, and inline-code aliases can make a self reviewer appear distinct, while link destinations can mint apparent voters.'
1 '- adversarial panel / placeholder reviewer: block — rendered placeholders such as linked or emphasized TBD can retain source-shaped tokens and enter the voter set.'
1 '- adversarial panel / finding reviewer: block — decorated finding text can render as an approval request while source-shaped classification misses it after verdict neutralization.'
1 '- adversarial panel / identity reviewer: block — Markdown image labels can display the claimant while their destinations alter identity tokens or create apparent voters.'
1 '- adversarial panel / source-grammar reviewer: block — backslash escapes such as `cod\\_ex` remain source-decorated even when the partial renderer does not change them.'
1 '- adversarial panel / raw-source reviewer: block — claimant identity was derived from a semantic view, so inline or trailing HTML comments could disappear before the source whitelist saw the claimant suffix.'
1 '- adversarial panel / identity reviewer: block — NFKC preserved Unicode category-M marks, so visually equivalent reviewer spellings could become distinct voter keys and mark-decorated placeholders could remain identities.'
1 '- adversarial panel / action reviewer: block — the human-action normalizer also preserved combining marks, so approval or blocking keywords could evade ordinary detection.'
1 '- adversarial panel / input-grammar reviewer: block — punctuation-decorated placeholders could become voters, and a raw claimant line after prose or a blockquote could remain a CommonMark lazy continuation rather than top-level authority.'
1 '- adversarial panel / identity reviewer: block — Cyrillic and mixed-script homoglyphs could make a claimant and reviewer appear equal to a human while comparing as independent.'
1 '- adversarial panel / action reviewer: block — a Cyrillic first character in `approve` inside a formal finding could evade ordinary human-action detection.'
1 '- adversarial panel / identity-key reviewer: block — placeholder rejection used compact alphanumeric order while authority used a sorted character multiset, so reordered or anagram spellings such as `yet none` and `D B T` could become voters.'
1 '- adversarial panel / grammar reviewer: block — the shared source predicate allowed colon in claimant identity even though colon terminates reviewer identity in the receipt line.'
1 '- adversarial panel / visibility reviewer: block — an open hidden HTML container could cross a blank line, leave a claimant structurally visible, and still hide it from a human.'
1 '- adversarial panel / correctness reviewer: block — incomplete multiline raw HTML markers could leave the HTML parser stack empty while pending input still nested a later claimant or receipt, including a marker completed only after the authority line.'
1 '- adversarial panel / visibility reviewer: block — receipt heading, revision, and verdict lines were compared with structural Markdown but not with the rendered-human view, so invisible evidence could retain formal meaning.'
1 '- adversarial panel / complexity reviewer: block — each exact heading candidate reparsed its entire source prefix, making duplicate-heading rejection quadratic.'
1 '- adversarial panel / correctness reviewer: block — an exact revision field after an already accepted verdict still reset the receipt, although any non-verdict at that point should terminate and preserve the evidence already collected.'
1 '- adversarial panel / complexity reviewer: block — verdict neutralization called `semantic.count` and `semantic.rfind` on the growing prefix for every matched verdict, making a k-verdict document O(k*n).'
1 '- adversarial panel / composite-identity reviewer: block — the actual claimant `codex planner / sol-high implementer` was represented only by its combined key, so either component could appear to be a different reviewer.'
1 '- adversarial panel / alias reviewer: block — equality-only comparison admitted conservative prefix and suffix aliases such as a claimant component plus `reviewer`.'
1 '- adversarial panel / performance reviewer: block — claimant-component independence remains quadratic for a composite claimant and many distinct reviewer keys because every verdict scans every claimant key with an unbounded component count.'
1 '- adversarial panel / detection reviewer: block — a canonical receipt prefix can hide a start-anchored command in reviewer or finding text because the detector classifies the whole verdict line instead of each component.'
1 '- adversarial panel / identity reviewer: block — global combining-mark folding collapses distinct accented and ASCII action identities in projection and origin Counter keys.'
```

A single-line trace identified the active classification path:

```
$ python3 -c 'import automation.check_action_projection as p; u="- adversarial panel / reviewer: block — finding"; c=p.fold_unicode_marks(p.strip_action_emphasis(p.rendered_human_text(u))); c=p.strip_action_list_markers(c); print(repr(c)); print("ACTION_VERB", [(m.group(),m.span()) for m in p.ACTION_VERB_RE.finditer(c)]); print("TASK_AUTHORITY", [(m.group(),m.span()) for m in p.TASK_AUTHORITY_DIRECTIVE_RE.finditer(c)]); print("ADDRESSED", [(m.group(),m.span()) for m in p.ADDRESSED_HUMAN_DIRECTIVE_RE.finditer(c)]); print("task_like", p.action_like_task_record_prose(u)); print("unit", p.task_action_unit_counts(u,"tasks/1_in-progress/2026-07-23-example/verification.md"))'
'adversarial panel / reviewer: block — finding'
ACTION_VERB [('block', (30, 35))]
TASK_AUTHORITY [(': block', (28, 35))]
ADDRESSED []
task_like True
unit Counter({'- adversarial panel / reviewer: block — finding': 1})
```

`TASK_AUTHORITY_DIRECTIVE_RE` was the predicate used by task-record prose; the general
verb regex also recognized the word but was not the predicate that made this unit
actionable.

## Em-dash block and completed-panel focused regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_em_dash_block_directives_remain_actions_in_every_prose_view automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_limit_completed_panel_compatibility_shape automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_treat_core_fit_verdicts_as_receipts automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_check_action_projection.ActionProjectionTests.test_provider_summary_allows_change_verbs_but_not_authority_asks automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_rejects_addressed_block_in_receipt_finding
......
----------------------------------------------------------------------
Ran 6 tests in 1.210s

OK
```

## Owning affected modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_reconcile_queue
----------------------------------------------------------------------
Ran 630 tests in 214.386s

OK
```

## Full repository suite after the final3 repair

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 142.15s
```

## Staged core-scope, reconciler, and diff gates

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks && python3 automation/reconcile/reconcile.py --check
core-scope: pass (2 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
reconcile: 0 blocking finding(s)
```

## Commit hook and exact committed range

The implementation and its records were committed as
`50f2cf5da74524087dabc3dfefeeb627b045c767`. Its hook selected all six registered
owners of the changed action grammar:

```
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
tests: 6/6 files passed
test elapsed: 72.65s
pre-commit: OK
```

The first combined exact-range command used an abbreviated head. Core scope accepted Git's
revision spelling, then the stricter reconciler rejected the non-full range before checking
repository state:

```
$ python3 automation/check_core_scope.py --range 4b467924b5832489829538164306439667e97aa0...50f2cf5 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks && python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...50f2cf5 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks && git diff --check 4b467924b5832489829538164306439667e97aa0...50f2cf5
core-scope: pass (9 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
usage: reconcile.py [-h] [--check] [--file-retries] [--fix-index]
                    [--fix-open-actions] [--fail-on-advisory]
                    [--at-transition NAME] [--task-id ID | --branch NAME]
                    [--range BASE...HEAD|root:HEAD] [--displaced-tip FULL_OID]
reconcile.py: error: --range must be full-base...full-head or root:full-head
```

The immediate retry used both full object IDs and passed all three gates:

```
$ python3 automation/check_core_scope.py --range 4b467924b5832489829538164306439667e97aa0...50f2cf5da74524087dabc3dfefeeb627b045c767 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks && python3 automation/reconcile/reconcile.py --check --range 4b467924b5832489829538164306439667e97aa0...50f2cf5da74524087dabc3dfefeeb627b045c767 --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks && git diff --check 4b467924b5832489829538164306439667e97aa0...50f2cf5da74524087dabc3dfefeeb627b045c767
core-scope: pass (9 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
reconcile: 0 blocking finding(s)
```

## Final4 adversarial panel on 7ddab99

**Reviewed revision:** 7ddab99d446bf6befcd26b57515325c9a49fd436

Panel result: 1 approve, 2 block.

```
- adversarial panel / correctness reviewer: block — Conjoined commands inside accepted findings are missed after the receipt line is blanked.
- adversarial panel / boundary reviewer: block — Completed panel compatibility can hide decorated human action findings in task verification records.
- adversarial panel / core fit reviewer: approve — Provider-neutral receipt authority stays confined to task-root verification, review freshness remains bound to core and task inputs, and historical panel compatibility grants no review authority.
```

Both blockers were accepted and repaired after this exact revision. This panel supplies no
acceptance evidence for the repair, and `--require-review` was not invoked against it.

## Completed-review visibility focused regressions

```
$ python3 -m unittest automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_limit_completed_panel_compatibility_shape automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_render_completed_panel_findings_once automation.tests.test_check_action_projection.ActionProjectionTests.test_completed_panel_neutralizes_only_exact_lowercase_verdict_tokens automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_keep_benign_panel_conjunctions_inert automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_scan_core_fit_reviewer_and_finding_text automation.tests.test_reconcile_queue.ReconcileQueueTests.test_task_action_origin_rejects_completed_review_hidden_commands
......
----------------------------------------------------------------------
Ran 6 tests in 2.242s

OK
```

The focused assertions bind each result, not only the suite exit: the formal conjoined
command and each of the three decorated historical findings produce one action; an
overlap found by both line and component paths produces one; two duplicate hostile lines
produce two; both exact lowercase verdict tokens are neutralized; and benign conjunction,
approval-record, bare-verb, inline-code, and image descriptions produce zero.

## Completed-review visibility owning modules

```
$ python3 -m unittest automation.tests.test_check_action_projection automation.tests.test_reconcile_queue
----------------------------------------------------------------------
Ran 634 tests in 227.864s

OK
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
reconcile: 0 blocking finding(s)
```

Negative snapshot tests printed their expected diagnostic lines during this run; the
owning command completed with exit status 0.

## Completed-review visibility full repository suite

```
$ python3 automation/run_tests.py --jobs 4
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 145.19s
```

## Sixteenth adversarial panel on ccbb9e4

Three independent reviewers with distinct lenses examined the exact revision
`ccbb9e4854faf42dc423638e6b6b39a284608f4b` in separate linked worktrees, with no view of
each other or of the implementer's self-assessment. The vote was 0 approve, 3 block.
Two findings were reproduced a fourth time by the orchestrating session before recording.

Reproduced truncation of a mixed panel, run against this revision:

```
$ python3 -c "core_fit_review_evidence(one approve and two block, second finding backticked)"
section_count: 1  revision_count: 1
verdicts parsed: 1
   -> - core-fit / lens one: approve — could not break it.
TALLY: 1 approve, 0 block
GATE RESULT: PASS (approve majority)
```

The first verdict whose finding leaves the closed source alphabet ends the receipt and
discards its own vote together with every later vote. Position decides the loss: an
invalid finding first discarded all three votes, in the middle discarded two, last
discarded one. A control panel of the same three verdicts in plain text parsed all three.

Recordability of ordinary finding text, run against this revision:

```
DROP markdown semantics dot py truncates verdicts.   (underscore)
DROP issue number 80 is still open.                  (number sign)
DROP coverage fell 5 percent overall.                (percent sign)
OK   a block vote is dropped; the gate then passes.
```

A reviewer cannot name the defective module inside a finding. The second reviewer measured
thirteen of fourteen realistic finding texts rejected, including backticked paths, curly
apostrophes, a second em dash, and Markdown links.

The third reviewer measured the action vocabulary widening over all 336 task Markdown
files with the same data and only the code swapped: 23 actionable units at main became 48
at this revision, five removals and thirty new detections across eleven existing files.

Two reviewers independently reported that `neutralize_core_fit_review_verdict_tokens` is
imported by the action gate and never called by any production path, so the test that pins
the authorized token-only behavior asserts against an unreachable function. Two reviewers
independently reported an undocumented `- adversarial panel /` grammar that grants receipt
neutrality with no heading, no reviewed-revision binding, no claimant, and no independence
check.

## Review verdicts

**Reviewed revision:** ccbb9e4854faf42dc423638e6b6b39a284608f4b

- core-fit / fail-open lens: block — verdict lines are blanked whole, so an ask wrapped onto the next line escapes detection.
- core-fit / authorized-scope lens: block — the closed finding alphabet silently drops a block verdict and every verdict after it.
- core-fit / regression lens: block — adding block to the action vocabulary flags ordinary prose in eleven existing files.

Every finding above is written inside the closed source alphabet because findings outside
it are discarded without warning. That constraint is itself the first reviewer's finding.

## Rebuilt narrow receipt parser — focused regressions

Eleven tests, one per invariant the sixteenth panel named.

```
$ python3 -m unittest \
    automation.tests.test_check_core_scope.CoreScopeTests.test_review_receipt_accepts_findings_written_in_ordinary_prose \
    automation.tests.test_check_core_scope.CoreScopeTests.test_mixed_panel_tally_never_loses_a_verdict \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_verdict_the_receipt_cannot_accept_fails_it_loudly \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_verdict_outside_the_contiguous_block_fails_the_receipt \
    automation.tests.test_check_core_scope.CoreScopeTests.test_review_receipt_needs_exactly_one_real_heading_and_revision \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_accept_a_canonical_review_receipt \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_receipt_neutralization_blanks_the_token_and_nothing_else \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_report_an_ask_in_a_reviewer_or_a_finding \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_report_an_ask_on_a_wrapped_finding_line \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_task_action_units_give_receipt_near_misses_no_exemption \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_a_malformed_verdict_refuses_the_whole_receipt
...........
----------------------------------------------------------------------
Ran 11 tests in 0.141s

OK
```

## Rebuilt parser — the sixteenth panel's fail-open, replayed

The same one-approve, two-block panel the withdrawn parser reported as `1 approve, 0
block`. Its three findings carry a backticked path, a percent sign, a number sign, a
curly apostrophe, and two extra em dashes — every class the closed alphabet rejected.
The script is `tmp/probe.py`, reproduced inline below the output. It was run at
`1d536d0ba12268c75cf642817acc208ca97935c0` and does not run at any later revision: it
calls `accepted_verdict_token_spans`, which existed only in that revision's module. The
equivalent behavior at HEAD is recorded under the eighteenth-panel sections below.

```
$ python3 tmp/probe.py
verdicts parsed: 3
tally: 1 approve, 2 block
errors: ()
spans: ((110, 117), (178, 183), (241, 246))
same length: True
changed offsets outside the token spans: []
'- core-fit / first:         — the `automation/x.py` boundary holds'
'- core-fit / second:       — 50% of the adapters break, see #81'
'- core-fit / third:       — the reviewer’s case — nested — still parses'
```

```python
import sys
sys.path.insert(0, "automation")
import check_action_projection as CAP
import review_receipt as RR
from markdown_semantics import semantic_text

REVISION = "a" * 40
PANEL = (
    "- core-fit / first: approve — the `automation/x.py` boundary holds\n"
    "- core-fit / second: block — 50% of the adapters break, see #81\n"
    "- core-fit / third: block — the reviewer’s case — nested — still parses\n"
)
DOCUMENT = f"# V\n\n## Review verdicts\n\n**Reviewed revision:** {REVISION}\n\n{PANEL}"

receipt = RR.parse_review_receipt(semantic_text(DOCUMENT))
tally = [entry.verdict for entry in receipt.verdicts]
print("verdicts parsed:", len(receipt.verdicts))
print("tally:", tally.count("approve"), "approve,", tally.count("block"), "block")
print("errors:", receipt.errors)

rendered = CAP.rendered_human_text(DOCUMENT)
spans = CAP.accepted_verdict_token_spans(rendered)
blanked = CAP.blank_spans(rendered, spans)
print("spans:", spans)
print("same length:", len(rendered) == len(blanked))
changed = {index for index, (a, b) in enumerate(zip(rendered, blanked)) if a != b}
print("changed offsets outside the token spans:",
      sorted(i for i in changed if not any(s <= i < e for s, e in spans)))
for line in blanked.splitlines()[-3:]:
    print(repr(line))
```

## Rebuilt parser — staged diff and core-scope gate

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (6 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Rebuilt parser — change size against the withdrawn implementation

```
$ git diff --cached --stat main -- automation templates
 automation/check_action_projection.py            |   7 +-
 automation/check_core_scope.py                   |  39 ++-----
 automation/review_receipt.py                     | 141 +++++++++++++++++++++++
 automation/tests/test_check_action_projection.py | 118 +++++++++++++++++++
 automation/tests/test_check_core_scope.py        | 136 ++++++++++++++++++++++
 templates/task/verification.md                   |   9 +-
 6 files changed, 418 insertions(+), 32 deletions(-)
```

The withdrawn implementation was 3746 insertions and 81 deletions over the same two
folders, across four source files and four test files.

## Rebuilt parser — the filled template through the action gate

`templates/README.md` requires that copying a template and replacing its placeholders
produces a valid item. The filled copy was passed to `task_action_unit_counts` once per
verdict token.

```
$ python3 tmp/filled_template.py
--- verdict token 'approve': 1 unprojected action(s) ---
    1 '- adversarial panel / reviewer-b: approve — could not break it'
--- verdict token 'block': 0 unprojected action(s) ---
```

The `core-fit` receipt line is neutral in both fills. The remaining unit is the
non-`core-fit` lens line, which the 2026-08-04 grammar deliberately leaves outside the
receipt and which behaves exactly as it does on `main`; closing it needs the second panel
grammar the 2026-08-07 withdrawal decision forbids.

```python
import sys
sys.path.insert(0, "automation")
from pathlib import Path
import check_action_projection as CAP

raw = Path("templates/task/verification.md").read_text(encoding="utf-8")
filled = (
    raw
    .replace("<task title>", "Stop review verdicts from looking like human asks")
    .replace("<YYYY-MM-DD> by <who>", "2026-08-07 by sol-high")
    .replace('<check name, e.g. "unit tests">', "unit tests")
    .replace("<exact command>", "python3 automation/run_tests.py")
    .replace("<real output, trimmed to the meaningful part>", "tests: 15/15 files passed")
    .replace("<full immutable commit ID reviewed by every verdict below>", "b" * 40)
    .replace("<reviewer other than Claimed-by>", "reviewer-a")
    .replace(
        "<substitution or boundary challenged; required only when "
        "`--require-review` is explicitly selected>",
        "another agent runtime reads the same files, so the boundary holds",
    )
    .replace("<reviewer / lens>", "adversarial panel / reviewer-b")
    .replace('<one-line finding or "could not break it">', "could not break it")
)
for token in ("approve", "block"):
    text = filled.replace("<approve | block>", token)
    counts = CAP.task_action_unit_counts(
        text, "tasks/1_in-progress/2026-08-04-example/verification.md", ()
    )
    print(f"--- verdict token {token!r}: {sum(counts.values())} unprojected action(s) ---")
    for excerpt, count in counts.items():
        print("   ", count, repr(excerpt))
```

## Rebuilt parser — full repository suite

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 44.19s
```

## Rebuilt parser — reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

No independent review has been run against the rebuilt parser. `--require-review` was not
invoked, and this session wrote no receipt for its own work.

## Seventeenth panel repair — every hole replayed against the repaired parser

One script per finding class. Item 1 is the decisive one: each variant previously parsed
as `1 approve, 0 block` with no error, so the gate passed a panel that rejected the
change. The script is `tmp/repairs.py`, reproduced below its output. It was run at
`f824780504015e628696d6947af357975ec21a52`. Re-running it at HEAD prints the same lines
except item 5's `parse errors:`, which now shows a `ReceiptError(...)` repr rather than a
bare string, because problems carry their line number since then.

```
$ python3 tmp/repairs.py
1. marker and delimiter variants on the two block verdicts
   1. ordered  in block: 0 approve, 0 block, 2 error(s)   stranded: 0 approve, 0 block, 1 error(s)
   1) ordered  in block: 0 approve, 0 block, 2 error(s)   stranded: 0 approve, 0 block, 1 error(s)
   no marker   in block: 0 approve, 0 block, 2 error(s)   stranded: 0 approve, 0 block, 1 error(s)
   bullet      in block: 0 approve, 0 block, 2 error(s)   stranded: 0 approve, 0 block, 1 error(s)
   hyphen      in block: 0 approve, 0 block, 2 error(s)   stranded: 0 approve, 0 block, 1 error(s)
   en dash     in block: 0 approve, 0 block, 2 error(s)   stranded: 0 approve, 0 block, 1 error(s)
2. reviewer with no identity
   reviewer='  ': 0 approve, 0 block, 1 error(s)
   reviewer='🛑': 0 approve, 0 block, 1 error(s)
   reviewer='_': 0 approve, 0 block, 1 error(s)
   reviewer='...': 0 approve, 0 block, 1 error(s)
   reviewer='-': 0 approve, 0 block, 1 error(s)
3. heading exactness
   exact           : 1 approve, 0 block, 0 error(s)
   parenthetical   : 0 approve, 0 block, 1 error(s)
4. which artifact may claim the exemption
   tasks/1_in-progress/2026-08-04-example/verification.md     0 action(s)
   tasks/1_in-progress/2026-08-04-example/worklog.md          1 action(s)
   tasks/1_in-progress/2026-08-04-example/design.md           1 action(s)
   tasks/1_in-progress/2026-08-04-example/notes/verification.md 1 action(s)
5. raw HTML that only renders as a receipt
   rendered view contains the heading: True
   parse errors: ('verification.md needs exactly one exact `## Review verdicts` heading',)
   actions reported: 1
```

```python
import sys
sys.path.insert(0, "automation")
import check_action_projection as CAP
import review_receipt as RR

REVISION = "a" * 40
PATH = "tasks/1_in-progress/2026-08-04-example/verification.md"
APPROVE = "- core-fit / first: approve — could not break it\n"


def receipt(body, heading="## Review verdicts"):
    return f"# V\n\n{heading}\n\n**Reviewed revision:** {REVISION}\n\n{body}"


def tally(body, heading="## Review verdicts"):
    parsed = RR.parse_review_receipt(receipt(body, heading))
    votes = [entry.verdict for entry in parsed.verdicts]
    return (f"{votes.count('approve')} approve, {votes.count('block')} block, "
            f"{len(parsed.errors)} error(s)")


print("1. marker and delimiter variants on the two block verdicts")
for name, shape in (
    ("1. ordered", "1. core-fit / {0}: block — {1}\n"),
    ("1) ordered", "1) core-fit / {0}: block — {1}\n"),
    ("no marker ", "core-fit / {0}: block — {1}\n"),
    ("bullet    ", "• core-fit / {0}: block — {1}\n"),
    ("hyphen    ", "- core-fit / {0}: block - {1}\n"),
    ("en dash   ", "- core-fit / {0}: block – {1}\n"),
):
    inside = APPROVE + shape.format("b", "a bypass") + shape.format("c", "same bypass")
    after = APPROVE + "\nThe panel adjourned.\n\n" + shape.format("b", "a bypass")
    print(f"   {name}  in block: {tally(inside)}   stranded: {tally(after)}")

print("2. reviewer with no identity")
for reviewer in ("  ", "\N{OCTAGONAL SIGN}", "_", "...", "-"):
    body = APPROVE + f"- core-fit / {reviewer}: block — a bypass\n"
    print(f"   reviewer={reviewer!r}: {tally(body)}")

print("3. heading exactness")
print("   exact           :", tally(APPROVE))
print("   parenthetical   :",
      tally(APPROVE, "## Review verdicts (when a review was explicitly run)"))

print("4. which artifact may claim the exemption")
document = receipt(APPROVE)
for path in (
    "tasks/1_in-progress/2026-08-04-example/verification.md",
    "tasks/1_in-progress/2026-08-04-example/worklog.md",
    "tasks/1_in-progress/2026-08-04-example/design.md",
    "tasks/1_in-progress/2026-08-04-example/notes/verification.md",
):
    counts = CAP.task_action_unit_counts(document, path, ())
    print(f"   {path:58s} {sum(counts.values())} action(s)")

print("5. raw HTML that only renders as a receipt")
html = (
    "<p>## Review verdicts</p>\n"
    f"<p>**Reviewed revision:** {REVISION}</p>\n"
    "<p>- core-fit / first: approve — could not break it</p>\n"
)
print("   rendered view contains the heading:",
      "## Review verdicts" in CAP.rendered_human_text(html))
print("   parse errors:", RR.parse_review_receipt(html).errors)
print("   actions reported:",
      sum(CAP.task_action_unit_counts(html, PATH, ()).values()))
```

## Seventeenth panel repair — the new regressions fail on the blocked revision

The six new core-scope tests were run against `1d536d0`'s parser and gates, with the
tests themselves left at the repaired revision. Eighteen subtests across three of the six
tests fail there and all pass after the repair. The other three cover behavior `1d536d0`
already had; they are mutation coverage, not repair evidence. The two dash variants pass
inside the block at `1d536d0` because its narrower recognizer already required a bullet,
and fail only in the stranded position — which is the asymmetry the repair removes.

```
$ git checkout 1d536d0 -- automation/review_receipt.py automation/check_core_scope.py automation/check_action_projection.py
$ python3 -m unittest automation.tests.test_check_core_scope
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='ordered 1. marker', placement='inside the block')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='ordered 1. marker', placement='stranded after it')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='ordered 1) marker', placement='inside the block')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='ordered 1) marker', placement='stranded after it')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='no marker at all', placement='inside the block')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='no marker at all', placement='stranded after it')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='bullet glyph marker', placement='inside the block')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='bullet glyph marker', placement='stranded after it')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='ascii hyphen dash', placement='stranded after it')
FAIL: test_a_marker_or_dash_variant_never_leaves_the_tally_silently (case='en dash', placement='stranded after it')
FAIL: test_a_reviewer_without_an_identity_is_refused_not_dropped (reviewer='  ')
FAIL: test_a_reviewer_without_an_identity_is_refused_not_dropped (reviewer='🛑')
FAIL: test_a_reviewer_without_an_identity_is_refused_not_dropped (reviewer='_')
FAIL: test_a_reviewer_without_an_identity_is_refused_not_dropped (reviewer='...')
FAIL: test_a_reviewer_without_an_identity_is_refused_not_dropped (reviewer='-')
FAIL: test_a_reviewer_without_an_identity_is_refused_not_dropped (reviewer='( )')
FAIL: test_only_the_exact_review_verdicts_heading_opens_a_receipt (heading='## Review verdicts (when a review was explicitly run)')
FAIL: test_only_the_exact_review_verdicts_heading_opens_a_receipt (heading='## Review verdicts today')
Ran 68 tests in 1.618s

FAILED (failures=18, skipped=1)
```

## Seventeenth panel repair — focused regressions

```
$ python3 -m unittest \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_marker_or_dash_variant_never_leaves_the_tally_silently \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_reviewer_without_an_identity_is_refused_not_dropped \
    automation.tests.test_check_core_scope.CoreScopeTests.test_only_the_exact_review_verdicts_heading_opens_a_receipt \
    automation.tests.test_check_core_scope.CoreScopeTests.test_verdict_line_details_the_grammar_actually_depends_on \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_second_revision_field_anywhere_in_the_section_fails_closed \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_later_h2_ends_the_receipt_section \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_no_list_marker_or_dash_can_slip_a_verdict_past_the_receipt \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_only_a_task_verification_record_may_claim_a_receipt \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_raw_html_cannot_render_a_receipt_no_gate_validated \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_receipt_neutralization_blanks_the_token_and_nothing_else
..........
----------------------------------------------------------------------
Ran 10 tests in 0.154s

OK
```

## Seventeenth panel repair — the filled template through the action gate

Unchanged by this pass: the `core-fit` receipt line is neutral, and the non-`core-fit`
lens line still projects an action when filled with `approve`, exactly as on `main`.

```
$ python3 tmp/filled_template.py
--- verdict token 'approve': 1 unprojected action(s) ---
    1 '- adversarial panel / reviewer-b: approve — could not break it'
--- verdict token 'block': 0 unprojected action(s) ---
```

## Seventeenth panel repair — full repository suite

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 44.57s
```

## Seventeenth panel repair — reconciler and core-scope gate

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

```
$ git diff --cached --check && python3 automation/check_core_scope.py --staged --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks
core-scope: pass (6 core path(s), task 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; independent review manual; not invoked)
```

## Seventeenth panel repair — the pull-request reconciler command

The command CI runs on a pull request (`.github/workflows/harness.yml` builds its range
from `pull_request.base.sha...pull_request.head.sha`). It still exits 1, and the reason is
not the repaired parser: both findings come from intermediate commits, not from the branch
head. The same command from the withdrawal baseline forward is clean.

The range head must be the current HEAD, so both commands below derive it. A reader can
re-run them exactly as written at any later commit on this branch and get this output,
because what they report depends on the intermediate commits, not on the head. The runs
recorded here were made at `4b66357fd501b4cee6700d6b6ccad6b694197262`.

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks --range "$(git rev-parse main)...$(git rev-parse HEAD)"
[task-action-origin] tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md: task artifact introduced an unqueued human action: - adversarial panel / core fit reviewer: approve — Core admission stays provider neutral, the canonical template pins the sixteen claimant limit, and accented action identities remain distinct.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
[task-action-origin] tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md: task artifact introduced an unqueued human action: - adversarial panel / core fit reviewer: approve — Provider-neutral receipt authority stays confined to task-root verification, review freshness remains bound to core and task inputs, and historical panel compatibility grants no review authority.
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
reconcile: 2 blocking finding(s)
```

```
$ python3 automation/reconcile/reconcile.py --check --at-transition merge --branch task/2026-08-04-stop-review-verdicts-from-looking-like-human-asks --range "679a62a8d00435a8169746b72285d967bd26945c...$(git rev-parse HEAD)"
reconcile: 0 blocking finding(s)
```

Both lines are fenced at the head, so `task_action_unit_counts` over the current file
reports nothing:

```
$ python3 -c 'import sys; sys.path.insert(0, "automation"); from pathlib import Path; import check_action_projection as p; f = "tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md"; print(sum(p.task_action_unit_counts(Path(f).read_text(), f, ()).values()))'
0
```

A task edge is evaluated against the bytes of its own commit, so a fence added later
cannot repair `50f2cf5` and `df0a5de`, the two commits that wrote those transcripts. They
committed cleanly at the time because the implementation they carried exempted
`- adversarial panel / …` lines under the second receipt grammar that the 2026-08-07
decision withdrew. Recorded as
[a known issue](../../../memory/known-issues/2026-08-07-withdrawn-panel-grammar-reopens-two-branch-edges.md)
with the three options and why none of them is an agent's to choose alone.

## Eighteenth panel repair — every decorated near-miss is now reported

Sixteen forms a writer could plausibly type. Before this pass, fifteen of them parsed as
`1 approve, 0 block` with no error at all: the rejector allowed exactly one decoration
character, so two escaped it. The rejector's only power is to refuse, so widening it can
report more and accept nothing new; the acceptor is untouched. The script is
`tmp/decorations.py`, reproduced below the output.

```
$ python3 tmp/decorations.py
=== item 1: decorated near-misses (want err>=1 and 0a/0b) ===
  0a/0b err=1    **- core-fit / d: block — dissent
  0a/0b err=1    - [ ] core-fit / d: block — dissent
  0a/0b err=1    > - core-fit / d: block — dissent
  0a/0b err=1    - `core-fit` / d: block — dissent
  0a/0b err=1    - **core-fit** / d: block — dissent
  0a/0b err=1    - core‑fit / d: block — dissent
  0a/0b err=1    -- core-fit / d: block — dissent
  0a/0b err=1    * * core-fit / d: block — dissent
  0a/0b err=1    + > core-fit / d: block — dissent
  0a/0b err=1    1.. core-fit / d: block — dissent
  0a/0b err=1    (1) core-fit / d: block — dissent
  0a/0b err=1      * core-fit / d: block — dissent
  0a/0b err=1    • - core-fit / d: block — dissent
  0a/0b err=1    - _core-fit_ / d: block — dissent
  0a/0b err=1    - ~~core-fit~~ / d: block — dissent
  0a/0b err=1    - core - fit / d: block — dissent
=== item 3: entity / autolink / inline tag in the finding ===
  core gate: 1 verdict(s) 0 err | action gate: 0 action(s) | see <https://example.com/adr> for the rule
  core gate: 1 verdict(s) 0 err | action gate: 0 action(s) | the &amp; in the finding survives
  core gate: 1 verdict(s) 0 err | action gate: 0 action(s) | boundary holds for <div> containers
```

The second block is acceptance criterion 1: before this pass each of those three was
counted by the core gate and reported as an unqueued human action by the action gate,
which refuses the commit. The token is now placed by the verdict's own prefix — marker,
reviewer, token — so markup later in the finding cannot move it.

```python
import sys
sys.path.insert(0, "automation")
import review_receipt as rr
import check_action_projection as cap

REV = "a" * 40
PATH = "tasks/1_in-progress/2026-08-04-x/verification.md"
APPROVE = "- core-fit / a: approve — ok\n"


def doc(body):
    return "# V\n\n## Review verdicts\n\n**Reviewed revision:** " + REV + "\n\n" + body


def tally(body):
    parsed = rr.parse_review_receipt(doc(body))
    votes = [entry.verdict for entry in parsed.verdicts]
    return "{0}a/{1}b err={2}".format(
        votes.count("approve"), votes.count("block"), len(parsed.errors)
    )


DECOR = [
    "**- core-fit / d: block — dissent",
    "- [ ] core-fit / d: block — dissent",
    "> - core-fit / d: block — dissent",
    "- `core-fit` / d: block — dissent",
    "- **core-fit** / d: block — dissent",
    "- core‑fit / d: block — dissent",
    "-- core-fit / d: block — dissent",
    "* * core-fit / d: block — dissent",
    "+ > core-fit / d: block — dissent",
    "1.. core-fit / d: block — dissent",
    "(1) core-fit / d: block — dissent",
    "  * core-fit / d: block — dissent",
    "• - core-fit / d: block — dissent",
    "- _core-fit_ / d: block — dissent",
    "- ~~core-fit~~ / d: block — dissent",
    "- core - fit / d: block — dissent",
]

print("=== item 1: decorated near-misses (want err>=1 and 0a/0b) ===")
for line in DECOR:
    print("  {0:14s} {1}".format(tally(APPROVE + line + "\n"), line))

print("=== item 3: entity / autolink / inline tag in the finding ===")
for finding in (
    "see <https://example.com/adr> for the rule",
    "the &amp; in the finding survives",
    "boundary holds for <div> containers",
):
    body = "- core-fit / a: approve — " + finding + "\n"
    parsed = rr.parse_review_receipt(doc(body))
    units = cap.task_action_unit_counts(doc(body), PATH, ())
    print("  core gate: {0} verdict(s) {1} err | action gate: {2} action(s) | {3}".format(
        len(parsed.verdicts), len(parsed.errors), sum(units.values()), finding
    ))
```

## Eighteenth panel repair — what a receipt problem now says

Every problem carries the file and the line. A stranded verdict names the line that
actually ended the block rather than itself. A refused heading quotes the spelling it
found. Twelve near-misses report five problems and a count of the rest.

The script is `tmp/messages.py`, reproduced below its output.

```
$ python3 tmp/messages.py
-- stranded after a wrapped finding
    tasks/1_in-progress/x/verification.md:11: Review verdicts has a core-fit line outside the contiguous receipt block, which ended at line 10: the wrap continues here
-- stranded after prose
    tasks/1_in-progress/x/verification.md:13: Review verdicts has a core-fit line outside the contiguous receipt block, which ended at line 11: The panel adjourned.
-- uncanonical inside the block
    tasks/1_in-progress/x/verification.md:10: Review verdicts rejects a core-fit line that is not `- core-fit / <reviewer>: <approve|block> — <finding>`: **- core-fit / b: block — decorated
-- no identity
    tasks/1_in-progress/x/verification.md:9: Review verdicts rejects a core-fit line whose reviewer has no identity: - core-fit /  : approve — ok
-- revision not first
-- inexact heading
    tasks/1_in-progress/x/verification.md:5: verification.md needs exactly one exact `## Review verdicts` heading; found `## Review verdicts (when a review was explicitly run)`
-- two exact headings
    tasks/1_in-progress/x/verification.md:11: verification.md needs exactly one exact `## Review verdicts` heading; found 2 of them
-- twelve near-misses -> 6 reported
    v.md:10: Review verdicts rejects a core-fit line that is not `- core-fit / <reviewer>: <approve|block> — <find
    v.md:11: Review verdicts has a core-fit line outside the contiguous receipt block, which ended at line 10: **-
    v.md:12: Review verdicts has a core-fit line outside the contiguous receipt block, which ended at line 10: **-
    v.md:13: Review verdicts has a core-fit line outside the contiguous receipt block, which ended at line 10: **-
    v.md:14: Review verdicts has a core-fit line outside the contiguous receipt block, which ended at line 10: **-
    v.md: Review verdicts has 7 further problem(s) not listed
```

```python
import sys
sys.path.insert(0, "automation")
import review_receipt as rr

REV = "a" * 40


def doc(body, heading="## Review verdicts"):
    return "# V\n\nintro\n\n" + heading + "\n\n**Reviewed revision:** " + REV + "\n\n" + body


def show(name, body, **kw):
    parsed = rr.parse_review_receipt(doc(body, **kw))
    print("--", name)
    for line in rr.formatted_errors(parsed, "tasks/1_in-progress/x/verification.md"):
        print("   ", line)


show("stranded after a wrapped finding", (
    "- core-fit / a: approve — the boundary holds but\n"
    "  the wrap continues here\n"
    "- core-fit / b: block — flawless line\n"
))
show("stranded after prose", (
    "- core-fit / a: approve — ok\n\nThe panel adjourned.\n\n"
    "- core-fit / b: block — flawless line\n"
))
show("uncanonical inside the block", (
    "- core-fit / a: approve — ok\n**- core-fit / b: block — decorated\n"
))
show("no identity", "- core-fit /  : approve — ok\n")
show("revision not first", "x\n", heading="## Review verdicts")
show("inexact heading", "- core-fit / a: approve — ok\n",
     heading="## Review verdicts (when a review was explicitly run)")
show("two exact headings",
     "- core-fit / a: approve — ok\n\n## Review verdicts\n\n"
     "**Reviewed revision:** " + REV + "\n\n- core-fit / b: approve — ok\n")

many = "- core-fit / a: approve — ok\n" + "".join(
    "**- core-fit / r{0}: block — decorated\n".format(n) for n in range(12)
)
parsed = rr.parse_review_receipt(doc(many))
print("-- twelve near-misses ->", len(parsed.errors), "reported")
for line in rr.formatted_errors(parsed, "v.md"):
    print("   ", line[:110])
```

That run is pinned to `4b66357fd501b4cee6700d6b6ccad6b694197262`. At HEAD the same script
prints the same problems with the wording the eighteenth-panel repair gave them.

The `revision not first` probe prints nothing because its own fixture is malformed — it
puts the revision field first regardless. That path is covered by
`test_the_revision_field_must_be_the_first_line_of_the_receipt`, which asserts the message
and its line number.

## Eighteenth panel repair — the filled template no longer projects an action

The other-lens verdict is now written with its verdict word in a code span, in both
`templates/task/verification.md` and `skills/adversarial-review/SKILL.md`. Filled either
way, the template projects nothing. Every earlier run of this script reported one action
for the `approve` fill.

```
$ python3 tmp/filled_template.py
--- verdict token 'approve': 0 unprojected action(s) ---
--- verdict token 'block': 0 unprojected action(s) ---
```

## Eighteenth panel repair — focused regressions

```
$ python3 -m unittest \
    automation.tests.test_check_core_scope.CoreScopeTests.test_decoration_around_a_verdict_never_leaves_the_tally_silently \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_finding_carrying_markup_is_still_a_counted_verdict \
    automation.tests.test_check_core_scope.CoreScopeTests.test_receipt_problems_name_the_file_the_line_and_the_block_end \
    automation.tests.test_check_core_scope.CoreScopeTests.test_receipt_problems_are_capped_and_counted \
    automation.tests.test_check_core_scope.CoreScopeTests.test_the_revision_field_must_be_the_first_line_of_the_receipt \
    automation.tests.test_check_core_scope.CoreScopeTests.test_an_equal_split_is_not_an_approve_majority \
    automation.tests.test_check_core_scope.CoreScopeTests.test_one_reviewer_voting_twice_keeps_only_the_later_verdict \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_reviewer_may_not_contain_a_colon \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_a_finding_carrying_markup_is_still_neutralized \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_a_verdict_prefix_the_rendered_view_lost_blanks_nothing \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_the_receipt_path_is_matched_whole_and_never_by_suffix
...........
----------------------------------------------------------------------
Ran 11 tests in 0.131s

OK
```

## Eighteenth panel repair — full repository suite and reconciler

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_integrate.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_open_actions.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 44.82s
```

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Nineteenth panel repair — the three defects, replayed

One script, `tmp/regressions.py`, reproduced below its output. Item 1 is the regression
the previous pass introduced: placement scanned the rendered view from line 0, so a
superseded lookalike above the receipt absorbed the blanking. The real verdict was then
reported as an unqueued ask, and seven characters of the decoy's own word — `approved`
became `       d` — were erased on a line that is not in any receipt.

```
$ python3 tmp/regressions.py
=== item 1: decoy above the receipt ===
  actions reported: 0
   line: '- core-fit / dana: approved — round one, superseded'
   line: '- core-fit / dana:         — the boundary holds'

=== item 2: eight escapes ===
  0a/0b err=1    - **core**-**fit** / d: block — dissent
  0a/0b err=1    - `core` - `fit` / d: block — dissent
  0a/0b err=1    - core -- fit / d: block — dissent
  0a/0b err=1    - core...-...fit / d: block — dissent
  0a/0b err=1    - core-fit ／ d: block — dissent
  0a/0b err=1    - lens core-fit / d: block — dissent
  0a/0b err=1    Note: core-fit / d: block — dissent
  0a/0b err=1    - xcore-fit / d: block — dissent

=== item 3: verdicts the structural view blanks ===
  0a/0b err=1    indented 4
  0a/0b err=1    indented 8
  0a/0b err=1    div block
  0a/0b err=1    inline span
  0a/0b err=1    fenced
  0a/0b err=1    comment
```

At `6d84769` the first block reported one action and mutated the decoy, and every line in
the second block, plus `div block`, `inline span`, `fenced` and `comment` in the third,
read `1a/0b err=0` — the panel's verdict silently dropped and the gate passing.

```python
import sys
sys.path.insert(0, "automation")
import review_receipt as rr
import check_action_projection as cap
from markdown_semantics import rendered_human_text

REV = "a" * 40
PATH = "tasks/1_in-progress/2026-08-04-x/verification.md"

DECOY = (
    "# V\n\n"
    "## Panel round one\n\n"
    "- core-fit / dana: approved — round one, superseded\n\n"
    "## Review verdicts\n\n"
    "**Reviewed revision:** " + REV + "\n\n"
    "- core-fit / dana: approve — the boundary holds\n"
)

print("=== item 1: decoy above the receipt ===")
counts = cap.task_action_unit_counts(DECOY, PATH, ())
print("  actions reported:", sum(counts.values()))
for excerpt in counts:
    print("   ", repr(excerpt))
blanked = rr.blank_receipt_verdict_tokens(DECOY, PATH, rendered_human_text(DECOY))
for line in blanked.splitlines():
    if "dana" in line:
        print("   line:", repr(line))

print()
print("=== item 2: eight escapes ===")


def doc(body, heading="## Review verdicts"):
    return "# V\n\n" + heading + "\n\n**Reviewed revision:** " + REV + "\n\n" + body


def tally(body):
    parsed = rr.parse_review_receipt(doc(body))
    votes = [entry.verdict for entry in parsed.verdicts]
    return "{0}a/{1}b err={2}".format(
        votes.count("approve"), votes.count("block"), len(parsed.errors)
    )


APPROVE = "- core-fit / a: approve — ok\n"
ESCAPES = [
    "- **core**-**fit** / d: block — dissent",
    "- `core` - `fit` / d: block — dissent",
    "- core -- fit / d: block — dissent",
    "- core...-...fit / d: block — dissent",
    "- core-fit ／ d: block — dissent",
    "- lens core-fit / d: block — dissent",
    "Note: core-fit / d: block — dissent",
    "- xcore-fit / d: block — dissent",
]
for line in ESCAPES:
    print("  {0:14s} {1}".format(tally(APPROVE + line + "\n"), line))

print()
print("=== item 3: verdicts the structural view blanks ===")
HIDDEN = {
    "indented 4": "    - core-fit / d: block — dissent",
    "indented 8": "        - core-fit / d: block — dissent",
    "div block": "<div>\n- core-fit / d: block — dissent\n</div>",
    "inline span": "<span>- core-fit / d: block — dissent</span>",
    "fenced": "```\n- core-fit / d: block — dissent\n```",
    "comment": "<!-- - core-fit / d: block — dissent -->",
}
for name, block in HIDDEN.items():
    print("  {0:14s} {1}".format(tally(APPROVE + block + "\n"), name))
```

## Nineteenth panel repair — blast radius and the backtracking probe

The rejector is now searched rather than anchored, so its false-positive surface had to be
measured against real content, and `.search` changes the scan shape so the cost had to be
measured too. Every tracked Markdown file is parsed, and every tracked task record is run
through the action gate. The script is `tmp/blast_radius.py`.

```
$ python3 tmp/blast_radius.py
  refused: tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/verification.md
      tasks/0_backlog/2026-08-07-migrate-the-review-verdicts-heading/verification.md:17: Review verdicts needs exactly one real `**Reviewed revision:** <com
  refused: tasks/1_in-progress/2026-08-02-reconcile-the-contracts-with-the-code/verification.md
      tasks/1_in-progress/2026-08-02-reconcile-the-contracts-with-the-code/verification.md:288: Review verdicts needs exactly one real `**Reviewed revision:
  receipt accepted: tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md 3 verdict(s)
  receipt accepted: tasks/4_done/2026-07-22-protect-core-portability/verification.md 3 verdict(s)
  refused: templates/task/verification.md
      templates/task/verification.md:17: Review verdicts needs exactly one real `**Reviewed revision:** <commit>` field, as the first line of the receipt
tracked markdown files: 645 | receipts accepted: 2 | refused past the heading: 3
unprojected actions over every tracked task record: 18

backtracking probe (seconds per call, 200k-character lines):
  punctuation run      0.0021
  no slash after fit   0.0020
  many core prefixes   0.0046
  core fit no slash    0.0055
  slash far away       0.0019
```

Zero blast radius. All three refusals are the unfilled-placeholder case — a section whose
revision field is still `<full immutable commit ID …>` — which behaved the same before.
Both real receipts still parse, including the 2026-07-22 historical one. The action-gate
total is 18, identical to `6d84769`:

```
$ git checkout 6d84769 -- automation/review_receipt.py && python3 -c 'import subprocess, sys; sys.path.insert(0, "automation"); from pathlib import Path; import check_action_projection as cap; tracked = subprocess.run(["git","ls-files","tasks/*.md"], capture_output=True, text=True, check=True).stdout.split(); print("6d84769 unprojected actions over every tracked task record:", sum(sum(cap.task_action_unit_counts(Path(p).read_text(encoding="utf-8"), p, ()).values()) for p in tracked))'
6d84769 unprojected actions over every tracked task record: 18
```

Nothing exceeds six milliseconds on a 200,000-character line, because both runs inside the
rejector are bounded to sixteen characters.

## Nineteenth panel repair — the new regressions fail at 6d84769

```
$ git checkout 6d84769 -- automation/review_receipt.py
$ python3 -m unittest <the five tests below>
ERROR: test_placement_needs_the_whole_prefix_and_a_token_boundary (automation.tests.test_check_action_projection.ActionProjectionTests)
FAIL: test_decoration_anywhere_in_the_line_is_still_refused (case='- **core**-**fit** / dissenter: block — a concrete bypass')
FAIL: test_decoration_anywhere_in_the_line_is_still_refused (case='- `core` - `fit` / dissenter: block — a concrete bypass')
FAIL: test_decoration_anywhere_in_the_line_is_still_refused (case='- core -- fit / dissenter: block — a concrete bypass')
FAIL: test_decoration_anywhere_in_the_line_is_still_refused (case='- core...-...fit / dissenter: block — a concrete bypass')
FAIL: test_decoration_anywhere_in_the_line_is_still_refused (case='- core-fit ／ dissenter: block — a concrete bypass')
FAIL: test_decoration_anywhere_in_the_line_is_still_refused (case='- lens core-fit / dissenter: block — a concrete bypass')
FAIL: test_decoration_anywhere_in_the_line_is_still_refused (case='Note: core-fit / dissenter: block — a concrete bypass')
FAIL: test_decoration_anywhere_in_the_line_is_still_refused (case='- xcore-fit / dissenter: block — a concrete bypass')
FAIL: test_a_verdict_the_structural_view_drops_is_refused_not_skipped (case='indented four spaces')
FAIL: test_a_verdict_the_structural_view_drops_is_refused_not_skipped (case='indented eight spaces')
FAIL: test_a_verdict_the_structural_view_drops_is_refused_not_skipped (case='div block')
FAIL: test_a_verdict_the_structural_view_drops_is_refused_not_skipped (case='inline span')
FAIL: test_a_verdict_the_structural_view_drops_is_refused_not_skipped (case='fenced')
FAIL: test_a_verdict_the_structural_view_drops_is_refused_not_skipped (case='html comment')
FAIL: test_a_lookalike_above_the_receipt_cannot_steal_the_blanking (automation.tests.test_check_action_projection.ActionProjectionTests)
Ran 5 tests in 0.057s

FAILED (failures=15, errors=1)
```

The subtest labels are shortened here to fit; the runner prints each with its full class
path. `test_a_refused_heading_quotes_the_spelling_it_found` passes at `6d84769` and is not
listed: it is mutation coverage for a branch that already existed, not repair evidence.

## Nineteenth panel repair — focused regressions at HEAD

```
$ python3 -m unittest \
    automation.tests.test_check_core_scope.CoreScopeTests.test_decoration_anywhere_in_the_line_is_still_refused \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_verdict_the_structural_view_drops_is_refused_not_skipped \
    automation.tests.test_check_core_scope.CoreScopeTests.test_a_refused_heading_quotes_the_spelling_it_found \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_a_lookalike_above_the_receipt_cannot_steal_the_blanking \
    automation.tests.test_check_action_projection.ActionProjectionTests.test_placement_needs_the_whole_prefix_and_a_token_boundary
.....
----------------------------------------------------------------------
Ran 5 tests in 0.081s

OK
```

## Nineteenth panel repair — filled template, full suite, reconciler

```
$ python3 tmp/filled_template.py
--- verdict token 'approve': 0 unprojected action(s) ---
--- verdict token 'block': 0 unprojected action(s) ---
```

```
$ python3 automation/run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 15/15 files passed
test elapsed: 45.86s
```

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```
