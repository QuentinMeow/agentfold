# Verification — let a handover project a queue field that contains an inline code span

**Verified:** 2026-07-25 by claude

Only commands actually run and their real output.

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
exit=0
```

## Repository tests

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 10/10 files passed
```

```
$ python3 automation/tests/test_reconcile_queue.py
Ran 283 tests in 125.718s
OK
```

## New regression tests against the repaired checker

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_strict_handover_projects_backticked_context_field [... six tests ...] -v
test_strict_handover_projects_backticked_context_field ... ok
test_strict_handover_projects_rendered_code_span_context ... ok
test_strict_handover_rejects_context_copying_neither_spelling ... ok
test_strict_handover_context_without_code_span_is_unchanged ... ok
test_strict_handover_projects_code_spanned_human_item_at_all ... ok
test_strict_handover_rejects_agent_entry_carrying_code_span ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.100s

OK
```

## The same tests against the pre-fix checker

Run from a detached worktree at `0456738`, the commit before the repair, with only
the new test file copied in.

```
$ python3 -m unittest [... the same six tests ...] -v
test_strict_handover_projects_backticked_context_field ... FAIL
test_strict_handover_projects_rendered_code_span_context ... FAIL
test_strict_handover_rejects_context_copying_neither_spelling ... ok
test_strict_handover_context_without_code_span_is_unchanged ... ok
test_strict_handover_projects_code_spanned_human_item_at_all ... FAIL
test_strict_handover_rejects_agent_entry_carrying_code_span ... FAIL

----------------------------------------------------------------------
Ran 6 tests in 0.103s

FAILED (failures=4)
```

The three code-span projection tests fail before the repair, which is the defect. The
agent-entry test fails before the repair, which is the hole Ruling 2 closes. The two
rejection tests pass on both sides, which is the evidence that nothing was weakened.

## Measurement behind Ruling 2 — the unguarded `needs-agent` tightening

The repair was applied with no `actor` guard and then measured against the pre-fix
checker on every path the checks actually evaluate.

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
exit=0

$ python3 automation/reconcile/reconcile.py --check \
    --branch task/2026-07-25-fix-handover-projection-code-span-copy \
    --range 0456738d3d9f6e45532c32b71f6441e1e3f0551c...6d4e337c3c3b3b795f4de6486198791023be7e83
reconcile: 0 finding(s)
exit=0

$ python3 automation/reconcile/reconcile.py --check --at-transition merge \
    --branch task/2026-07-25-fix-handover-projection-code-span-copy \
    --range 0456738d3d9f6e45532c32b71f6441e1e3f0551c...6d4e337c3c3b3b795f4de6486198791023be7e83
reconcile: 0 finding(s)
exit=0
```

The maximal sweep over the whole recorded history was run twice, once with the repaired
checker at the fix commit and once with the pre-fix checker in a detached worktree at
`0456738`, and the two finding sets were compared.

```
$ python3 automation/reconcile/reconcile.py --check --branch main \
    --range root:0456738d3d9f6e45532c32b71f6441e1e3f0551c
reconcile: 55 finding(s)

$ python3 automation/reconcile/reconcile.py --check \
    --branch task/2026-07-25-fix-handover-projection-code-span-copy \
    --range root:6d4e337c3c3b3b795f4de6486198791023be7e83
reconcile: 55 finding(s)

$ comm -13 control.txt withfix.txt   # findings the repair introduced
$ comm -23 control.txt withfix.txt   # findings the repair removed
control=      55  withfix=      55
```

Both diffs are empty: the 55 findings are identical before and after, all of them
pre-existing legacy-history findings under `task-admission` and `queue-resolution` that
this repair does not touch. Zero new findings on every path, so the measurement selected
the unguarded branch and the `needs-agent` tightening was taken.

The one committed handover entry that carries a code span in a projected section was
also measured directly.

```
$ python3 - (compare old and new prose views on
    history/conversations/2026-07-25-0749PDT-reconcile-post-merge-branches/handover.md)
OLD form1 residue: '-'
NEW form1 residue: '-'
OLD form2 residue: '-'
NEW form2 residue: '-'
verdict unchanged: True
```

## Evidence that the earlier diagnosis was wrong

Measured on the live blocking item's fields, before any change, showing that both
tuple elements blank code spans and that accepting either instead of both is a no-op.

```
$ python3 - (simulate the comparison on the live item)
form1 raw-semantic: matches=False
form2 rendered: matches=False

current semantics (require BOTH): False
proposed fix   (accept EITHER)  : False

form1 == form2 : True
```
