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

## The blocked handover, end to end on the real artifact

The blocked session's handover was committed at a fresh conversation path. Its second
`Needs your attention` entry copies the code-spanned fields of the live decision item, which
is the case that was impossible before the repair.

```
$ git add history/conversations/2026-07-25-1140PDT-fold-edge-graph-decisions-and-ship-stage-0/handover.md
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
exit=0
```

The identical file staged against the pre-fix checker, in a detached worktree at `0456738`,
fails with exactly the finding this task repairs.

```
$ git add history/conversations/2026-07-25-1140PDT-fold-edge-graph-decisions-and-ship-stage-0/handover.md
$ python3 automation/reconcile/reconcile.py --check
[handover-queue-projection] history/conversations/2026-07-25-1140PDT-fold-edge-graph-decisions-and-ship-stage-0/handover.md: Needs your attention entry 2 must copy the creation-snapshot Why-you-might-care and If-you-do-nothing fields using the fixed handover suffix
    fix: use one top-level list entry per live human action; put an exact Action-labeled queue link first and keep context declarative
reconcile: 1 finding(s)
exit=1
```

Entry 2 is the code-spanned item and the only entry that differs, so the repair is what
made the handover committable. No `--no-verify` bypass was used at any point.

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

## Pull-request body projection

```
$ python3 automation/check_action_projection.py --from-env ACTION_PROJECTION_BODY \
    --additional-summary-env ACTION_PROJECTION_TITLE --action-section "What to review" \
    --queue-actor any --required-queue-actor needs-human \
    --branch task/2026-07-25-fix-handover-projection-code-span-copy \
    --base-revision <origin/main> --candidate-revision <branch head> \
    --label github-pull-request-description
action-projection: 0 finding(s)
exit=0
```

## Pull request 14 checks

Both admission jobs failed on the `opened` event against the already-filed
`merge_commit_sha` race, then passed once an `edited` event recomputed the candidate.

```
$ gh pr checks 14
Authoritative action projection from trusted workflow code   pass   10s
Current review-state action projection                        pass    6s
External source release admission                             pass    9s
reconcile-and-test                                            pass   39s
```
