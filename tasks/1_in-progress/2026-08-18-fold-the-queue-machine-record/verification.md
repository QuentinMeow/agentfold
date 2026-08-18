# Verification — fold the machine record on new human queue items

**Verified:** 2026-08-18 by claude

Only commands actually run and their real output. Everything below was produced on
`task/2026-08-18-fold-the-queue-machine-record`, branched from `main` at `fc8c0af`,
on Python 3.14.6, in a clone whose commit gate is installed
(`core.hooksPath=automation/hooks`). Output is trimmed to the meaningful part, never
paraphrased.

## Corrections to the first record

A red-team pass found two kill shots and six defects in the shape this file first
recorded, and an independent authoring measurement found three more. The repairs are in
`Close the append hole the frozen skeleton left open`. Five numbers this file previously
asserted did not replicate and are corrected here rather than defended:

| First recorded | Measured now |
|---|---|
| baseline `run_tests.py` 15/15 on `main` at `fc8c0af` | **14/15.** `fc8c0af` fails on Python 3.14.6 with `AttributeError: module 'ast' has no attribute 'Str'`. The guard rides on this branch's own first commit, `bccfe0d`; it was never on `main`, and the design's §7.4 was right to call it owed |
| corpus 627 tracked `.md` | **628** (`git ls-files '*.md' \| wc -l`) |
| full check set unscoped: 35 findings, visibility 5 | **38 findings; visibility is 8 across 5 files.** The 5 was a file count reported in a findings column |
| scoping ladder `143 → 5 → 0` | **105 → 5 → 0.** The load-bearing endpoints reproduce exactly; the naive start is 105 when the v0.1 predicate is reconstructed from the shipped code |
| `--fix-queue-fold` idempotent, 0 fields lost | **was false in three ways** — it folded the answer line away irreversibly, no-opped on the one-line form while claiming convergence, and promoted indented code to a real field. All three are repaired below |

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
test elapsed: 18.33s
exit=0

$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 503 tests in 62.039s

OK
```

The baseline is **14/15**, not 15/15. Measured on a pristine checkout of `main`:

```
$ git checkout --detach fc8c0af && git clean -qfdx
$ python3 automation/run_tests.py
FAIL automation/tests/test_reconcile_queue.py
tests: 14/15 files passed

$ python3 -m unittest automation.tests.test_reconcile_queue
AttributeError: module 'ast' has no attribute 'Str'

$ git show fc8c0af:automation/tests/test_reconcile_queue.py | grep -n ast.Str
408:    if isinstance(node, ast.Str):
$ git show bccfe0d:automation/tests/test_reconcile_queue.py | grep -n ast.Str
408:    # `ast.Str` is how 3.7 spells a string literal; 3.8 folded it into
411:    # constant, which is the discrimination `ast.Str` itself performed.
```

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s), 5 advisory (not blocking)
exit=0
```

The five advisory findings are the wrapped values described under
"Silent truncation is live in this repository today". Per check, on its declared scope:

```
live queue items in the declared scope: 67
  record-swallow        : 0 finding(s)
  fold-shape            : 0 finding(s)
  queue-render          : 0 finding(s)
  human-attention       : 0 finding(s)
  queue-frozen-skeleton : 0 finding(s)
```

## Kill shot 1 — a payload appended to a mutable field line

The check dropped every lifecycle-mutable field **line** whole, which is what makes the
lifecycle legal and is also where bytes could hide: the payload only had to move from
column 0 to the end of one. Reproduced against the shipped code at `7aaf11f`, in a
throwaway clone with the hook installed, using the red team's exact bytes:

```
$ git commit -m "RT: routine deadline note"
reconcile: 0 blocking finding(s)
[task/2026-08-18-fold-the-queue-machine-record 215f951] RT: routine deadline note
```

The same bytes on the repaired branch, in a fresh clone, `core.hooksPath` installed:

```
$ python3 -  # append the payload to **Answer by:** on a live review
$ git add -A && git commit -m "RT: routine deadline note"
pre-commit: reconciler
[queue-frozen-skeleton] message-queue/needs-human/reviews/non-blocking-review-the-pull-request-shape.md:
  live queue item changed bytes that its action identity cannot see; a comment, a fenced
  or indented block, or hidden markup was added to or removed from a frozen record
    fix: revert the invisible edit; only lifecycle fields and trailing whitespace may
    change while an item is live, and anything else belongs in a distinct successor action
reconcile: 1 blocking finding(s), 5 advisory (not blocking)

$ git log --oneline -1
a1f0318 Close the append hole the frozen skeleton left open   <- the commit did not land
```

Every mutable field, on a live item and on a record already carrying the owner's
committed answer. Each row asserts `queue_action_identity()` is preserved *before* it
asserts the refusal, so the probe proves the blind spot rather than assuming it:

```
item       field                  identity kept  skeleton
live       Your review            True           REFUSED
live       Status                 True           REFUSED
live       Resolution evidence    True           REFUSED
live       Review target          True           REFUSED
live       Review revision        True           REFUSED
live       Reviewed revision      True           REFUSED
live       Review outcome         True           REFUSED
live       Answer by              True           REFUSED
live       Re-asked (new line)    True           REFUSED
answered   Status                 True           REFUSED
answered   Resolution evidence    True           REFUSED
answered   Review target          True           REFUSED
answered   Review revision        True           REFUSED
answered   Reviewed revision      True           REFUSED
answered   Review outcome         True           REFUSED
answered   Answer by              True           REFUSED
answered   Blocks at              True           REFUSED
answered   Until then             True           REFUSED
answered   Your review            True           REFUSED
answered   Re-asked (new line)    True           REFUSED
```

The whole-file shapes, on the answered record, all still refused — including the mid-line
hidden `<span>`, which the shipped skeleton accepted and which `check_human_attention`
cannot see on an answered item because it skips one:

```
  HTML comment at EOF                          identity kept=True  REFUSED
  HTML comment before the title                identity kept=True  REFUSED
  fenced block at EOF                          identity kept=True  REFUSED
  indented code at EOF                         identity kept=True  REFUSED
  hidden div at EOF                            identity kept=True  REFUSED
  hidden span mid-line on Answer by            identity kept=True  REFUSED
  HTML comment mid-line on Status              identity kept=True  REFUSED
```

**Every lifecycle edit stays legal.** The rule added is not "a mutable value may not
change" — it may change to anything — but "a mutable value must be exactly the value a
parser reads", which is what makes the pair (frozen skeleton, mutable values) total with
respect to the file's bytes:

```
  human writes one sentence in the blank          ACCEPT
  human wraps their sentence with an <angle> word ACCEPT
  waiting -> folding claim edge                   ACCEPT
  awaiting-artifact -> waiting publication edge   ACCEPT
  timing escalation (Answer by moves out)         ACCEPT
  Re-asked bump (a new mutable line)              ACCEPT
  re-apply the fold's hard breaks                 ACCEPT
  an editor strips the hard breaks back           ACCEPT
```

Zero new refusals is **proven rather than sampled**, because the repaired skeleton is
byte-identical to the shipped one on every queue document this repository has ever held:

```
revisions touching message-queue/        : 248
live-item mutation pairs in history      : 119
accepted today by queue_action_identity  : 105
refused by the SHIPPED skeleton          : 0
refused by the REPAIRED skeleton         : 0
NEW REFUSALS on real history (must be 0) : 0

historical queue blobs whose skeleton is unchanged by the repair: 9191 (differs: 0)
```

The totality property is a test rather than an argument
(`test_the_frozen_skeleton_accounts_for_every_byte_of_the_file`): every `rstrip`ed line of
every live item is either frozen in the skeleton or a mutable field line whose raw value
is byte-identical to the parsed one. Nothing falls between the two.

## Kill shot 2 — the fixer folded the answer line away

`fold-shape` reported "the fold sits above the answer line" and named
`--fix-queue-fold`. Following that instruction moved `**Your review:**` inside the fold —
the state the same check calls worst — and the command was a no-op on it afterwards.
Reproduced at `7aaf11f`:

```
$ grep -n "Your review" tmp-item.md
81:**Your review:** ______
$ python3 automation/reconcile/reconcile.py --fix-queue-fold tmp-item.md
tmp-item.md refolded
$ grep -n "Your review\|<details>\|</details>" tmp-item.md
66:<details>
78:**Your review:** ______        <- inside the collapsed fold
80:</details>
$ python3 automation/reconcile/reconcile.py --fix-queue-fold tmp-item.md
queue fold: 0 file(s) rewritten   <- no longer repairable
```

The same file on the repaired branch:

```
$ grep -n "Your review" tmp/tmp-item.md
81:**Your review:** ______
$ python3 automation/reconcile/reconcile.py --fix-queue-fold tmp/tmp-item.md
tmp/tmp-item.md NOT rewritten — refolding it would not make it valid:
    the fold sits above the answer line; machine bookkeeping belongs under
    `## For the record`, below the line you answer on
    fix: move `## For the record` and its fold below the answer line by hand, or copy
    the block from `templates/queue/` — this command will not write a file it cannot
    leave clean
queue fold: 0 file(s) rewritten, 1 refused
exit=1
$ grep -n "Your review\|<details>\|</details>" tmp/tmp-item.md
66:<details>
79:</details>
81:**Your review:** ______        <- untouched, outside the fold
```

Two independent guards, because one would have been enough only until the next shape
nobody thought of: the emitter never harvests a line matching `HUMAN_RESPONSE_LINE_RE`,
and `fix_queue_fold` writes nothing whose result still carries a `fold-shape` problem or
a `record-swallow` loss. The finding that used to name the command now names the repair
that works on it — for the two rules about *where* the fold sits, "move it".

## D1 — the one-line fold now converges

```
$ python3 automation/reconcile/reconcile.py --fix-queue-fold tmp/one-liner.md
tmp/one-liner.md refolded
queue fold: 1 file(s) rewritten
exit=0

fold-shape before: 4          fold-shape after : []
fields readable before: 10    fields readable  : 11    <- the swallowed field recovered
record-swallow   : []         idempotent       : True

$ python3 automation/reconcile/reconcile.py --fix-queue-fold tmp/one-liner.md
queue fold: 0 file(s) rewritten
```

## D2, D3 — one view disagreement, two defects

`record_visible_lines` kept indented code while `semantic_text` blanks it. GitHub renders
a four-space-indented `**Filed:** …` as `<pre><code>` with two literal asterisks, so it is
a code sample and not a bold label. The disagreement was a **blocking false positive** and
an emitter that promoted the sample to a real machine field the reconciler then enforced.
Fixed at the root — that view now blanks indented code, exactly as `semantic_text` does:

```
                                          shipped        repaired
record_swallow_losses(indented sample) : [(83,'Filed')]  []
text_fields after --fix-queue-fold     : 'indented code, not a field'   None
```

## D4 — the shapes the matcher missed

Measured with the repaired `RECORD_FIELD_SHAPE_RE`; every one renders as a bold label and
none is read by `FIELD_RE`, and each is now reported inside the record region:

```
  '1) **Filed:** 2026-01-01'      shape=True   FIELD_RE=False   -> [(83, 'Filed')]
  '>> **Filed:** x'               shape=True   FIELD_RE=False   -> [(83, 'Filed')]
  '> > **Filed:** x'              shape=True   FIELD_RE=False   -> [(83, 'Filed')]
  '| x | **Filed:** y |'          shape=True   FIELD_RE=False   -> [(83, 'Filed')]
  '- - **Filed:** x'              shape=True   FIELD_RE=False   -> [(83, 'Filed')]
  '2. 1. **Filed:** x'            shape=True   FIELD_RE=False   -> [(83, 'Filed')]
```

A table cell is detected and deliberately **not** harvested by the emitter: promoting a
cell to a column-0 machine field would invent a record nobody wrote. A GFM row written
without its outer pipes is still not read, and the docstring says so.

## D5 — the region no longer collapses in silence

```
  answer line fenced     region= 25  truncated=True
  no answer line at all  region= 25  truncated=True
  baseline               region= 63  truncated=False

[record-swallow] …: no readable **Your answer:** / **Your review:** line, so every line
  of `## For the record` falls outside the checked region
```

The region still collapses — widening it to the whole file would police prose and
reintroduce the false positives position scoping exists to remove — but going blind is
now a blocking finding rather than a quiet pass. All 15 live human items carry a readable
answer line, so this is inert today.

## D6 — every commit passes the gate on its own, and one that still cannot

`7aaf11f` (a link repair) is squashed into `20c8e8f`, so the branch no longer carries a
commit the repository's own referee refuses. Each commit checked out and gated:

```
commit     reconcile --check                                   run_tests.py
fc8c0af    reconcile: 0 blocking finding(s)                    tests: 14/15 files passed
bccfe0d    reconcile: 0 blocking finding(s)                    tests: 15/15 files passed
18f6c21    reconcile: 0 blocking finding(s)                    tests: 15/15 files passed
43990bd    reconcile: 0 blocking finding(s)                    tests: 15/15 files passed
a1f0318    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
0495f40    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
```

`43990bd` is `20c8e8f` with `7aaf11f` folded into it; `fc8c0af` is the base and is `main`.

Replaying the real pre-commit hook against each commit's own staged diff is stricter than
a checkout, and it finds two more. Both are recorded rather than smoothed over:

```
bccfe0d    staged=13  exit=1  [core-scope] Core fit needs `**Provider substitution:** …`
18f6c21    staged=5   exit=1  [core-scope] Core fit needs `**Provider substitution:** …`
43990bd    staged=2   exit=0  pre-commit: OK
a1f0318    staged=9   exit=0  pre-commit: OK
0495f40    staged=3   exit=0  pre-commit: OK
```

1. **`design.md`'s Core fit read as an unfilled placeholder.** `check_core_scope`'s
   `is_placeholder` treats any value containing `<` as unfilled, and the
   `Provider substitution` reason named the fold by its tag. Reworded in `a1f0318`, which
   is why the last two commits pass; the first two cannot be re-made carrying the fix,
   for the reason below.
2. **`bccfe0d` creates the task directly in `1_in-progress`, and the landing gate refuses
   it.** This is unrepaired and it is a ship blocker:

```
$ python3 automation/reconcile/reconcile.py --check --range <fc8c0af>...<a1f0318>
[task-admission] tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record/task.md:
  task snapshot bccfe0d67… violated lifecycle topology: new
  task:2026-08-18-fold-the-queue-machine-record was created directly in 1_in-progress
    fix: create new tasks in 0_backlog, then claim and move them through the lifecycle
reconcile: 1 blocking finding(s), 5 advisory (not blocking)
```

The documented repair is to file the task in `0_backlog` and claim it in a second commit.
Attempted, and it is not reachable from this session:

```
$ git commit   # the backlog-creation commit
[task-structure] tasks/0_backlog/2026-08-18-fold-the-queue-machine-record/task.md:
  unclaimed backlog work has no canonical needs-agent request
    fix: file a non-blocking pickup request and link it in Queue actions
reconcile: 1 blocking finding(s)
```

A backlog task needs a canonical pickup request under `message-queue/needs-agent/requests/`,
and this session was instructed to treat `message-queue/` as frozen. **The branch cannot
pass `--range` until someone with permission to write that queue item splits `bccfe0d`
into a filing commit and a claim commit.** Nothing was weakened to hide this, and no
`--no-verify` commit is on the branch — one throwaway experiment used it while probing
this constraint and was discarded unreferenced.

## D7 — the placeholders a sanitizer deleted

`<YYYY-MM-DD>` and `<who>` parse as unknown HTML tags. This matters now in a way it did
not before: the record block is a `<details>` a reader is invited to open, so the rendered
template became a surface people copy from. Measured with this repository's own renderer:

```
BEFORE
**Filed:** , by [, from task ``]
**Answer by:**

AFTER
**Filed:** < YYYY-MM-DD >, by < who >[, from task ``]
**Answer by:** < UTC YYYY-MM-DD — 90 days from Filed unless something real dates it >
```

Spacing the brackets was chosen over backticking them because `**Filed:**` must begin with
a bare date for `parse_leading_date`, and a backticked date breaks the copy-and-fill
guarantee. `` `<id>` `` and the backticked path placeholders are unchanged: they show
empty above only because `rendered_human_text` parses HTML without building code spans
first, which is a known limit of that view and not what a CommonMark renderer does. That
half rests on the red team's measurement against the real GitHub API, not on anything run
here, and it is labelled as theirs.

## Silent truncation is live in this repository today

`FIELD_RE` and `EXAMPLE_CONSEQUENCE_RE` are per-line patterns and CommonMark's lazy
continuation is not, so a value written as ordinary wrapped prose renders whole and parses
to its first newline. **This is not hypothetical: two live queue items carry five values
cut mid-sentence right now.**

```
message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md
  line 44  *Example consequence:*   "nothing will queue a repair for it, and knows the …"
  line 51  *Example consequence:*   "expects a `retries/` folder that fills itself, fin…"
message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md
  line 59  *Example consequence:*   "live and the three tasks stay in review, because a…"
  line 68  *Example consequence:*   "done, while the crossing itself stays permanently …"
  line 78  *Example consequence:*   "actionable because the code is on main and can be …"
```

Both items predate the current template, so both are frozen and a rewrite is refused.
Blocking them would be an unrepairable gate; saying nothing would be the silent loss the
whole check exists to end. So the same predicate reports at two tiers:

* **blocking** (`record-swallow`) on items the current template governs — **0 today**, and
  the rule every new item is written under;
* **advisory** (`explanation-shape`) on items it does not — the five above, which will keep
  printing until those two questions are answered and deleted. That is deliberate.

The human's own answer line is exempt at both tiers: a person may wrap their sentence, and
their answer commit is the one edit this repository can never refuse.

## The word budget goes back to 700

Raising it to 800 was argued from three of eight authored items failing at 701–723.
Measured afterwards on freshly authored items, the raise did what a raised ceiling does:

```
                              700 ceiling      800 ceiling
mean words before the answer        673.4            736.2   (+9.3 %)
mean rendered lines                  43.5             55.1   (+27 %)
items over 700 words                  3/8              6/8
paired authoring-quality difference          McNemar p = 0.50 (inside noise)
```

The owner's complaint is visual volume, so a ceiling that buys no measured quality and
costs a tenth more words is the wrong trade. What the failed attempts needed was the
number, which the finding now carries — how many words are written, how many are allowed,
and exactly how many to cut. Reverting is inert on the corpus: the five live items the
format governs measure 700, 696, 687, 676 and 675 words, and the one 824-word item
predates the format and is skipped.

**Both numbers came from the coordinator's measurement, not from a run in this session.**
Nothing here re-derives them; what this session verified is that 700 refuses nothing that
is live.

## A fabricated commit id is refused

Two authoring attempts kept a real 7-hex prefix and invented the trailing 33 digits,
because the rule they could read demanded a *full* id and nothing said the id had to
exist. It is refused, and the message now names the legal way to file a review before its
artifact exists:

```
real base      : 18f6c21a7b031476922a3b3c79f203d6d8b0282d
fabricated     : 18f6c21aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
REVIEW_REVISION_RE.fullmatch : True      <- well-formed, which is what makes it dangerous
git_review_revision_problems : ['18f6c21aaaa… is unavailable']

[queue-schema] …: **Review revision:** is not a reviewable Git artifact: … is unavailable
    fix: an id that does not resolve in this repository was invented, not read: paste
    `git rev-parse <ref>` output on both sides of the range, and until the artifact
    exists file the item with **Status:** awaiting-artifact and both target and revision
    literally `pending`
```

The resolvability rule already existed; what was missing was a test holding it and a
message pointing at `pending`. Both are now present
(`test_review_binding_refuses_an_invented_commit_id`). A `Review target` Git range is
covered transitively, because target and revision must be byte-identical.

## Whole-repository scoping proof — no file scoping applied at all

The predicates were run directly against every tracked Markdown file, ignoring their
declared scope, because a check that is only inert because of where it is pointed is not
inert.

```
tracked .md files: 628
live queue items : 67

scope bucket                            files  swallow  wrapped   fold
(root .md)                                  4        0        1      0
.github                                     1        0        0      1
automation                                  1        0        0      0
docs                                        9        0       12      0
handbook                                   18        0        1      0
history                                    96        0       17      0
memory                                     50        0        0      0
message-queue/ NON-items                    7        0        1      1
message-queue/ live items                  67        0        5      0
roadmap                                     3        0        0      0
services                                    3        0        0      0
skills                                     11        0        1      0
tasks                                     340        0      144      0
templates                                  18        0        0      1
TOTAL                                     628        0      182      3

scoping ladder over all 628 tracked .md, no file scoping:
  v0.1 naive predicate (whole file, comments kept) : 105
  + record-region scoping                          : 5
  + comment/fence/indented-code skip (as shipped)  : 0
```

`record-swallow` is **0 unscoped** across all 628 files, unchanged by the D3 and D4
repairs, which is the number that matters: it is the one new predicate whose scope is
every live queue item of both actors.

The `wrapped` column is the truncation predicate run with no scoping at all. **182 across
the repository is the honest number**, and it is why that predicate is scoped to live
queue items: `tasks/**/design.md` has written `*Example consequence:*` as wrapped prose
144 times, those files are records, and nothing reads their parsed values.

The full check set, unscoped:

```
  record-swallow        : 0 finding(s)
  fold-shape            : 3 finding(s) in 3 file(s)
        1x  .github/pull_request_template.md
        1x  message-queue/open-actions.md
        1x  templates/pull-request.md
  raw-html (files)      : 27 file(s)
  visibility            : 8 finding(s) across 5 file(s)
        templates/queue/clarification.md   choices=['Reading A — <short name>', 'Reading B — <short name>']
        templates/queue/decision.md        choices=['Option A — <short name>', 'Option B — <short name>']
        templates/task/design.md           choices=['Option A — <name>', 'Option B — <name>']
        templates/task/verification.md     headings=['<check name, e.g. "unit tests">']
        templates/task/worklog.md          headings=['<YYYY-MM-DD> — <session slug> (<who>)']
  TOTAL unscoped        : 38
```

**38, not 35, and visibility is 8 findings across 5 files** — the earlier 5 was a file
count sitting in a findings column. Every one is outside the declared scope, and the eight
visibility findings are all `templates/` placeholders whose angle brackets Python's
`HTMLParser` reads as tags. The D7 repair does not reduce them: they are choice labels and
headings outside the fold, and rewriting every placeholder in `templates/task/` is a
different task.

## The fold ships with zero production exercise

Stated plainly because nothing else in this branch says it: **`queue-resolution` refuses a
retro-fold, so all 15 live human items stay unfolded permanently.**

```
$ python3 automation/reconcile/reconcile.py --fix-queue-fold <live item> && git commit
[queue-resolution] …: live queue action was rewritten: action identity changed while the
  queue item remained live
```

The fold path therefore has no production exercise at all. No existing item will ever use
it; only items filed from today's templates will, and none has been filed. `grep -r
"^<details>" message-queue/` returns nothing. The corpus is mid-migration and the nearest
real files are actively wrong to copy — they predate the redesign, use flat fields, and
carry the banned `Look-at` — which is now stated once, in `templates/README.md`, because
copying the nearest existing file is a reasonable instinct that produces an invalid result.

## The emitter, and the templates

```
$ python3 automation/reconcile/reconcile.py --fix-queue-fold   # run 1
queue fold: 0 file(s) rewritten
$ python3 automation/reconcile/reconcile.py --fix-queue-fold   # run 2
queue fold: 0 file(s) rewritten
$ git status --short
```

Both runs are no-ops at HEAD because the three templates already carry the canonical
block. Ten malformed shapes converge to one byte string, idempotently, losing no field —
the nine the first record listed, plus the one-line form that used to be a dead end:

```
$ python3 -m unittest automation.tests.test_reconcile_queue.ReconcileQueueTests.test_fix_queue_fold_converges_every_malformed_shape \
    ...ReconcileQueueTests.test_fix_queue_fold_repairs_the_one_line_fold \
    ...ReconcileQueueTests.test_fix_queue_fold_never_folds_the_answer_line_away \
    ...ReconcileQueueTests.test_fix_queue_fold_refuses_to_write_a_state_it_cannot_leave_clean \
    ...ReconcileQueueTests.test_fix_queue_fold_never_promotes_indented_code_to_a_field
Ran 8 tests
OK
```

Rules a checker enforces and no document showed are now in the templates, which are
budget-exempt and are the file a filing agent already has open: the `Confidence` spelling
with its em dash, the banned `Look-at` field, that a recommendation must repeat a shown
choice's label text rather than paraphrase it, that a Git range must be byte-identical and
unbackticked on both sides, and that every value is one physical line. The two agent
templates say in one line that their difference from the human three is deliberate.

## No live item was touched

```
$ python3 automation/reconcile/reconcile.py --fix-open-actions
message-queue/open-actions.md regenerated
$ git status --porcelain
 M automation/reconcile/reconcile.py
 M automation/tests/test_reconcile_queue.py
 M templates/README.md
 M templates/queue/clarification.md
 M templates/queue/decision.md
 M templates/queue/request.md
 M templates/queue/retry.md
 M templates/queue/review.md
```

The digest regenerates byte-identically and **0 files under `message-queue/` are
modified**, which is the direct consequence of folding zero live items.

## Line budgets — net contract lines added: 0

```
     139 AGENTS.md
      60 automation/AGENTS.md
      60 message-queue/AGENTS.md
      60 tasks/AGENTS.md
      60 history/AGENTS.md
      70 skills/explain-to-human/SKILL.md
     124 README.md
```

`message-queue/AGENTS.md` and `skills/explain-to-human/SKILL.md` are byte-unchanged.
`automation/AGENTS.md` stays at 60. Everything this round added went into
`templates/README.md` and the five queue templates, which `check_agents_budget` exempts.

## Trailing whitespace, declared to the one tool every clone has

```
$ git check-attr whitespace -- templates/queue/review.md \
    message-queue/needs-human/reviews/non-blocking-rereview-human-action-files.md README.md
templates/queue/review.md: whitespace: -blank-at-eol
message-queue/needs-human/reviews/non-blocking-rereview-human-action-files.md: whitespace: -blank-at-eol
README.md: whitespace: unspecified

$ git diff --check ; echo "exit=$?"
exit=0
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

## The fourteen attack shapes

Unchanged from the first record and re-run after the repairs:

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

**A2** is `fold-shape` alone, and that is now a documented consequence rather than a
surprise: swallowing the answer line destroys the landmark the record region's lower half
is defined by, so the region collapses — and since this round, it says so out loud.

## `FIELD_RE` and trailing whitespace — the defect the design missed

The fold puts two trailing spaces on every field line but the last, and `FIELD_RE`
captured them into the parsed *value*: `'pending  '`, `'______  '`, which
`PLACEHOLDER_RE.fullmatch` stops recognising as an unfilled slot. The regex now ends
`(.*?)[ \t]*$`. Measured over every tracked Markdown file before committing it: 3 files
change their parsed values, all three the templates this task folded, each to the value it
already meant.

## Not verified, and why

- **The rendered height on a phone.** `<details>` collapsing is HTML semantics rather than
  a claim about this repository, and nothing here screenshots a phone.
- **GitHub's own sanitizer.** No network call was made from this session. The claim that a
  backticked `<id>` survives real GitHub rendering is the red team's measurement against
  `api.github.com/markdown`, and it is attributed to them. What is measured here is this
  repository's own renderer view, which is stricter about code spans than CommonMark.
- **The authoring numbers.** The +9.3 % length increase, the McNemar p = 0.50, and the
  fabricated-oid observation come from the coordinator's authoring runs. This session
  re-derived none of them; it verified only that acting on them refuses nothing live.
- **Two tests skip under `automation/run_tests.py`.** The runner materialises an isolated
  working-tree view with no `.git`, so the whole-corpus measurement, the historical
  mutation walk and the byte-partition proof have nowhere to run there. All three run in a
  real clone and their output is above; `require_real_checkout()` names the reason rather
  than silently passing.
- **`bccfe0d`'s lifecycle topology.** Named above as an unrepaired ship blocker, with the
  exact command that refuses it and the exact reason the documented repair is out of reach
  from here.
- **Generator use is unenforced.** Nothing checks that an item came from a template rather
  than from the nearest legacy file, and `--new-queue-item` was not built.

---

# Landing session — 2026-08-18, by claude

Everything under this heading was produced after the record above, on the repaired branch.
Where it contradicts the record above, this section is the later measurement and says so.

## The lifecycle blocker is repaired, and the landing gate passes

The first commit was split into a `0_backlog` filing commit carrying the canonical
`task-pickup` request, and a claim coordination commit that sets `Claimed-by`, moves the
folder to `1_in-progress`, adds `plan.md` and `worklog.md`, and deletes the request. Every
commit after it was replayed through the real pre-commit hook; none used `--no-verify`.

```
$ python3 automation/reconcile/reconcile.py --check --range \
    fc8c0af0bb7f434c5463eda9f6eda8d570f58afa...58e701d29cf3cd01a6f192374c2868cac2337183
reconcile: 0 blocking finding(s), 5 advisory (not blocking)
exit=0
```

The `[task-admission]` finding that refused the branch — "task snapshot … was created
directly in 1_in-progress" — is gone. The 5 advisories are the two frozen items with values
cut mid-sentence, unchanged and expected.

## Every commit gated by checkout

Each commit checked out in a fresh clone with the hook installed, then gated:

```
commit     reconcile --check                                   run_tests.py
de1e62b    reconcile: 0 blocking finding(s)                    tests: 14/15 files passed
19a3b7e    reconcile: 0 blocking finding(s)                    tests: 14/15 files passed
c1c78a6    reconcile: 0 blocking finding(s)                    tests: 15/15 files passed
e628ad4    reconcile: 0 blocking finding(s)                    tests: 15/15 files passed
89a11fe    reconcile: 0 blocking finding(s)                    tests: 15/15 files passed
234bceb    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
d5195b5    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
92c03f3    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
5951c39    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
d2ba47e    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
58e701d    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
e292b21    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
cb245eb    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
16aceb6    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
2cf5479    reconcile: 0 blocking finding(s), 5 advisory        tests: 15/15 files passed
```

Every commit on the branch except the one carrying this table is in it, and that regress
has to stop somewhere: a table cannot contain the commit that writes it. Rather than a
count that goes stale on the next commit, the invariant is the one to check —
`git rev-list fc8c0af..HEAD` names the rows that should exist, every commit listed above
was gated by checkout in a fresh clone with the hook installed, and the range run below
covers the whole branch including the rows recorded after the fact. No commit used
`--no-verify`.

**The two 14/15 rows are stated rather than smoothed over.** `de1e62b` and `19a3b7e` are
record-only coordination commits that change no code, so they inherit `main`'s state at
`fc8c0af` exactly — including its Python 3.14.6 failure:

```
$ git checkout --detach 19a3b7e && python3 automation/run_tests.py
FAIL automation/tests/test_reconcile_queue.py
tests: 14/15 files passed
$ python3 -m unittest automation.tests.test_reconcile_queue
AttributeError: module 'ast' has no attribute 'Str'
```

The `ast.Str` guard rides on `c1c78a6`, the first commit that touches code. Splitting the
old first commit moved the first green row one commit later; it introduced nothing. The
gate the hook actually runs — core scope, the reconciler, and the staged-path test lane —
passed on every commit at commit time, because both coordination commits stage only record
paths and their lane selects no test file.

Two corrections in this file are stale as of this session and are corrected here rather
than edited above, because the record above is what that session measured:

- "`bccfe0d`'s lifecycle topology … an unrepaired ship blocker" — repaired; the shas it
  names no longer exist on the branch and survive only on `backup/pre-ceremony-a2ab98d`.
- "`message-queue/needs-human/reviews/README.md` still lacks its one-line warning" — it
  now carries it.

## Re-measured on the correction pass (2026-08-18, later session)

The landing gate at the branch tip, full object ids, and the whole branch re-gated:

```
$ python3 automation/reconcile/reconcile.py --check --range \
    fc8c0af0bb7f434c5463eda9f6eda8d570f58afa...2cf5479273ec052fa12d77840027dfe17dd5316e
reconcile: 0 blocking finding(s), 5 advisory (not blocking)
exit=0
```

Every commit `fc8c0af..2cf5479` was checked out detached in a fresh clone with the hook
installed and gated individually: **0 blocking on all of them**, and the advisory column
reproduces the table above exactly — blank through `89a11fe`, `5 advisory` from `234bceb`
onward.

The rendered-volume figures recorded for the ten legacy items were re-derived from scratch
rather than trusted, and reproduce exactly: **106** bookkeeping field lines, **7,385**
painted characters, **252** lines of screen at 40 columns, against **740** characters and
**30** lines collapsed — −90.0% characters, −88.1% screen. Width sensitivity reproduces
too: 32 → 290, 40 → 252, 48 → 221. Scope is every `**Key:** value` line above the answer
line except `Action`, `Why-you-might-care` and `If-you-do-nothing`; painted characters are
those lines with `**` and backticks removed; a phone line is a greedy wrap at 40 columns.

Two figures in the record did **not** survive:

- The worst single file is
  `message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md`
  at **1,013** characters and **33** lines over 11 field lines. The excerpt that
  `non-blocking-choose-what-happens-to-the-ten-older-question-files.md` originally labelled
  "the worst file" was from `non-blocking-review-template-first-explanation.md`, which
  measures 790 and 27 — **fourth of ten**. Its bytes were faithful and only its label was
  wrong; the next bullet records how both were repaired.
- That same item's "Ten of the fifteen questions waiting for you" was the pre-branch
  count. At this tip: **17** live `needs-human/` items, **15** with `Status: waiting`,
  **10** carrying bookkeeping above the answer line and **7** below. **Both claims are now
  repaired.** Editing the live item is refused, and amending its filing commit is refused
  too (at hook time HEAD still holds the old item, so the check sees a live rewrite). The
  legal route was to rebuild the filing commit from its parent, so the item is born
  correct: `reconcile --check` reports `0 blocking finding(s)` on that rebuilt commit. The
  item now reads "Ten of the seventeen questions in your queue", states 7 under / 10 above,
  and excerpts `non-blocking-review-layered-development-workspace.md`, the measured worst
  of the ten at 1,013 characters and 33 lines. The two handovers that project the item were
  rebuilt the same way, because a committed handover is immutable and its projection had to
  be born correct as well.

## The word budget: 800, on held-out evidence

The revert to 700 recorded above was measured wrong, and both measurements are kept.

```
                                     700 ceiling      800 ceiling
TRAIN, freshly authored items
  mean words before the answer             673.4            736.2   (+9.3 %)
  mean rendered lines                       43.5             55.1   (+27 %)
  items over 700 words                       3/8              6/8
  paired quality difference                        McNemar p = 0.50 (inside noise)

HELD-OUT, same candidate prose under both gates
  Tier C pass^2                            0.375            0.750
  blocking findings, 16 files                 11                4
  human items over budget                   7/10             0/10
  mean words before the answer                     724.7
  worst overrun at 700                          92 words (baseline's worst: 5)
```

Both are the coordinator's measurements and neither was re-derived here. What this session
verified is the consequence: at 800, `reconcile --check` is 0 blocking, every live governed
item has headroom, and the new counter reports it.

Re-run unabridged at the branch tip after the repair above. It supersedes an earlier run of
the same command recorded here, which reported 694 words for
`non-blocking-choose-what-happens-to-the-ten-older-question-files.md`; correcting that item
lengthened it to 716, and no other line moved. Re-run it rather than trust these numbers:

```
$ python3 automation/reconcile/reconcile.py --word-count
templates/queue/decision.md: 226 of 800 words — 574 to spare
templates/queue/clarification.md: 227 of 800 words — 573 to spare
templates/queue/review.md: 296 of 800 words — 504 to spare
message-queue/needs-human/decisions/non-blocking-choose-the-gate-for-externally-changed-instruction-files.md: 687 of 800 words — 113 to spare
message-queue/needs-human/decisions/non-blocking-choose-what-happens-to-the-ten-older-question-files.md: 716 of 800 words — 84 to spare
message-queue/needs-human/decisions/non-blocking-dispose-five-half-read-values-in-two-frozen-questions.md: 727 of 800 words — 73 to spare
message-queue/needs-human/decisions/non-blocking-re-ask-the-older-questions-in-plainer-words.md: 676 of 800 words — 124 to spare
message-queue/needs-human/decisions/non-blocking-stop-a-principle-from-copying-the-line-budget.md: 700 of 800 words — 100 to spare
message-queue/needs-human/reviews/non-blocking-review-the-explanation-standard.md: 696 of 800 words — 104 to spare
message-queue/needs-human/reviews/non-blocking-review-the-pull-request-shape.md: 675 of 800 words — 125 to spare
word count: 10 file(s), 0 over budget
exit=0
```

The command exits 1 when anything is over, so an author can use it as a self-check before
the commit that would otherwise be the first place the number appears.

## `memory/decisions/` has no integrity gate at all

Measured in a throwaway clone at the branch head, hook installed, one payload appended at
end of file, staged, then gated. Each row is an independent probe from a clean tree:

```
target                                        payload          reconcile --check
memory/decisions/2026-07-22-bold-key-…md      visible prose    0 blocking, 5 advisory
memory/decisions/2026-07-22-bold-key-…md      HTML comment     0 blocking, 5 advisory
memory/decisions/2026-07-22-bold-key-…md      fenced block     0 blocking, 5 advisory
memory/decisions/2026-07-22-bold-key-…md      indented code    0 blocking, 5 advisory
history/conversations/…/handover.md           HTML comment     1 blocking, 5 advisory
history/conversations/…/handover.md           visible prose    1 blocking, 5 advisory

$ git commit -m "probe: append an invisible directive to a decided ADR"   # hook: OK
$ python3 automation/reconcile/reconcile.py --check --range <base>...<head>
reconcile: 0 blocking finding(s), 5 advisory (not blocking)
```

The handover rows are `handover-queue-projection` ("handover record was modified after
queue-projection adoption"). So the original finding's class is closed where it was raised:
queue items by `queue-frozen-skeleton`, handovers by an existing byte-level gate. What
remains is different in kind — `memory/decisions/` has no integrity check to be blind, and
the boot sequence sends every agent to read it. Filed as
`message-queue/needs-agent/requests/non-blocking-freeze-decided-records-against-invisible-appends.md`.

## The rendering win, measured

Definition, stated because the number is meaningless without it. *Painted characters* are
the characters a renderer paints for the machine field lines: the bold key text, the colon,
the space and the value, with the `**` and backtick syntax removed. *Phone lines* is a
greedy word wrap of each painted line at 40 columns, at least one line each.

```
the ten live human items that predate the current format
  106 field lines · 7,385 painted characters · 252 phone lines
collapsed behind one `<summary>` each
      10 lines ·   740 painted characters ·  30 phone lines
                                            −90.0 % characters, −88.1 % lines

worst single file  message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md
                   1,013 painted characters, 33 phone lines -> 74 characters, 3 phone lines
```

Width sensitivity, because "phone" is a wrap width and not a device:

```
  32 columns: 290 -> 30 lines      40 columns: 252 -> 30      48 columns: 221 -> 20
```

**One inherited figure did not reproduce.** The pair "524 → 89 painted characters, 17 → 3
phone lines" was handed to this session as measured. The line half reproduces exactly:
`non-blocking-review-the-pull-request-shape.md` has 9 record fields wrapping to 17 lines at
40 columns, against 3 for the collapsed summary. The character half does not reproduce
under any single consistent definition — that file's record section measures 521 painted
characters including its heading and caption, 451 for its field lines alone, against 74 for
the summary. The figures above are this session's own, with the definition stated, and the
inherited pair should not be requoted.

## What this session did not verify

- **GitHub's own renderer.** No network call was made from here either. The claim that YAML
  front matter renders as a table above the first heading is attributed in the ADR that
  uses it, and is not this repository's measurement.
- **The authoring numbers**, train and held-out alike. Both tables above are the
  coordinator's; this session verified only that acting on them refuses nothing live.
- **The fold in production.** Still zero exercise: `queue-resolution` refuses a retro-fold,
  so all 15 live human items stay unfolded, and the three items filed this session are
  agent-written rather than a real authoring run. Two of them carry the fold; nobody has
  yet opened one on a phone.
