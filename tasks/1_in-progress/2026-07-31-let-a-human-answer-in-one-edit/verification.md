# Verification — let a human answer in one edit

Branch task/2026-07-31-let-a-human-answer-in-one-edit, stacked on
task/2026-07-30-clear-the-stuck-queue-items. Every command below was run; every block is
its real output.

Reference commits:

- `c7257e3` — the claim commit, the last state carrying the defects
- `60dc43c` — the fix

## Defect 1 — the documented human-answer workflow could not be committed

### Before

The live review `message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md`
was `waiting` with a bound revision and a blank response. One edit was made to it — the
response blank replaced with a sentence — and staged, which is exactly what the human's
own commit presents to the pre-commit hook.

```
$ python3 automation/reconcile/reconcile.py --check
[queue-schema] message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md: review response is not bound to the requested revision
    fix: copy Review revision into Reviewed revision with the response
[queue-schema] message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md: review response needs an explicit terminal **Review outcome:**
    fix: use approved, changes-requested, rejected, or abandoned (legacy not-approved means changes-requested)
reconcile: 2 blocking finding(s)
```

Adding a backticked path to the same sentence — "Also please mention this in
handbook/guardrail-modes.md when you fold it.", with the filename in backticks as a
human naturally writes it — added the third blocker. The stack's narrowed path detection
does not help: `.md` is a known extension, so any plausible filename the human types is
treated as a repository claim.

```
$ python3 automation/reconcile/reconcile.py --check
[queue-schema] ...: review response is not bound to the requested revision
[queue-schema] ...: review response needs an explicit terminal **Review outcome:**
[link-check] message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md: `handbook/guardrail-modes.md` does not exist
    fix: fix the path, create the target, or unquote if not a path
reconcile: 3 blocking finding(s)
```

### After — the human's commit, through the real pre-commit hook

One edit to the response blank, including the backticked path that does not exist:

```
$ git diff --stat
 .../reviews/non-blocking-review-template-first-explanation.md           | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

$ git commit -m "Answer the template-first explanation review"
pre-commit: core scope
core-scope: no core changes (independent review manual; not invoked)
pre-commit: reconciler
reconcile: 0 blocking finding(s)
...
pre-commit: OK
COMMIT EXIT=0
faaca2a Answer the template-first explanation review
```

### After — the agent's folding claim supplies the binding

```
$ git commit -m "harness: claim and classify the answered template-first review"
agent claim binds: sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f
...
pre-commit: OK
COMMIT EXIT=0
faaaa61 harness: claim and classify the answered template-first review
faaca2a Answer the template-first explanation review
```

The two-commit lifecycle also passes the range admission that CI and merge use:

```
$ python3 automation/reconcile/reconcile.py --check --range 60dc43c0e72e91341fc122610ffda0653db2f3d7...faaaa61c633f75e15d3c93ec1ce173c33f66d324
reconcile: 0 blocking finding(s)
```

These two demonstration commits were reset away afterwards; the live review item is
back to its unanswered state and `git status` is clean at `60dc43c`.

### The binding is still required, and cannot be forged

An agent that claims `folding` without classifying the response is rejected:

```
$ python3 automation/reconcile/reconcile.py --check
[queue-schema] ...: review response is not bound to the requested revision
    fix: copy Review revision into Reviewed revision with the folding claim
[queue-schema] ...: review response needs an explicit terminal **Review outcome:**
    fix: use approved, changes-requested, rejected, or abandoned (legacy not-approved means changes-requested)
[queue-resolution] ...: live queue action was rewritten: the waiting -> folding claim changed more than status
reconcile: 3 blocking finding(s)
```

An agent that writes the response *and* approves it in one commit is rejected by the
hook itself, and the commit does not land:

```
$ git commit -m "forge an approval in one commit"
pre-commit: core scope
core-scope: no core changes (independent review manual; not invoked)
pre-commit: reconciler
[queue-resolution] message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md: live queue action was rewritten: the waiting -> folding claim changed more than status
    fix: preserve the action and response identity; file a distinct successor action when the requested work changes
reconcile: 1 blocking finding(s)

$ git log --oneline -1
60dc43c Let a human answer a queue item in one edit
```

## Defect 2 — no queue template was copy-and-fill valid

Each template was copied to its endpoint, every `<placeholder>` replaced with a
plausible value of the documented form, and the whole reconciler run against the result —
one template at a time. The filling rule is `fill_queue_template` from
`automation/tests/test_reconcile_queue.py`, so this proves exactly what the regression
test enforces.

### Before (`c7257e3`)

```
templates/queue/clarification.md @ c7257e3
  [queue-schema] .../non-blocking-copy-and-fill.md: missing required field **If unanswered:** for non-blocking-*
  [queue-schema] .../non-blocking-copy-and-fill.md: **Status:** must be one of: folding, waiting
  reconcile: 2 blocking finding(s)
templates/queue/decision.md @ c7257e3
  [queue-schema] .../non-blocking-copy-and-fill.md: missing required field **If unanswered:** for non-blocking-*
  [queue-schema] .../non-blocking-copy-and-fill.md: **Status:** must be one of: folding, waiting
  reconcile: 2 blocking finding(s)
templates/queue/request.md @ c7257e3
  [queue-schema] .../non-blocking-copy-and-fill.md: missing required field **If unanswered:** for non-blocking-*
  [queue-schema] .../non-blocking-copy-and-fill.md: **Status:** must be one of: in-repair, open
  reconcile: 2 blocking finding(s)
templates/queue/retry.md @ c7257e3
  [queue-schema] .../non-blocking-copy-and-fill.md: missing required field **If unanswered:** for non-blocking-*
  [queue-schema] .../non-blocking-copy-and-fill.md: **Status:** must be one of: in-repair, open
  reconcile: 2 blocking finding(s)
templates/queue/review.md @ c7257e3
  [queue-schema] .../non-blocking-copy-and-fill.md: missing required field **If unanswered:** for non-blocking-*
  [queue-schema] .../non-blocking-copy-and-fill.md: **Status:** must be one of: awaiting-artifact, folding, waiting
  [queue-schema] .../non-blocking-copy-and-fill.md: **Review target:** must identify exactly one file, Git range, or HTTPS artifact
  [queue-schema] .../non-blocking-copy-and-fill.md: **Review revision:** is not an immutable sha256 or Git revision
  [queue-schema] .../non-blocking-copy-and-fill.md: review without a response must keep **Review outcome:** pending
  reconcile: 5 blocking finding(s)
```

Five out of five templates failed, 13 findings in total. The audit predicted the timing
fields; the run also found `**Status:** <waiting | folding>`, which is an angle-bracket
placeholder and never one of the allowed statuses.

### After

```
templates/queue/clarification.md @ working tree
  reconcile: 0 blocking finding(s)
templates/queue/decision.md @ working tree
  reconcile: 0 blocking finding(s)
templates/queue/request.md @ working tree
  reconcile: 0 blocking finding(s)
templates/queue/retry.md @ working tree
  reconcile: 0 blocking finding(s)
templates/queue/review.md @ working tree
  reconcile: 0 blocking finding(s)
```

Five out of five pass. All five filed together also pass:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Defect 3 — schema fields with no template

`templates/README.md` now carries one table naming each single-instance marker field and
the file that holds it, and `templates/queue/retry.md` says which two fields the
reconciler adds to its own retries. Locations were confirmed against the repository:

```
$ grep -rn --include='*.md' -E '^\*\*(Collaboration mode|Task admission schema|Queue resolution schema|Queue projection schema|Queue action-entry schema|Queue liveness schema|Last-updated):' . | grep -v '/templates/'
AGENTS.md:15:**Collaboration mode:** `async` — see `handbook/collaboration-modes.md` for what each
tasks/AGENTS.md:3:**Task admission schema:** v1
roadmap/desired-state.md:3:**Last-updated:** 2026-07-24
roadmap/current-state.md:3:**Last-updated:** 2026-07-31
docs/designs/layered-development-workspace.md:6:**Last-updated:** 2026-07-24
history/AGENTS.md:3:**Queue projection schema:** v1
history/AGENTS.md:4:**Queue action-entry schema:** v2
history/AGENTS.md:5:**Queue liveness schema:** v1
message-queue/AGENTS.md:3:**Queue resolution schema:** v1
```

## Regression tests

Nine new tests in `automation/tests/test_reconcile_queue.py`:

```
test_human_answers_a_review_in_one_edit
test_a_blank_review_outcome_reads_as_pending
test_the_folding_claim_may_add_the_review_binding
test_an_agent_cannot_classify_a_response_it_wrote_in_the_same_commit
test_the_review_binding_is_write_once_and_claim_edge_only
test_the_binding_cannot_repoint_or_rewrite_the_human_response
test_a_path_in_a_human_response_never_breaks_link_check
test_every_queue_template_survives_copy_and_fill
test_a_queue_template_hiding_a_required_field_in_a_comment_fails
test_schema_marker_fields_are_documented_where_templates_are_indexed
```

`test_review_response_is_bound_to_exact_local_bytes` was updated: it encoded the old
rule, and now asserts that a `waiting` response stands alone while a partial binding is
still rejected.

## Full suite and check

```
$ python3 automation/run_tests.py
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
test elapsed: 33.00s
```

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
CHECK EXIT=0
```

The narrow staged lane also passes, which matters because the queue templates became
registered test inputs and `prune_inert_projection` used to delete them from that lane's
projection:

```
$ python3 automation/run_tests.py --staged
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_run_tests.py
tests: 2/2 files passed
test elapsed: 31.81s
```

No command in this task used `--no-verify` for any commit that was kept.
