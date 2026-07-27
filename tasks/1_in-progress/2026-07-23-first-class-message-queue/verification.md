# Verification — Make the message queue the first-class interaction surface

**Verified:** 2026-07-23 by codex

Only commands actually run and their real output are recorded here.

## Full repository test runner

```
$ python3 automation/run_tests.py
Ran 118 tests in 41.845s
OK
Ran 55 tests in 2.329s
OK (skipped=1)
Ran 24 tests in 0.019s
OK
Ran 9 tests in 0.022s
OK
Ran 259 tests in 152.212s
OK
Ran 9 tests in 0.004s
OK
Ran 5 tests in 0.202s
OK
Ran 3 tests in 0.490s
OK
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 8/8 files passed
```

## Final queue regression suite

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 260 tests in 150.468s
OK
```

## Latest-main ancestry

```
$ git rev-parse main origin/main
acc23b6289f5ca66744718af379aba0468be93e2
acc23b6289f5ca66744718af379aba0468be93e2
$ git merge-base --is-ancestor 999a6c4 origin/main
$ git merge-base --is-ancestor 9e24478 origin/main
```

Both ancestry commands exited 0. These are the merged heads of PRs #4 and #6.

## Staged repository admission

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## 2026-07-26 Action parser hardening

Focused parser and presentation coverage passed 11 tests in 1.036 seconds. The full
action-projection suite passed 118 tests in 24.970 seconds, and the complete queue suite
passed 384 tests in 193.670 seconds.

```
$ python3 automation/run_tests.py
tests: 11/11 files passed
$ GIT_INDEX_FILE=<temporary-index> python3 automation/check_core_scope.py --staged
core-scope: pass (2 core path(s), task 2026-07-23-first-class-message-queue; independent review manual; not invoked)
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

`python3 -m py_compile automation/reconcile/reconcile.py
automation/tests/test_reconcile_queue.py` and `git diff --check` both exited 0 without
output. The temporary index contained the four modified paths and did not change the
real staging area.

The rebuilt immutable candidate ran the exact pre-commit gate:

```
commit a641dd888524ebb0c5ff462dba156b49cd907206
Ran 384 tests in 277.465s
OK
tests: 11/11 files passed
pre-commit: OK
```

All three fresh first-wave lenses blocked that exact revision. Reproductions showed a
padded backward rollback that hid an invalid earlier lifecycle or schema-dependency
edge, a second visible Action disguised by non-`Cf` default-ignorable characters,
contradictory visible content in an extra disclosure block, and quadratic ordinary-link
resolution. No panel approval is claimed for `a641dd8`.

## Review status

The implementation has undergone repeated independent adversarial audits, and every
finding implemented in this review round has a regression test. Per the owner's stop
boundary, a fresh final immutable-revision panel is intentionally deferred until after
the first human review; no final-pass verdict is claimed here.

## 2026-07-24 derived-assurance revision

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

The final queue-publication commit ran the repository pre-commit suite:

```
Ran 118 tests in 19.269s
OK
Ran 55 tests in 0.857s
OK (skipped=1)
Ran 24 tests in 0.012s
OK
Ran 9 tests in 0.011s
OK
Ran 262 tests in 67.384s
OK
Ran 9 tests in 0.004s
OK
Ran 5 tests in 0.094s
OK
Ran 3 tests in 0.234s
OK
tests: 8/8 files passed
pre-commit: OK
```

## 2026-07-24 stacked-publication checkpoint

```
$ git rev-parse task/2026-07-23-first-class-message-queue
c05e8002e495e4ee346e685213c48f8d6632fa85
```

The coordination lane recorded `c05e8002e495e4ee346e685213c48f8d6632fa85`
as the published PR #7 head before the ancestry join. No final merge-panel verdict was
claimed by that coordination checkpoint.

## 2026-07-26 action-first human review repair

Focused presentation, migration, timing, and lifecycle regressions:

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_valid_human_presentation_v2_is_self_contained_and_parseable automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_presentation_v2_uses_each_items_delivery_class automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_presentation_v2_requires_blank_line_after_tracking_summary automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_presentation_v2_notice_matches_lifecycle_status automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_presentation_v2_rejects_ambiguous_or_asymmetric_content automation.tests.test_reconcile_queue.ReconcileQueueTests.test_v2_activation_migrates_only_unanswered_waiting_action_identity automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_presentation_v2_is_sticky_after_activation automation.tests.test_reconcile_queue.ReconcileQueueTests.test_awaiting_review_v2_exposes_no_premature_response_prompt
Ran 8 tests in 2.405s
OK
```

Legacy artifact-publication compatibility and lifecycle regressions:

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_legacy_awaiting_review_adopts_v2_only_when_published automation.tests.test_reconcile_queue.ReconcileQueueTests.test_v2_activation_migrates_only_unanswered_waiting_action_identity automation.tests.test_reconcile_queue.ReconcileQueueTests.test_review_binding_is_published_by_awaiting_to_waiting_transition automation.tests.test_reconcile_queue.ReconcileQueueTests.test_valid_human_presentation_v2_is_self_contained_and_parseable automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_presentation_v2_rejects_ambiguous_or_asymmetric_content
Ran 5 tests in 2.093s
OK
```

Complete repository runner before the immutable review commit:

```
$ python3 automation/run_tests.py
Ran 118 tests in 53.425s
OK
Ran 55 tests in 2.303s
OK (skipped=1)
Ran 24 tests in 0.017s
OK
Ran 9 tests in 0.017s
OK
Ran 40 tests in 15.715s
OK (skipped=1)
Ran 28 tests in 10.372s
OK
Ran 309 tests in 227.912s
OK
Ran 9 tests in 0.003s
OK
Ran 19 tests in 1.863s
OK
Ran 5 tests in 0.148s
OK
Ran 3 tests in 0.363s
OK
tests: 11/11 files passed
```

Exact staged consistency check:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

The complete queue suite was repeated against the final staged contents before
candidate publication:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 321 tests in 120.547s
OK
```

The fourth immutable candidate ran the exact pre-commit gate:

```
commit 850c48c7b7054ce62b1b1654307afc2d86066882
Ran 321 tests in 225.679s
OK
tests: 11/11 files passed
pre-commit: OK
```

The first three fresh review lenses all blocked that exact revision, so the remaining
two lenses were not treated as approvals and the five-lens cycle restarted. Reproduced
failures were two opaque or biased projected actions, a root-commit direct-to-folding
creation bypass, negated recommendations, an open-ended fourth review disposition,
unverified Git artifact URLs, path-spelled duplicate references, punctuation-changing
handover labels, and rejection of ordinary dotted prose. No approval is claimed for
`850c48c`.

Complete queue suite after the multi-agent repair of those findings:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 326 tests in 129.596s
OK
```

The focused exploit batch, Python compilation, diff check, and direct schema audit of
all six live v2 actions also passed; the schema audit reported `checked=6 problems=0`.

After incorporating the plain-language actions through deterministic activation rules,
the complete queue suite was repeated against the rebuilt atomic candidate:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 327 tests in 126.783s
OK
```

The exact staged reconciler also reported `reconcile: 0 finding(s)`.

The rebuilt immutable candidate ran the exact pre-commit gate:

```
commit 93418015cc04ff0e4f9ecf0dacc3eef0810a3e56
Ran 327 tests in 376.295s
OK
tests: 11/11 files passed
pre-commit: OK
```

The zero-context UX lens approved that exact revision. Lifecycle and parser lenses
blocked it, so the review cycle was not unanimous and the remaining two lenses were
not counted. Reproductions showed a direct-to-folding creation bypass for custom human
kinds, a malformed local-artifact URL crash, quote-adjacent sentence-boundary errors,
and contradictory prose after an exact recommendation. No panel approval is claimed
for `9341801`.

Complete queue suite after repairing that review cycle:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 330 tests in 127.254s
OK
```

Seven focused parser tests, eight focused lifecycle tests, direct exploit probes,
Python compilation, and the diff check also passed. A direct audit of all six live v2
files reported zero presentation problems.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit fcefb5d5a8ed10ecacc1f74ef913c8cbd7e6b64d
Ran 330 tests in 199.381s
OK
tests: 11/11 files passed
pre-commit: OK
```

Its zero-context UX lens approved. The lifecycle and parser lenses blocked, so the
cycle was not unanimous. Reproductions showed that custom v2 kinds could not pass the
generic repeated-option schema, closed review guidance could hide visible fenced or
raw-HTML alternatives, abbreviation and embedded-question sentence cases were
misclassified, and recommendation purity rejected ordinary Markdown wrapping used by
the templates. No panel approval is claimed for `fcefb5d`.

Complete queue suite after repairing that review cycle:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 334 tests in 121.149s
OK
```

Five focused parser tests, twelve focused custom-kind schema/lifecycle tests, template
self-validation, direct exploit probes, Python compilation, and the diff check also
passed. A direct audit of all six live v2 files again reported zero problems.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit 8383317ff27950a76f5675303e3485f12fb5133d
Ran 334 tests in 188.359s
OK
tests: 11/11 files passed
pre-commit: OK
```

Its zero-context UX lens approved. The lifecycle and parser lenses blocked, so the
cycle was not unanimous. Reproductions showed missing decision-style recommendation
enforcement for custom kinds, paragraph-crossing recommendation continuations, a
false rejection of ordinary `U.S. Supreme Court` prose, and missing Unicode/quoted
terminal-punctuation support in handover projection. No panel approval is claimed for
`8383317`.

Complete queue suite after repairing that review cycle:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 336 tests in 123.866s
OK
```

Eight focused parser/handover tests, thirteen focused custom-kind recommendation and
lifecycle tests, direct exploit probes, Python compilation, and the diff check also
passed. The full reconciler reported zero findings; all six live v2 actions passed the
schema audit and terminal-punctuation check.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit e6011fab68ccb017f70efb664b27b8cc89f6bd51
Ran 336 tests in 185.610s
OK
tests: 11/11 files passed
pre-commit: OK
```

Its zero-context UX lens approved. The lifecycle and parser lenses blocked, so the
cycle was not unanimous. Reproductions showed pre-activation in-range response
smuggling, arbitrary rendered prose outside named state fields, an ambiguous acronym
sentence heuristic, and CommonMark reference-style links missing from duplicate
detection. No panel approval is claimed for `e6011fa`.

Complete queue suite after the jointly designed parser and lifecycle repair:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 342 tests
OK
```

The focused human-presentation set passed 10 tests, the strict-handover set passed 18,
and the new paragraph/field/reference matrix passed 4. All live v2 files passed direct
audit; Python compilation, the diff check, and both 60-line contract budgets passed.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit 8bbaff83dcff2f59ca59c35a2ae4165e30f1884e
Ran 342 tests in 362.976s
OK
tests: 11/11 files passed
pre-commit: OK
```

All three first-wave lenses blocked that exact revision. Reproductions covered an
undocumented combined paragraph budget, pre-activation rename-origin response
smuggling, visually blank field values, missed CommonMark autolinks, exact prefix and
handover-copy weakening through compatibility normalization, and Markdown delimiters
counted as rendered length. No panel approval is claimed for `8bbaff8`.

Complete queue suite after repairing that review cycle:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 348 tests in 221.805s
OK
```

The prior human-presentation, compact-paragraph, field-pure, reference, strict-
handover, and lifecycle groups all passed, including 23 focused rename/copy origin
tests. The live audit reported `6 marked, 0 invalid`; reconciliation, compilation,
diff checks, and both 60-line contract budgets passed.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit af607bd711786eb4a897ec9c50990a032b782aaf
Ran 348 tests in 357.039s
OK
tests: 11/11 files passed
pre-commit: OK
```

Its zero-context UX lens approved. Lifecycle and parser lenses blocked, so the cycle
was not unanimous. Reproductions showed a valid angle-bracket inline URL misclassified
as an autolink and an activation-then-whole-service-removal sequence that disabled
selected-range origin scanning and laundered a fabricated response. No panel approval
is claimed for `af607bd`.

Complete queue suite after repairing that review cycle:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 354 tests in 306.647s
OK
```

The focused resolver, human-presentation, handover-v3, and strict-handover groups
passed 37 tests. The live audit reported `6 marked, 0 invalid`; reconciliation,
compilation, diff checks, and both 60-line budgets passed.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit f803f5fa59971eda4294477a0bf93ee22471d7c8
Ran 354 tests in 496.114s
OK
tests: 11/11 files passed
pre-commit: OK
```

Its zero-context UX lens approved. Lifecycle and parser lenses blocked, so the cycle
was not unanimous. Reproductions showed a divergent direct-head range failing to
inherit the trusted base's active v2 provenance rule, and a valid Action with literal
brackets that no required v3 Markdown link label could project exactly. No panel
approval is claimed for `f803f5f`.

Complete queue suite after repairing that review cycle:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 359 tests in 324.400s
OK
```

The action-projection suite passed 118 tests and the focused resolver, presentation,
handover-v3, and strict-handover groups passed 38. The live audit reported `6 marked,
0 invalid`; reconciliation, compilation, diff checks, and both 60-line budgets passed.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit dea25d0ec6d5a0d3ed3f4bb750a11d802954aa14
Ran 359 tests in 501.631s
OK
tests: 11/11 files passed
pre-commit: OK
```

All three first-wave lenses blocked that exact revision. Reproductions covered rendered
label comparison against unrendered inline-code/emphasis Actions, missing v2 governance
from a validated displaced old tip, and quadratic scanning of malformed bracket floods.
No panel approval is claimed for `dea25d0`.

Complete exact-byte repository verification after repairing that review cycle:

```
$ python3 automation/run_tests.py
tests: 11/11 files passed
```

The queue suite passed 367 tests in 254.193 seconds; the action-projection suite passed
118. Reconciliation reported zero findings, the diff check passed, and the history and
handover-template contracts were 59 and 60 lines respectively.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit 60b5cc8395b3e33499855c744911f9d03587df78
Ran 367 tests in 261.763s
OK
tests: 11/11 files passed
pre-commit: OK
```

All three first-wave lenses blocked that exact revision. Reproductions covered a
wrapped canonical Action placeholder that the parser truncated, presentation v2 active
without queue-resolution v1 mutation enforcement, and an Action-looking HTML comment
that skipped safety validation of the real raw Action. No panel approval is claimed
for `60b5cc8`.

Complete exact-byte repository verification after repairing that review cycle:

```
$ python3 automation/run_tests.py
tests: 11/11 files passed
```

The queue suite passed 374 tests in 280.968 seconds; the action-projection suite passed
118. Reconciliation reported zero findings; compilation, diff checks, raw template
shape audits, and the 59/60-line contract budgets passed.

The next rebuilt immutable candidate ran the exact pre-commit gate:

```
commit 411a223c5f77ed76c2cbc6c4f0eb3d5522dd1580
Ran 374 tests in 274.931s
OK
tests: 11/11 files passed
pre-commit: OK
```

Its zero-context UX lens approved. Lifecycle and parser lenses blocked, so the cycle
was not unanimous. Reproductions showed an exact backward rollback range omitting its
candidate head from v2 dependency and lifecycle checks, a zero-width-prefixed visible
duplicate Action, and safe comment text inside inline code removed as an HTML comment.
No panel approval is claimed for `411a223`.

The first immutable repair commit ran the repository gate on its exact bytes:

```
commit 5a6d21a0ffb2eab9139887a12481462cd8a06804
Ran 310 tests in 255.116s
OK
tests: 11/11 files passed
pre-commit: OK
```

That revision was superseded after both completed reviewers blocked it:

- human factors/content design — block: broken click targets, insufficient review
  evidence, assumption-backed approval recommendations, and two future-tense actions;
- lifecycle/admission — block: v2 publication and folding deadlocks, v2 removal and
  restoration across a range, and response-free folding actions hidden by v3.

No approval is claimed for `5a6d21a`.

The second immutable candidate also ran the exact pre-commit gate:

```
commit dc315f788c5fb192f996bd5820271f18f6394087
Ran 314 tests in 164.128s
OK
tests: 11/11 files passed
pre-commit: OK
```

Both reviewers blocked that exact revision:

- human factors/content design — block: two already-merged reviews still described
  pre-merge outcomes and the exact Git ranges were not clickable review artifacts;
- lifecycle/admission — block: a legacy-format item could enter folding with no
  concrete response after presentation v2 activated.

No approval is claimed for `dc315f7`.

Focused regressions after those findings:

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_valid_human_presentation_v2_is_self_contained_and_parseable automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_action_templates_keep_the_notice_adjacent_to_the_action automation.tests.test_reconcile_queue.ReconcileQueueTests.test_awaiting_review_v2_exposes_no_premature_response_prompt automation.tests.test_reconcile_queue.ReconcileQueueTests.test_legacy_folding_action_cannot_hide_a_blank_response_under_v2 automation.tests.test_reconcile_queue.ReconcileQueueTests.test_v2_activation_reframes_a_crossed_merge_review_honestly
Ran 5 tests in 0.121s
OK
```

Complete queue lifecycle and presentation suite after the repair:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 316 tests in 106.425s
OK
```

The third immutable candidate ran the exact pre-commit gate:

```
commit ca50208197a8738ed8634e1815e91edae542130a
Ran 316 tests in 169.026s
OK
tests: 11/11 files passed
pre-commit: OK
```

The five-lens panel blocked that revision. Reproduced failures covered evidence-after-
recommendation anchoring, a biased/opaque action, stale post-merge consequences,
duplicate option identifiers and nonexistent recommendations, direct creation in
folding, wrong-type responses, publication-time scope injection, a provider-dependent
and range-only Git link rule, doubled handover punctuation, and unsafe crossed-review
identity rewrites. No approval is claimed for `ca50208`.

Focused regressions for the panel findings:

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_v2_activation_crossed_merge_reframe_is_ancestry_bound_and_exact automation.tests.test_reconcile_queue.ReconcileQueueTests.test_v2_activation_neutralizes_only_three_legacy_confirm_grammars automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_v2_activation_rejects_new_folding_human_action automation.tests.test_reconcile_queue.ReconcileQueueTests.test_range_rejects_new_folding_review_but_grandfathers_pre_v2_item automation.tests.test_reconcile_queue.ReconcileQueueTests.test_range_rejects_wrong_response_field_before_folding_claim automation.tests.test_reconcile_queue.ReconcileQueueTests.test_handover_v3_does_not_double_punctuate_action_label automation.tests.test_reconcile_queue.ReconcileQueueTests.test_awaiting_review_v2_exposes_no_premature_response_prompt automation.tests.test_reconcile_queue.ReconcileQueueTests.test_human_presentation_v2_rejects_ambiguous_or_asymmetric_content
Ran 8 tests in 2.793s
OK
```

Complete queue suite after the multi-agent repair:

```
$ python3 -m unittest -q automation.tests.test_reconcile_queue
Ran 321 tests in 118.203s
OK
```

Exact staged consistency check:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Parser and human-action schema repair after the `a641dd8` review:

```
$ python3 -m unittest -q automation.tests.test_reconcile_queue
Ran 393 tests in 190.272s
OK

$ python3 automation/run_tests.py
tests: 11/11 files passed

$ python3 -m unittest -q automation.tests.test_check_action_projection
Ran 118 tests in 21.115s
OK

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ GIT_INDEX_FILE=<temporary-index> python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ GIT_INDEX_FILE=<temporary-index> python3 automation/check_core_scope.py --staged
core-scope: pass (3 core path(s), task 2026-07-23-first-class-message-queue; independent review manual; not invoked)
```

`python3 -m py_compile` over the changed production and queue-test modules and
`git diff --check` both exited zero. A direct ordinary-link stress run completed in
0.003253, 0.006320, 0.011363, 0.020883, 0.043826, 0.086017, and 0.172185 seconds for
100, 200, 400, 800, 1,600, 3,200, and 6,400 links respectively.

The integrated rollback matrix passed 10 focused tests in 27.739 seconds, including
direct and synthetic padded heads, standard and custom kinds, clean history, pre-v2
grandfathering, dependency activation, and service removal/restoration. The core suite
passed 55 tests with one skip, and its immutable-range core-scope gate passed over all
13 core paths.

The replacement immutable candidate ran the exact pre-commit gate:

```
commit 3a7b8ccf6b96e317910da7f55b81d2f16c89e691
Ran 393 tests in 300.662s
OK
tests: 11/11 files passed
pre-commit: OK
```

All three fresh first-wave lenses blocked that exact revision. Reproductions showed a
queue-resolution-v1 remove-and-restore downgrade, arbitrary visible instruction fields
inside Tracking, field-looking continuations and Unicode-indented duplicate Actions,
and quadratic malformed raw-HTML scanning. No panel approval is claimed for
`3a7b8cc`.

Queue-v1 stickiness and combined parser repair after the `3a7b8cc` review:

```
$ python3 -m unittest <16 focused lifecycle methods>
Ran 16 tests in 18.642s
OK

$ python3 -m unittest -q automation.tests.test_reconcile_queue
Ran 402 tests in 225.812s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests in 1.129s
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ GIT_INDEX_FILE=<temporary-index> python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ GIT_INDEX_FILE=<temporary-index> python3 automation/check_core_scope.py --staged
core-scope: pass (3 core path(s), task 2026-07-23-first-class-message-queue; independent review manual; not invoked)
```

`python3 -m py_compile automation/markdown_semantics.py
automation/reconcile/reconcile.py automation/tests/test_reconcile_queue.py` and
`git diff --check` both exited zero.

The repaired immutable candidate ran the exact pre-commit gate:

```
commit 297c4b56d957968a2159ab8b09bb0b33ea80fb77
Ran 414 tests in 405.751s
OK
tests: 11/11 files passed
pre-commit: OK
```

Lifecycle review approved that exact revision, but UX and parser lenses blocked, so the
panel was not unanimous. Reproductions showed alternate CommonMark emphasis rendering
hidden Action/response labels, globally paired inline-code runs crossing block
boundaries, two crossed-merge reviews calling live behavior proposed, and one review's
Full context pointing to an unrelated roadmap page. No panel approval is claimed for
`297c4b5`.

Alternate-emphasis, per-inline-block code parsing, and live-review wording repair:

```
$ python3 -m unittest <73 focused parser/presentation methods>
Ran 73 tests
OK

$ python3 -m unittest -q automation.tests.test_check_action_projection
Ran 118 tests
OK

$ python3 -m unittest -q automation.tests.test_reconcile_queue
Ran 416 tests in 254.803s
OK

$ python3 automation/run_tests.py
Ran 416 tests in 414.051s
OK
tests: 11/11 files passed
```

Direct v2 audits of the two corrected crossed-merge reviews reported zero problems;
three focused presentation/reference tests and exact diff checks passed. Reconciliation
reported zero findings. Link, raw-HTML, block-code, and nested-emphasis stress runs
remained approximately linear through 8,000 cases.

The next immutable candidate ran the exact pre-commit gate:

```
commit 7fb6ff09c9601fb5d501be21b48702a2f3fa918a
Ran 416 tests in 406.542s
OK
tests: 11/11 files passed
pre-commit: OK
```

Fresh UX and lifecycle lenses blocked that exact revision; the parser lens did not
produce an approval. Reproductions showed GFM table body rows accepted as top-level
queue metadata, displaced-tip reuse of an immutable handover path with different bytes,
and a recommendation whose final verification evidence was not reachable from its
stable references. No panel approval is claimed for `7fb6ff0`.

GFM table, displaced-handover, and stable-evidence repair after the `7fb6ff0` review:

```
$ python3 -m unittest <9 focused GFM/parser methods>
Ran 9 tests in 1.197s
OK

$ python3 -m unittest <30 focused handover/topology methods>
Ran 30 tests in 59.356s
OK

$ python3 -m unittest -q automation.tests.test_reconcile_queue
Ran 427 tests in 290.055s
OK

$ python3 automation/run_tests.py
Ran 428 tests in 459.437s
OK
tests: 11/11 files passed
```

The final repository run included the last adopted-unmarked displaced-handover
regression. Action projection passed 118 tests; core scope passed 55 with one skip.
Working-tree and exact temporary-index reconciliation reported zero findings, the
temporary-index core gate passed, and compilation/diff checks exited zero. The roadmap
now links the immutable implementation commit and states the final evidence cited by
the test-runner review.

The next immutable candidate ran the exact pre-commit gate:

```
commit 6ba38d54db873cdc56c6d874da4ea220f52c10f2
Ran 428 tests in 449.883s
OK
tests: 11/11 files passed
pre-commit: OK
```

All three fresh first-wave lenses blocked that exact revision. Reproductions showed
cross-block raw-HTML/comment shielding by global backtick pairing, incorrect GFM cell
counts for unescaped pipes inside code spans, rename-out of immutable handovers, GFM
intraword-underscore identity collapse, and an overstated layered-workspace evidence
claim. No panel approval is claimed for `6ba38d5`.

The parser/presentation matrix passed 61 focused cases before one final narrow
code-exclusion hardening; its post-hardening five-test matrix also passed. The action
projection suite passed all 118 tests. Detection stress remained effectively linear
through 8,000 cases: malformed bold candidates completed in 0.00038–0.00107 seconds,
character-reference candidates in 0.00489–0.07871 seconds, and encoded visual-line
candidates in 0.00327–0.05636 seconds. The next immutable candidate's pre-commit gate
is the exact-byte complete-suite evidence after that final hardening.

That staged gate correctly refused to create a commit when one existing queue test
failed: `test_invalid_backtick_fence_info_does_not_hide_fields`. The queue run completed
411 of 412 tests successfully in 407.918 seconds, and the repository runner reported
10 of 11 files passed. No immutable candidate or panel approval is claimed for those
bytes.

Block-aware inline-code repair after the failed gate:

```
$ python3 -m unittest <10 focused block/code/entity/lifecycle methods>
Ran 10 tests
OK

$ python3 -m unittest -q automation.tests.test_reconcile_queue
Ran 414 tests in 260.173s
OK
```

Compilation and working-tree/cached diff checks exited zero. Boundary and valid
same-block code stress runs remained approximately linear through 1,600 cases.

Final integrated parser and repository verification:

```
$ python3 -m unittest -q <13 focused parser/UX methods>
Ran 13 tests in 1.718s
OK

$ python3 -m unittest -q automation.tests.test_check_action_projection
Ran 118 tests in 21.857s
OK

$ python3 automation/run_tests.py
Ran 402 tests in 351.734s
OK
tests: 11/11 files passed
```

Malformed inline raw-HTML opener stress runs completed in 0.002690, 0.004322,
0.008697, 0.018295, and 0.037184 seconds for 500, 1,000, 2,000, 4,000, and 8,000
nested openers. The quoted-opener family completed in 0.008797, 0.016084, 0.031085,
0.063522, and 0.127923 seconds at the same sizes. Final working-tree and exact
temporary-index reconciliation each reported zero findings; temporary-index core
scope passed for the three modified core paths. Compilation and diff checks exited
zero, and the real index remained untouched.

The next immutable candidate ran the exact pre-commit gate:

```
commit 69952dff726ff16ee609367496e1a3337d08c123
Ran 402 tests in 342.793s
OK
tests: 11/11 files passed
pre-commit: OK
```

All three fresh first-wave lenses blocked that exact revision. Reproductions showed
handover schema remove-and-restore downgrade history, repeatable option fields accepted
inside the response section, character-reference-encoded visible directives, and
Unicode line separators that split visible instructions without entering the Tracking
allowlist. No panel approval is claimed for `69952df`.

Handover-schema stickiness, activation dependency, and the combined parser repair after
the `69952df` review:

```
$ python3 -m unittest <26 focused lifecycle methods>
Ran 26 tests in 57.350s
OK

$ python3 -m unittest -q automation.tests.test_reconcile_queue
Ran 412 tests in 264.831s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests in 1.041s
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ GIT_INDEX_FILE=<temporary-index> python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)

$ GIT_INDEX_FILE=<temporary-index> python3 automation/check_core_scope.py --staged
core-scope: pass (2 core path(s), task 2026-07-23-first-class-message-queue; independent review manual; not invoked)
```

`python3 -m py_compile automation/markdown_semantics.py
automation/reconcile/reconcile.py automation/tests/test_reconcile_queue.py` and
`git diff --check` both exited zero.

Final repair after the `6ba38d5` review:

```
$ python3 -m unittest <11 focused GFM/rendering methods>
Ran 11 tests in 0.955s
OK

$ python3 -m unittest automation.tests.test_check_action_projection
Ran 118 tests in 22.816s
OK

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 442 tests in 308.586s
OK

$ python3 -m unittest <14 focused immutable-handover lifecycle methods>
Ran 14 tests in 35.207s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

The final combined queue run included both parser and immutable-handover regressions.
Disposable-index reconciliation also reported zero findings, its core-scope gate
passed for the three modified core paths, and compilation and diff checks exited zero.
The next immutable candidate's pre-commit output and independent panel verdicts are
recorded only after that candidate exists.

The next immutable candidate ran the exact pre-commit gate:

```
commit b5edef6fd05096b46ce84aad182bb5d5624e5d2e
Ran 442 tests in 472.991s
OK
tests: 11/11 files passed
pre-commit: OK
```

All three fresh first-wave lenses blocked that exact revision. Reproductions showed a
yes/no headline whose polarity contradicted its Approve outcome, legitimate identical
handover copies misclassified as mutations, incomplete GFM emphasis flanking and link
destination parsing, inline HTML comments bypassing strict handover enforcement, and
quadratic nested-emphasis rendering. No panel approval is claimed for `b5edef6`.

Repair after the `b5edef6` review:

```
$ python3 -m unittest <10 focused GFM/rendering methods>
Ran 10 tests in 1.011s
OK

$ python3 -m unittest automation.tests.test_check_action_projection
Ran 118 tests in 21.882s
OK

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 452 tests in 313.252s
OK

$ python3 -m unittest <26 focused immutable-handover lifecycle methods>
Ran 26 tests in 74.581s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Compilation, diff checks, disposable-index reconciliation, and disposable-index core
scope also passed. A 32,000-delimiter performance smoke completed in approximately
0.09 seconds. The exact candidate gate and new five-review panel are recorded only
after a new immutable commit exists.

The repaired immutable candidate ran the exact pre-commit gate:

```
commit ebfe7d5559fae160d51f38b156377efd3a90230f
Ran 452 tests in 499.188s
OK
tests: 11/11 files passed
pre-commit: OK
```

Fresh UX and lifecycle lenses approved that exact revision, but the parser lens
blocked, so the panel was not unanimous and no approval carries forward. Integrated
reproductions showed mutated delimiter lengths corrupting a later rule-of-three test,
Python's permissive entity decoder accepting text CommonMark keeps literal,
user-representable private-use placeholders colliding with code spans, and quadratic
per-span restoration. No panel approval is claimed for `ebfe7d5`.

Repair after the `ebfe7d5` review:

```
$ python3 -m unittest <11 focused CommonMark/rendering methods>
Ran 11 tests in 5.525s
OK

$ python3 -m unittest <5 final autolink/rendering methods>
Ran 5 tests
OK

$ python3 -m unittest automation.tests.test_check_action_projection
Ran 119 tests in 21.736s
OK

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 456 tests in 321.474s
OK

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Disposable-index core scope passed for the four changed automation paths, and
compilation and diff checks exited zero. Code-span/autolink segment scaling remained
linear from 4,000 units at 0.199 seconds through 64,000 units at 2.751 seconds. The
exact candidate gate and fresh five-review panel are recorded only after a new
immutable commit exists.

The next immutable candidate ran the exact pre-commit gate:

```
commit 60fabe3a4ffb3c602eb65afcfe5bac8938591592
Ran 456 tests in 505.896s
OK
tests: 11/11 files passed
pre-commit: OK
```

Fresh UX and lifecycle lenses approved that exact revision, but the parser lens
blocked, so the panel was not unanimous and no approval carries forward. Complete v3
reproductions showed that standalone label rendering lost bracket-dependent emphasis
flanking, code spans incorrectly took precedence over owning autolinks, and one-byte
lookbehind misclassified autolinks after an even backslash run. No panel approval is
claimed for `60fabe3`.

Repair after the `60fabe3` review:

```
$ python3 -m unittest <9 focused label/autolink methods>
Ran 9 tests in 9.170s
OK

$ python3 -m unittest automation.tests.test_check_action_projection
Ran 119 tests in 23.102s
OK

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 459 tests in 338.530s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests in 1.102s
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Compilation and diff checks exited zero. Four live GFM differential fixtures matched
the custom visible text. Rendering, reference resolution, and escaped-run adversarial
cases grew 7.61–7.77 times for eight times the input, remaining effectively linear.
The exact candidate gate and fresh five-review panel are recorded only after a new
immutable commit exists.

The next immutable candidate ran the exact pre-commit gate:

```
commit 3d7ffa77aaf92af0ccfc5c800643a5266bee5933
Ran 459 tests in 508.271s
OK
tests: 11/11 files passed
pre-commit: OK
```

Fresh UX and lifecycle lenses approved that exact revision, but the parser lens
blocked, so the panel was not unanimous and no approval carries forward. An integrated
v3 reproduction showed a URI or email autolink inside the apparent queue-link label
causing GFM to close the outer link, leaving it empty while the gate still attributed
the visible text to it. No panel approval is claimed for `3d7ffa7`.

Repair after the `3d7ffa7` review:

```
$ python3 -m unittest <8 focused link-ownership methods>
Ran 8 tests in 3.662s
OK

$ python3 -m unittest automation.tests.test_check_action_projection
Ran 119 tests in 22.491s
OK

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 461 tests in 327.691s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests in 1.153s
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Compilation and diff checks exited zero. Live GFM confirmed that nested URI/email
autolinks split from the empty queue anchor and are rejected, while escaped-angle and
code-span controls remain owned by the queue link and pass. Nested-label resolution
grew 7.04 times for eight times the input. The exact candidate gate and fresh panel
are recorded only after a new immutable commit exists.

The next immutable candidate ran the exact pre-commit gate:

```
commit 74354ba6e905895b34603d1329b261c4d6e8ec33
Ran 461 tests in 510.230s
OK
tests: 11/11 files passed
pre-commit: OK
```

Fresh UX and lifecycle lenses approved that exact revision, but the parser lens
blocked, so the panel was not unanimous and no approval carries forward. A generated
official-GFM differential and complete v3 reproduction showed that one/two-tilde
strikethrough was neither rendered nor rejected, creating visible Action/label
collisions. No panel approval is claimed for `74354ba`.

Repair after the `74354ba` review:

```
$ python3 -m unittest <6 focused GFM strikethrough methods>
Ran 6 tests
OK

$ python3 -m unittest automation.tests.test_check_action_projection
Ran 119 tests
OK

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 465 tests in 338.1s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Compilation and diff checks exited zero. An official-GitHub differential covering 804
structured and 3,000 seeded mixed cases reported zero differences. Scaling remained
linear from 1,000 units at 0.083 seconds through 8,000 units at 0.680 seconds. The exact
candidate gate and fresh panel are recorded only after a new immutable commit exists.

The next immutable candidate ran the exact pre-commit gate:

```
commit 78538b5197ddf24d9d8d98d11d9ed62e17167b32
Ran 465 tests in 513.825s
OK
tests: 11/11 files passed
pre-commit: OK
```

Fresh UX and lifecycle lenses approved that exact revision, but the parser lens
blocked, so the panel was not unanimous and no approval carries forward. A 9,767-source
official-GFM differential and complete v3 reproduction showed that bare URL, `www`,
and email autolink extensions were missing, allowing context-dependent visible identity
and reference ownership to bypass the strict gate. No panel approval is claimed for
`78538b5`.

Repair after the `78538b5` review:

```
$ python3 -m unittest automation.tests.test_check_action_projection
Ran 119 tests
OK

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 469 tests in 372.676s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Focused precedence and boundedness sets, compilation, and diff checks also passed.
An official cmark-gfm structured differential reported zero differences across 2,614
standalone/owning-link comparisons. A 5,616-case seeded mixed differential found no
false accepts and no owning-label differences. The exact candidate gate and fresh panel
are recorded only after a new immutable commit exists.

The next immutable candidate ran the exact pre-commit gate:

```
commit 112b441b3829c5ef3523cad812daa01cc2b48e78
Ran 469 tests in 559.736s
OK
tests: 11/11 files passed
pre-commit: OK
```

Fresh UX and lifecycle lenses approved that exact revision, but the parser lens
blocked, so the panel was not unanimous and no approval carries forward. A
22,591-source official cmark-gfm differential and complete v3 reproduction showed that
extended-email scanning kept surrounding underscore emphasis in the domain, missing
external links that cmark-gfm detects after grouping emphasis. No panel approval is
claimed for `112b441`.

Repair and stopping boundary after the `112b441` review:

```
$ python3 -m unittest <8 focused emphasized-autolink methods>
Ran 8 tests
OK

$ python3 -m unittest automation.tests.test_check_action_projection
Ran 119 tests
OK

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 472 tests in 449.419s
OK

$ python3 -m unittest -q automation.tests.test_check_core_scope
Ran 55 tests
OK (skipped=1)

$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

Compilation and diff checks exited zero. An expanded official cmark-gfm differential
covered 23,464 sources in standalone and owning-link contexts with zero accepted
external-link false negatives, zero accepted standalone rendering differences, and
zero owning-link structure breaks. Per the owner's stopping boundary, no new panel was
started after these bytes; the next session owns the exact commit gate and fresh panel.

The stopping-boundary candidate ran the exact pre-commit gate:

```
commit 589aafea2ec4cc7d1cda6c4f9ee4bbb50cfc5381
Ran 472 tests in 739.035s
OK
tests: 11/11 files passed
pre-commit: OK
```

No independent panel verdict is claimed for `589aafe`; the owner requested a clean
stop after the verified candidate instead of another review-and-repair loop.
