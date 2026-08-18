# Verification — fold the machine record on new human queue items

**Verified:** 2026-08-18 by claude

Only commands actually run and their real output. Everything below was produced on
`task/2026-08-18-fold-the-queue-machine-record`, branched from `main` at `fc8c0af`,
on Python 3.14.6. Output is trimmed to the meaningful part, never paraphrased.

## Repository suite

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
test elapsed: 17.99s
exit=0
```

Baseline before any change was also `15/15 files passed`, exit 0. The queue file alone
grew from `Ran 455 tests` to `Ran 487 tests`:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 487 tests in 55.585s

OK
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
exit=0
```

Per check, on its declared scope:

```
live queue items in the declared scope: 67
  record-swallow        : 0 finding(s)
  fold-shape            : 0 finding(s)
  queue-render          : 0 finding(s)
  human-attention       : 0 finding(s)
  queue-frozen-skeleton : 0 finding(s)
  queue-resolution      : 0 finding(s)
  queue-schema          : 0 finding(s)
```

## Whole-repository scoping proof — no file scoping applied at all

The predicates were run directly against every tracked Markdown file, ignoring their
declared scope, because a check that is only inert because of where it is pointed is
not inert. `v0.1 naive` is the same field-shape test with no region and no skipping.

```
tracked .md files: 627

scope bucket                          files  v0.1 naive  +region  +skip
(root .md)                                4           0        0      0
.github                                   1           0        0      0
automation                                1           0        0      0
docs                                      9          20        0      0
handbook                                 18           2        0      0
history                                  96          25        0      0
memory                                   50           0        0      0
message-queue/ NON-items                  7          54        0      0
message-queue/ live items                67          23        0      0
roadmap                                   3           0        0      0
services                                  3           0        0      0
skills                                   11           0        0      0
tasks                                   339          14        0      0
templates                                13           0        0      0
templates/queue/                          5           5        5      0
TOTAL                                   627         143        5      0

full v0.2 check set on ALL tracked .md, unscoped:
  record-swallow : 0
  fold-shape     : 3
  raw-html       : 27
  visibility     : 5
  TOTAL findings : 35
```

`record-swallow` is **0 unscoped**, which is the number that matters: it is the one new
predicate whose scope is every live queue item of both actors. The other three are 0 on
their declared scope and non-zero off it, for reasons that are correct rather than
accidental, and all 35 are outside that scope:

- `fold-shape` 3 — `.github/pull_request_template.md`, `templates/pull-request.md` and
  `message-queue/open-actions.md`, each of which carries several folds by design. The
  first two are not queue items; the third is the generated digest, which
  `live_queue_items()` excludes by name.
- `raw-html` 27 — every tracked file containing an HTML comment. `unsanctioned_raw_html`
  is `contains_raw_html` minus three line shapes, so it cannot report fewer than
  `contains_raw_html` does, and `contains_raw_html` has always been scoped to live human
  items.
- visibility 5 — all in `templates/`, whose `<placeholder>` angle brackets Python's
  `HTMLParser` reads as real tags.

The same measurement, as a standing test over the real corpus:

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_record_swallow_is_inert_on_every_live_item_in_this_repository
Inertness measured, not scoped: run it on every tracked Markdown file. ... ok
```

## The fourteen attack shapes

Every fixture is built from one canonical folded item produced by the shipped emitter, so
each edit targets bytes that exist.

```
ok PASS  A0  canonical folded item (must PASS)                   :: -
ok FLAG  A1  unclosed <details> above the answer line            :: fold-shape
ok FLAG  A2  fold wraps the answer line, no blank after summary  :: fold-shape
ok FLAG  A3  **Your review:** inside display:none                :: raw-html; field-hidden
ok FLAG  A4  ### SECRET choice inside display:none               :: raw-html; choice-hidden
ok FLAG  A5  fold wrapping a display:none                        :: record-swallow; raw-html
ok FLAG  A6  <details hidden>                                    :: fold-shape; raw-html; field-hidden
ok FLAG  A7  unclosed <details> before ## For the record         :: fold-shape
ok PASS  A8  injected instruction in <summary> (inert)           :: -
ok FLAG  A9  field on the line right after </details>            :: fold-shape; record-swallow
ok FLAG  A10 field indented one space                            :: record-swallow
ok FLAG  A10 field written as a list item                        :: record-swallow
ok FLAG  N   no blank line after </summary>                      :: fold-shape; record-swallow
ok FLAG  N   two folds in one item                               :: fold-shape
ok PASS  N   fold inside a fenced example (must PASS)            :: -

unexpected results: 0
```

Two rows are caught by a different gate than the design predicted, and neither changes
the verdict. **A2** is `fold-shape` alone: swallowing the answer line destroys the
landmark the record region's lower half is defined by, so the region goes empty rather
than expanding to the whole file, which is the conservative choice — expanding it would
police prose and reintroduce the false positives the position rule exists to avoid.
**A5** is caught by `record-swallow` rather than by the field-visibility rule, because
the inner `<div>` swallows the field lines below it before anything can hide them.

## Identity is not integrity — `queue-frozen-skeleton`

Fixture cases, over a live review already carrying a committed human answer. Each payload
is instruction-shaped; each preserves `queue_action_identity()`, which the test asserts
before it asserts the refusal.

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_refuses_every_invisible_append
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_the_frozen_skeleton_accepts_every_legitimate_live_edit
Ran 2 tests
OK
```

Refused: an HTML comment at end of file, an HTML comment before the title, a fenced block
at end of file, an indented code block, and a `display:none` div. Accepted: re-applying
the fold's hard breaks, an editor stripping them back, adding `Answer by`, recording
`Review outcome`, and claiming the item for folding.

Against this repository's own history rather than a fixture:

```
revisions touching message-queue/       : 248
live-item mutation pairs in history     : 119
accepted today by queue_action_identity : 105
ALSO accepted by the v0.2 skeleton      : 105
NEW REFUSALS on real history (must be 0): 0
```

## The emitter

```
$ python3 automation/reconcile/reconcile.py --fix-queue-fold   # run 1
queue fold: 0 file(s) rewritten
$ python3 automation/reconcile/reconcile.py --fix-queue-fold   # run 2
queue fold: 0 file(s) rewritten
$ git status --short
```

Both runs are no-ops at HEAD because the three templates already carry the canonical
block — the first application is the commit itself, where the emitter rewrote all three:

```
changed: ['templates/queue/decision.md', 'templates/queue/clarification.md', 'templates/queue/review.md']
second run changed: []
```

Field preservation across that rewrite, comparing each template to its committed parent:

```
decision.md: fields before 15 after 15  identical=True  fold-shape=[]  swallow=[]
clarification.md: fields before 15 after 15  identical=True  fold-shape=[]  swallow=[]
review.md: fields before 19 after 19  identical=True  fold-shape=[]  swallow=[]
```

Nine malformed shapes converge to one byte string, idempotently, losing no field —
flat with no fold, already canonical, no blank after `</summary>`, no blank before
`</details>`, no `<summary>`, fields indented two spaces, fields as list items,
`<details open>`, and the one-line `<details><summary>` form:

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_fix_queue_fold_converges_every_malformed_shape
Ran 1 test (9 subtests)
OK
```

## No live item was touched

```
$ shasum -a 256 message-queue/open-actions.md
67c845d90f2224fd73d8e5d62c2cf00cfebf2f62541cfb3fc9c957b7f0e54a98  message-queue/open-actions.md
$ python3 automation/reconcile/reconcile.py --fix-open-actions
message-queue/open-actions.md regenerated
$ shasum -a 256 message-queue/open-actions.md
67c845d90f2224fd73d8e5d62c2cf00cfebf2f62541cfb3fc9c957b7f0e54a98  message-queue/open-actions.md
$ git status --short -- message-queue/
```

The digest is byte-identical and nothing under `message-queue/` is modified, which is the
direct consequence of folding zero live items.

## Trailing whitespace, declared to the one tool every clone has

```
$ git diff --check ; echo "exit=$?"
exit=0

$ printf 'x   \n' > tmp/ws-probe.md && git add -N tmp/ws-probe.md && git diff --check
tmp/ws-probe.md:1: trailing whitespace.
+x
exit=2

$ git check-attr whitespace -- templates/queue/review.md \
    message-queue/needs-human/reviews/non-blocking-rereview-human-action-files.md README.md
templates/queue/review.md: whitespace: -blank-at-eol
message-queue/needs-human/reviews/non-blocking-rereview-human-action-files.md: whitespace: -blank-at-eol
README.md: whitespace: unspecified
```

`git am` under `apply.whitespace=fix`, in a purpose-built repository carrying this
repository's `.gitattributes`, one queue file and one ordinary file:

```
=== git am with apply.whitespace=fix, WITH .gitattributes ===
warning: 1 line applied after fixing whitespace errors.
Applying: add trailing
queue field lines keeping 2 trailing spaces: 2 / 2
other.md trailing whitespace kept: 0 / 1  <- still policed
```

Scale of the whitespace change, exactly as designed — 16 lines in 3 files, and the two
agent templates untouched:

```
templates/queue/decision.md: 4 lines with trailing whitespace -> [64, 65, 66, 67]
templates/queue/clarification.md: 4 lines with trailing whitespace -> [67, 68, 69, 70]
templates/queue/review.md: 8 lines with trailing whitespace -> [70, 71, 72, 73, 74, 75, 76, 77]
templates/queue/request.md: 0 lines with trailing whitespace -> []
templates/queue/retry.md: 0 lines with trailing whitespace -> []
TOTAL: 16
```

## Copy-and-fill still holds

```
$ python3 -m unittest -v automation.tests.test_reconcile_queue.ReconcileQueueTests.test_every_queue_template_survives_copy_and_fill \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_queue_template_hiding_a_required_field_in_a_comment_fails
Copy a template, fill its placeholders, commit: zero findings. ... ok
The copy-and-fill guarantee has teeth: prove the old shape breaks. ... ok
Ran 2 tests
OK
```

## `FIELD_RE` and trailing whitespace — the defect the design missed

The fold puts two trailing spaces on every field line but the last, and `FIELD_RE`
captured them into the parsed *value*: `'pending  '`, `'______  '`. Most readers strip
before comparing, so most were safe by luck rather than by design, and
`PLACEHOLDER_RE.fullmatch` stops recognising an unfilled slot. The regex now ends
`(.*?)[ \t]*$`. Measured over every tracked Markdown file, before committing it:

```
tracked files whose parsed fields change: 3 of 623
```

All three are the templates this task folded, and each changes to the value it already
meant (`'waiting  '` → `'waiting'`).

## Line budgets — net contract lines added: 0

```
     139 AGENTS.md
      60 automation/AGENTS.md
      60 message-queue/AGENTS.md
      60 tasks/AGENTS.md
      60 history/AGENTS.md
      34 memory/AGENTS.md
      70 skills/explain-to-human/SKILL.md
     124 README.md
```

`message-queue/AGENTS.md` and `skills/explain-to-human/SKILL.md` are byte-unchanged.
`automation/AGENTS.md` stays at 60 because the new check ids and `--fix-queue-fold` went
inside its existing reconciler table cell, which is one physical line. The
fold's nine rules and the record-region definition live in `templates/README.md`, which
is budget-exempt.

## Five gate holes a weak-model authoring run exposed

Measured before changing anything, over the live human items:

```
 824 words  modern=False  ...  non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md
 700 words  modern=True   ...  non-blocking-stop-a-principle-from-copying-the-line-budget.md
 696 words  modern=True   ...  non-blocking-review-the-explanation-standard.md
 687 words  modern=True   ...  non-blocking-choose-the-gate-for-externally-changed-instruction-files.md
 676 words  modern=True   ...  non-blocking-re-ask-the-older-questions-in-plainer-words.md
 675 words  modern=True   ...  non-blocking-review-the-pull-request-shape.md
```

One live item sits exactly on the old 700-word ceiling and the rest within 25 words of
it, which is what makes the budget a coin flip rather than a rule; it is now 800.

All four live `future-blocking` human items already carry
`**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration`, and
every live `Answer by` is roughly 90 days after its `Filed`, so neither new refusal
touches an existing item — confirmed by `reconcile: 0 blocking finding(s)` above.

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_human_future_boundary_may_only_be_transition_start \
    ...test_answer_by_may_not_lapse_on_the_day_it_is_filed \
    ...test_an_operation_boundary_accepts_a_version_number
Ran 3 tests in 0.012s
OK
```

## The commit gate this clone did not have

```
$ git config core.hooksPath
$ ls .git/hooks/pre-commit
ls: .git/hooks/pre-commit: No such file or directory
```

`core.hooksPath` is unset here, so `automation/install.py` has never run in this clone and
no commit on this branch was gated by the pre-commit hook — exactly the silent hole the
root `AGENTS.md` boot sequence warns about. Both gates were therefore run by hand after
every commit, and the one finding that reached a commit because of it — an unresolvable
backticked path in this file, which `check_links` reads as a repository path — was
found by that manual run and repaired in the following commit — it was a bare backticked
path one directory short of the real file. No `--no-verify` was used,
because there was no hook to bypass. Installing the hook changes this clone's Git
configuration and was left to its owner rather than done unasked.

## Not verified, and why

- **The rendered height on a phone.** `<details>` collapsing is HTML semantics rather
  than a claim about this repository, and nothing here screenshots a phone. No number in
  this file asserts one.
- **Two tests skip under `automation/run_tests.py`.** The runner materialises an isolated
  working-tree view with no `.git`, so the whole-corpus measurement and the historical
  mutation walk have nowhere to run there. Both run in a real clone and their output is
  above; `require_real_checkout()` names the reason rather than silently passing.
- **Generator use is unenforced.** Nothing checks that an item came from a template
  rather than from the nearest legacy file, and `--new-queue-item` was not built.
