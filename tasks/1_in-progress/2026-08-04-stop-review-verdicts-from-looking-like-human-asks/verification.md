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
