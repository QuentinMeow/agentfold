# Verification — Stop indented prose from hiding from every repository check

**Verified:** 2026-08-02 by claude (session 2026-08-02, branch
`task/2026-08-02-stop-indented-prose-from-hiding-from-the-checks`)

Only commands actually run and their real output. Every "before" transcript was produced
by restoring the two changed source files from
`7a2da6a4cfbfde0c771ef656092f2554f46e071e` — the branch point, and still an ancestor of
this branch after a later rebase, which did not touch either file — then running, then
restoring them again from `HEAD`. Both halves therefore ran against the same records, the
same tests, and the same scratch scripts. The three scripts under
`tmp/indented-prose/` are git-ignored scratch; each one derives the repository root from
its own location, so a reader can drop them anywhere in a checkout and re-run every
transcript below.

## The smallest reproduction, before and after

```
$ git checkout 7a2da6a -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 -c "
import sys; sys.path.insert(0,'automation')
from markdown_semantics import semantic_text
print(repr(semantic_text('- a\n    b\n')))"
'- a\n\n'

$ git checkout HEAD -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 -c "
import sys; sys.path.insert(0,'automation')
from markdown_semantics import semantic_text
print(repr(semantic_text('- a\n    b\n')))"
'- a\n    b\n'
```

## Reproductions one and two, directly

`tmp/indented-prose/reproductions.py` builds one live agent request whose ask is a
four-space continuation under a list item, replaces that ask outright, and asks the queue
checks about it; then it writes one human ask into a task record twice, nested and at top
level, and asks the projection gate to count it.

```
$ git checkout 7a2da6a -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 tmp/indented-prose/reproductions.py
identity equal (nested): True
mutation problem (nested): None
identity equal (top level): False
mutation problem (top level): action identity changed while the queue item remained live
units nested: Counter()
units top: Counter({'Please confirm the retention window before this lands.': 1})

$ git checkout HEAD -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 tmp/indented-prose/reproductions.py
identity equal (nested): False
mutation problem (nested): action identity changed while the queue item remained live
identity equal (top level): False
mutation problem (top level): action identity changed while the queue item remained live
units nested: Counter({'- The window matters: Please confirm the retention window before this lands.': 1})
units top: Counter({'Please confirm the retention window before this lands.': 1})
```

The top-level half is unchanged in both runs, which is what makes each pair a
demonstration: the same bytes were already caught at the margin and only escaped one level
into a list.

## All three reproductions, as tests

`automation/tests/test_markdown_semantics.py` carries every case above plus the
`link-check` one, which needs a repository fixture rather than a bare function call.

```
$ git checkout 7a2da6a -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 automation/tests/test_markdown_semantics.py
FAIL: test_a_four_space_line_cannot_interrupt_a_paragraph (__main__.IndentedCodeViewTests)
FAIL: test_a_four_space_line_under_a_list_item_is_prose (__main__.IndentedCodeViewTests)
FAIL: test_a_four_space_line_under_a_list_item_is_prose_after_a_blank_line (__main__.IndentedCodeViewTests)
FAIL: test_a_lazy_continuation_keeps_its_list_item_open (__main__.IndentedCodeViewTests)
FAIL: test_a_list_item_moves_the_threshold_to_its_content_column (__main__.IndentedCodeViewTests)
FAIL: test_a_nested_list_item_moves_the_threshold_again (__main__.IndentedCodeViewTests)
FAIL: test_a_new_sibling_item_reopens_the_same_threshold (__main__.IndentedCodeViewTests)
FAIL: test_a_quoted_paragraph_lazily_continues_into_the_next_line (__main__.IndentedCodeViewTests)
FAIL: test_a_table_row_is_paragraph_text (__main__.IndentedCodeViewTests)
FAIL: test_an_empty_list_item_still_opens_a_content_column (__main__.IndentedCodeViewTests)
FAIL: test_an_ordered_item_moves_the_threshold_to_its_own_content_column (__main__.IndentedCodeViewTests)
FAIL: test_indentation_width_is_shared_with_the_projection_gate (__main__.IndentedCodeViewTests)
FAIL: test_a_broken_link_inside_a_list_continuation_is_reported (__main__.LinkCheckTests)
FAIL: test_replacing_an_ask_inside_a_list_continuation_is_refused (__main__.QueueMutationTests)
FAIL: test_human_attention_above_fold_reads_a_list_continuation (__main__.SemanticConsumerTests)
FAIL: test_human_header_block_reads_a_list_continuation (__main__.SemanticConsumerTests)
FAIL: test_level_two_section_body_reads_a_list_continuation (__main__.SemanticConsumerTests)
FAIL: test_section_body_reads_a_list_continuation (__main__.SemanticConsumerTests)
FAIL: test_task_status_references_reads_a_list_continuation (__main__.SemanticConsumerTests)
FAIL: test_task_tokens_reads_a_list_continuation (__main__.SemanticConsumerTests)
FAIL: test_an_ask_inside_a_list_continuation_is_counted (__main__.TaskActionOriginTests)
Ran 40 tests in 0.092s
FAILED (failures=21)

$ git checkout HEAD -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 automation/tests/test_markdown_semantics.py
----------------------------------------------------------------------
Ran 40 tests in 0.074s

OK
```

The nineteen tests that pass in both halves are the top-level twins and the
still-blanked-code cases; the twenty-one failures above are exactly what this change
repairs.

## Every named consumer, before and after

`tmp/indented-prose/consumers.py` puts a `task:` token, a task path, and a sentence into
four-space continuations under list items in one human item, then asks each named reader.

```
$ git checkout 7a2da6a -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 tmp/indented-prose/consumers.py
task_tokens: set()
task_status_references: []
header_block: '\n\n**Status:** waiting\n\n- The blocked work is:\n\n\n\n'
above_fold has purge: False
section_body: '- The window matters because:'
level_two: '- The window matters because:\n\n\n**Your answer:** ______'
field_counts: {'Status': 1, 'Your answer': 1}
field_counts indented dup: {'Status': 1}

$ git checkout HEAD -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 tmp/indented-prose/consumers.py
task_tokens: {'2026-08-02-example'}
task_status_references: ['tasks/1_in-progress/2026-08-02-example/task.md']
header_block: '\n\n**Status:** waiting\n\n- The blocked work is:\n    task:2026-08-02-example, recorded in\n    tasks/1_in-progress/2026-08-02-example/task.md\n\n'
above_fold has purge: True
section_body: '- The window matters because:\n    Nothing purges the audit log today.'
level_two: '- The window matters because:\n    Nothing purges the audit log today.\n\n**Your answer:** ______'
field_counts: {'Status': 1, 'Your answer': 1}
field_counts indented dup: {'Status': 1}
```

Six of the seven named consumers change. `field_counts` is identical in both halves, and
that is the correct result rather than a gap: its `FIELD_RE` is anchored at column zero, so
a field written on an indented line was never counted before the change either, and no
line this function ever blanked could have matched. The test
`test_field_counts_never_depended_on_this_view` pins that so the next reader does not have
to re-derive it.

## The legitimate indented-code cases still hold

```
$ python3 -m unittest test_reconcile_queue.ReconcileQueueTests.test_semantic_text_blanks_indented_code_lines \
    test_reconcile_queue.ReconcileQueueTests.test_link_check_ignores_a_path_inside_an_indented_code_block \
    test_reconcile_queue.ReconcileQueueTests.test_semantic_text_still_blanks_a_fence_nested_in_a_list_item \
    test_reconcile_queue.ReconcileQueueTests.test_link_check_still_catches_a_broken_link_fenced_inside_a_list_item -v
test_semantic_text_blanks_indented_code_lines (test_reconcile_queue.ReconcileQueueTests) ... ok
test_link_check_ignores_a_path_inside_an_indented_code_block (test_reconcile_queue.ReconcileQueueTests) ... ok
test_semantic_text_still_blanks_a_fence_nested_in_a_list_item (test_reconcile_queue.ReconcileQueueTests) ... ok
test_link_check_still_catches_a_broken_link_fenced_inside_a_list_item (test_reconcile_queue.ReconcileQueueTests)
Fenced blocks nested in list items must stay blanked: the new indented- ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.019s

OK
```

All four passed unmodified. The only edit to that file is five added lines in one other
fixture:

```
$ git diff 7a2da6a HEAD --stat -- automation/tests/test_reconcile_queue.py
 automation/tests/test_reconcile_queue.py | 5 +++++
 1 file changed, 5 insertions(+)
```

`test_handover_ignores_commented_and_fenced_fake_links` listed a four-space link straight
after a line of prose among its hidden links. Under CommonMark that is a paragraph
continuation a human reads, not a code block, so the fixture now separates it with a blank
line — which is what makes it code — plus a comment saying why. Its assertion is unchanged.

## Whole-tree reconciler, before and after

```
$ git checkout 7a2da6a -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
exit=0

$ git checkout HEAD -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
exit=0
```

Run once more with advisory findings promoted to failures, so nothing was counted
separately and then ignored. Both halves reported the same:

```
$ python3 automation/reconcile/reconcile.py --check --fail-on-advisory
reconcile: 0 blocking finding(s)
exit=0
```

The narrower rule surfaces no finding on any existing file in the repository.

## CommonMark case matrix

`tmp/indented-prose/cases.py` holds thirty hand-computed cases — top-level code, code under
a bullet, ordered and nested items, empty items, thematic breaks, setext underlines, lazy
continuations, block quotes, table rows, fences — each naming the tokens that must survive
and the tokens that must be blanked, and each also asserting the line count is unchanged.

```
$ git checkout 7a2da6a -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 tmp/indented-prose/cases.py
FAIL keep 'KEEP' in '- [ ] criterion text\n      KEEP continuation\n' -> '- [ ] criterion text\n\n'
FAIL keep 'KEEP' in '-\n\n    KEEP\n' -> '-\n\n\n'
failures: 13 of 30 cases

$ git checkout HEAD -- automation/markdown_semantics.py automation/check_action_projection.py
$ python3 tmp/indented-prose/cases.py
failures: 0 of 30 cases
```

Two disagreements between the matrix and the first draft of the rule were found this way.
One was a bug — a thematic break was not closing the list above it, so a code block after
`- a` / `- - -` stayed visible — and the walk now matches containers on every block start.
The other was a wrong expectation: six spaces under `- [ ] x` after a blank line really is
an indented code block, because the item's content column is two. Every case in the matrix
that distinguishes the old rule from the new one is also a named test in
`automation/tests/test_markdown_semantics.py`, whose run is recorded above.

## Full test suite

```
$ python3 automation/run_tests.py
PASS automation/tests/test_probe.py
tests: 1/1 files passed
test elapsed: 0.01s
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_markdown_semantics.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 13/13 files passed
test elapsed: 116.18s
```

## Input-ownership table

```
$ python3 -m unittest test_run_tests.InputOwnershipTests -v
test_every_declared_repository_read_is_owned_by_the_reader (test_run_tests.InputOwnershipTests) ... ok
test_every_runner_attribute_this_file_names_actually_exists (test_run_tests.InputOwnershipTests)
Catch a rename whose only surviving caller sits behind an env-gated test. ... ok
test_ownership_is_closed_under_module_imports (test_run_tests.InputOwnershipTests) ... ok
test_pruning_removes_record_paths_and_keeps_test_fixtures (test_run_tests.InputOwnershipTests) ... ok
test_the_whole_suite_passes_against_a_record_free_projection (test_run_tests.InputOwnershipTests)
The expensive half of the inert proof: delete the records, run everything. ... skipped 'set AGENTFOLD_INERT_PROBE=1 to run the whole suite against a record-free projection'

----------------------------------------------------------------------
Ran 5 tests in 2.878s

OK (skipped=1)
```

## Review verdicts (when a review was explicitly run)

No independent review was run. The mode is `async`, this is not a one-way door — the change
is one function whose undo is a revert — and the `async` gate is tests plus the reconciler,
both recorded above.
