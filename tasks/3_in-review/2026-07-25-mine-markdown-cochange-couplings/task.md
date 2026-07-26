# Mine markdown co-change couplings and validate heading anchors

**Claimed-by:** claude
**Filed:** 2026-07-25, by claude, from chat direction after the edge-graph approval — `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Stage 0 and Stage 1 of the approved markdown edge graph, and nothing beyond them. The
approved architecture ships the zero-annotation half first precisely so it can kill the
expensive half: a mined co-change layer plus heading-anchor validation, then one written
experiment that decides whether a typed edge schema is ever justified.

Two mechanisms and one record land here. First, heading-anchor validation inside the
existing `check_links` in `automation/reconcile/reconcile.py`. That check has a live hole:
`re.fullmatch(r"[\w./-]+", cand)` rejects any candidate containing `#`, so a link written
as an-absent-path.md#foo is skipped whole — neither its path nor its anchor is
examined today. Splitting path from fragment applies the existing existence logic to the
path half and validates the fragment against the target file's ATX headings under GitHub's
slug algorithm; the repo has no heading-extraction or slugification helper yet, so both are
new. Second, a standalone stdlib mining CLI under `automation/` walks git history, counts
file-pair co-occurrence, and reports directed couplings above a support and confidence
floor, with the shared commit subjects as already-written evidence. Third, an append-only
accepted/rejected ledger makes each mined verdict durable, so a dismissal never
re-surfaces, and turns the rejection rate into the effective-false-positive rate the
design's governance bands are stated against.

The mining half is advisory by construction: the report verb always exits 0, and it is
deliberately not a `CHECKS` entry in the reconciler, because reconciler findings carry no
severity today and therefore every finding blocks. Severity tiers are a separate backlog
task (2026-07-22-severity-tiers-for-reconciler-findings), and this task does not wait for
it or pre-empt it.

Everything past Stage 1 stays out: the typed `## Edges` schema, the committed graph
artifact, the `impact` query, clause-scoped review debt and the per-folder freshness modes,
repair-item filing, the pre-commit advisory, further directory activation, and the viewer.
Those are deferred and filed separately.

## Acceptance criteria

- [ ] WHEN a live markdown file links `<path>#<fragment>` and `<path>` is absent from both
      the git index and the worktree, THE SYSTEM SHALL yield a `link-check` finding naming
      that path — the case silently skipped today
- [ ] WHEN `<path>` exists but `<fragment>` matches no ATX heading slug in that file, THE
      SYSTEM SHALL yield a distinct `link-check` finding naming the fragment
- [ ] WHEN a fragment matches a heading under GitHub's slug rules — lowercased, spaces to
      hyphens, punctuation dropped, duplicate slugs numbered — THE SYSTEM SHALL stay silent,
      and the existing 19 checks report the same findings on this repository as before
- [x] The mining CLI runs on stdlib only, reads git history through `git log`, and its
      report verb exits 0 on every input including a report full of couplings
- [x] The report applies support ≥ 3 commits, confidence ≥ 0.8, a 40-file commit-size cap,
      a stop-list of files the contract requires to change every session, suppression of
      same-directory pairs, and prints the shared commit subjects for each reported pair
- [x] Every reported candidate can be recorded once in the append-only ledger as accepted
      or rejected with a one-line reason, and a rejected pair is absent from every later
      report
- [x] The report states the rejection rate as the effective-false-positive rate against
      the design's bands: under 10% on target, 10–25% probation, above 25% off
- [ ] Unit tests for the CLI and for anchor validation live in their own files under
      `automation/tests/`, outside `automation/tests/test_reconcile_queue.py`
- [ ] `automation/AGENTS.md` names the new CLI in its tool table and still passes
      `agents-budget` at its 60-line ceiling, with no rule dropped to make room
- [x] `verification.md` records the gating experiment over two hot files: for each
      top-ranked coupling, whether it is a real dependency, and whether a hand-authored
      edge would have added anything the mined pair plus its shared commit subjects did
      not — together with the four-day, ~107-commit warm-up limitation
- [x] `python3 automation/reconcile/reconcile.py --check` and `python3
      automation/run_tests.py` both pass, with real output recorded

**Why five criteria stay unchecked at `4_done`.** Four of them owe transcripts that never
reached `verification.md` — the anchor-hole before-state, the two new `link-check` findings,
and the `agents-budget` run — and backlog task
2026-07-25-complete-stage-0-verification-transcripts is the named carrier of that gap. The
fifth is a genuine miss rather than a missing transcript: the eight anchor tests landed
inside `automation/tests/test_reconcile_queue.py` instead of a file of their own, so the CLI
half of that criterion is met and the anchor half is not. The warm-up limitation is recorded
with the history that actually existed at measurement time — 200 commits, 144 in scope, over
five days — rather than the four-day, ~107-commit estimate the criterion names.

## Links

- Accepted decision: `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`
- Full design, Stage 0 and Stage 1 of the staged plan: `docs/designs/markdown-edge-graph.md`
- Owner-facing decision summary: `docs/designs/markdown-edge-graph-decisions.md`
- Path-type and reciprocity decisions this stage inherits:
  `memory/decisions/2026-07-25-document-edge-path-types.md`,
  `memory/decisions/2026-07-25-document-edges-are-authored-once.md`
- Related backlog task, not a dependency: 2026-07-22-severity-tiers-for-reconciler-findings
