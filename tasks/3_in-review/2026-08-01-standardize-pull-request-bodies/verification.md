# Verification — standardize pull-request bodies

## The schema against the boundary check

`automation/tests/test_pull_request_schema.py` builds bodies in the schema's exact shape
and asserts what `automation/check_action_projection.py` says about them.

```
$ python3 -m unittest automation.tests.test_pull_request_schema
..........
----------------------------------------------------------------------
Ran 10 tests in 0.799s

OK
```

The ten cases, and what each one holds:

| Test | Holds |
|---|---|
| `test_schema_shaped_body_with_a_ranked_action_list_passes` | a filled body in this exact shape is accepted, indented context included |
| `test_the_stack_note_alert_does_not_look_like_an_unqueued_ask` | a top-level `> [!NOTE]` stack banner does not read as an ask |
| `test_absolute_commit_pinned_links_are_accepted` | the link form GitHub renders is the form the check accepts |
| `test_no_action_acknowledgement_is_accepted_when_nothing_is_live` | the empty case passes as written |
| `test_claiming_no_action_while_one_is_live_is_refused` | an author cannot declare an empty queue that is not empty |
| `test_omitting_a_live_action_is_refused` | a body cannot quietly drop an item its task still owes |
| `test_an_unfilled_template_fails_closed` | submitting the skeleton unchanged is refused |
| `test_permission_phrasing_outside_the_action_section_is_refused` | "can now merge" fails; the indicative repair passes |
| `test_an_ask_outside_the_action_section_is_refused` | a question inside a fold is refused |
| `test_the_schema_and_its_github_adapter_both_exist_and_agree` | both files carry the same sections in the same order, with no alert after the first fold |

## Three defects the tests found in the first draft

These are recorded because they are the reason the tests exist, not to claim credit for
fixing them. Details are in `design.md`.

1. A `<details>` block with no heading above it was parsed as part of `What to review`, so
   the whole folded half of the body was rejected.
2. A GitHub alert inside `<details>` renders as literal `[!NOTE]` text.
3. "A branch that filed its own review can now merge" is refused by the boundary check as a
   directive outside the action section.

## Full suite

```
$ python3 automation/run_tests.py
...
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 12/12 files passed
test elapsed: 36.64s
```

`test_run_tests.py` failed on the first attempt with
`test_pull_request_schema.py reads .github/pull_request_template.md, which the ownership
table does not give it`. That is the repository's own rule that a new tracked input
registers its owning tests; the table in `automation/run_tests.py` now names both the
schema and its adapter, and the suite passes.

## Repository invariants

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```
