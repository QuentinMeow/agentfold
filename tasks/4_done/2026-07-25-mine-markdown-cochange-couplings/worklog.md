# Worklog — mine markdown co-change couplings and validate heading anchors

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-25 — file-stage-0-and-1 (claude)

- Filed the task record for Stage 0 and Stage 1 of the approved markdown edge graph, with
  the canonical pickup request in the same coordination commit. No feature code written.
- Confirmed the anchor hole is live before planning around it: `check_links` in
  `automation/reconcile/reconcile.py` guards candidates with
  `re.fullmatch(r"[\w./-]+", cand)`, which rejects every candidate containing `#`, so a
  link with a bad path *and* a bad anchor produces no finding at all today.
- Confirmed the repository has no heading-extraction or slugification helper, so both are
  new code in step 3 rather than a reuse.
- Recorded three narrow choices in `design.md`: mining as a standalone advisory CLI rather
  than a `CHECKS` entry (findings have no severity, so every finding blocks), the ledger as
  a tracked text file beside the tool rather than a `memory/` entry (verdicts are permanent,
  memory entries expire), and anchor validation inside the existing `check_links` rather
  than a new check id (retry filenames embed check ids).
- Left the four obstacles the next session would otherwise rediscover in `plan.md`: the
  zero-line `automation/AGENTS.md` budget, the core-scope receipt and branch requirement,
  the quadratic cost of a history walk inside a reconciler check, and the ~205-second test
  suite that runs on every commit.
- Decision this task implements: `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`.

## 2026-07-25 — gating-experiment (claude)

- Ran plan step 9, the experiment that decides whether Stages 2 to 4 are ever built, at
  commit e52f68e. Full transcripts in `verification.md`; both verdicts in `design.md`.
- Swept the floors at confidence 0.5/0.8/0.9 against support 3/5: 52, 43, 20, 18, 11, 9
  candidates. Confidence is the whole control surface; the support floor removes only
  9-17% at every confidence, so it is not doing the job the design assigned it.
- Overruled the brief's choice of hot files on measurement: `automation/AGENTS.md` has 19
  in-scope revisions against `handbook/git-workflow.md`'s 14, so the two hottest durable
  contracts are `automation/AGENTS.md` and `message-queue/AGENTS.md`. Kept the second
  deliberately because it is the target of the case the design calls decisive.
- Judged all 27 candidates touching those two files at confidence ≥ 0.5, plus the two
  candidates in the default report's top ten that fall outside that set, by reading the
  files and the shared diffs. Recorded 29 verdicts through the tool's verbs: 28 accept, 1
  reject. Effective false positives 3.4%, on target — but 10.0% over the default top ten,
  which is the probation trigger, and 0.0% over the hot-file set alone. The governance
  threshold does not name its denominator and at these volumes that decides the band.
- Verified the decisive claim rather than trusting it: `templates/queue/review.md` contains
  the string `message-queue` zero times. Found what the design missed — the restatement is
  fivefold across every queue template, none of them linking its owner.
- Found a live drift: commit aca7014 put "an explicit UTC date" into the owning contract
  and UTC into all five templates' field lines, and left all five prose comments saying
  "a named date".
- Three negative results decided the recommendation. The evidence field is
  non-discriminating: all 27 candidates draw from the same twelve commit subjects, so the
  subjects say which feature landed and never what the relationship is — which argues *for*
  authoring one sentence per edge. Clause anchors are unavailable on the hottest file,
  which has exactly one heading, and 41% of judged candidates point at it. And clause-
  scoped review debt would have filed zero items across the strongest case's whole history,
  because the dependents were always edited in the same commit — including the commit where
  the drift happened, so it would have been silent on the one failure in its own domain.
- Recommendation: narrow. Build a reduced Stage 2 (vocabulary, one `Because:` line, clause
  anchor for the query only). Strike Stage 3 entirely — no committed artifact, no byte-exact
  gate, no determinism suite — and build the graph on demand. Strike the `each-run`
  freshness mode and review-debt repair filing; keep the join report and the ledger.
- Blocker found: `automation/tests/test_mine_cochange.py` asserted the shipped ledger holds
  no verdicts, so the first real use of the ledger failed the test suite and the pre-commit
  hook, and the first commit attempt was refused with core scope and the reconciler both
  passing. Escalated rather than working around it, since the mechanism was under audit.
  Repair authorized and made: that one assertion now checks that the shipped ledger parses
  with zero malformed lines and that every verdict it holds is well-formed — verdict in the
  closed set, ISO date, no tabs in any field, source distinct from target, reason present on
  every rejection. The method is renamed to match, no other test was touched, and
  `mine_cochange.py` behaviour is unchanged. An assertion that a mechanism's durable store
  is empty is an assertion that the mechanism is never used; that is the lesson.
- Corrected a plan-record error rather than the coverage: the eight anchor-validation tests
  do exist, appended to `automation/tests/test_reconcile_queue.py` at lines 12103 to 12208 —
  dead path behind an anchor, live anchor, dead anchor, fenced-heading rejection, duplicate
  slug numbering, the punctuation-heavy real slug, the record and schema exemptions, and a
  bare same-file fragment. Plan step 4 named a file that was never created; step 4 now names
  where they landed. Verified by reading the test names, not by assuming.
- Stated plainly in both `verification.md` and `design.md` what an accept means in this
  ledger: no typed schema exists, so the 28 accepts cannot mean "an edge was declared" and
  each means "judged a real dependency, to be declared if and when Stage 2 ships". The
  ledger is a judgment record, not a declaration record.
- One gap the closing session still owes: steps 1 to 8 landed in e52f68e without recording
  their own transcripts, so the anchor-hole before-state, the two new `link-check` findings,
  and the agents-budget run are still missing from `verification.md`.
- Left step 9's checkbox and every other checkbox in `plan.md` alone, so the session that
  closes out step 10 owns the whole checklist.

## 2026-07-26 — reconcile-merged-task-status (claude)

- Pull request 13 merged into `main` as merge commit 74b9d0d, so the task record was the
  only thing still saying the work was in progress. Advanced it from `1_in-progress` to
  `4_done` without passing through `3_in-review`, since the merge had already happened; the
  task id is unchanged.
- Took over the checklist the gating-experiment session deliberately left whole, and
  checked seven of ten `plan.md` steps and six of eleven acceptance criteria. Every checked
  box was substantiated from `verification.md` or from the merged code, not from the plan's
  own prose.
- Steps 1, 8, and 10 stay unchecked, and so do the four criteria that owe the anchor-hole
  before-state, the two new `link-check` findings, and the `agents-budget` run. Backlog task
  2026-07-25-complete-stage-0-verification-transcripts is the named carrier of that gap, and
  the future-blocking action that orders it against this task is unchanged and still live.
- Found one criterion that no backfill can satisfy: it requires the CLI tests and the anchor
  tests to live in their own files outside `automation/tests/test_reconcile_queue.py`, and
  the eight anchor tests landed inside that file. The CLI half is met by
  `automation/tests/test_mine_cochange.py`; the anchor half is a real miss, so the criterion
  stays unchecked and `task.md` records the split. The owner's wording was left alone.
- Noted a second wording-versus-measurement gap without touching the criterion: the
  warm-up limitation is recorded against 200 commits, 144 in scope, over five days, where
  the criterion names four days and ~107 commits. The limitation itself is recorded, so the
  criterion is checked on substance.
- Advancing this task to `4_done` is what unblocks the transcript backfill, whose ordering
  action names this task reaching that status.
