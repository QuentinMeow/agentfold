# Build Stage 2 of the edge graph in its reduced, measured form

**Status:** in-repair
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** Build the typed edge schema in the reduced form the gating experiment supports: the relation vocabulary and its one-question test, one `Because:` line per edge, a clause anchor only where the target has two or more headings, `Update-when:` as prose the query prints, `handbook/` activated alone, and edges authored from the mined candidate list rather than from memory.
**Full context:** `docs/designs/markdown-edge-graph.md`
**Resolution evidence:** `roadmap/current-state.md`
**If unanswered:** No typed edge exists; the mined advisory CLI stays the whole feature and relationships between documents keep being recorded nowhere.

## What you need to know

The gating experiment found exactly one thing mining cannot express, and it is the reason
this stage survives at all: **the relation type**. All 27 hot-file candidates draw their
evidence from the same pool of twelve commit subjects, and "harness: bind actions and
reviews to exact boundaries" is the leading evidence line for the pair that copies a prefix
rule, the pair that summarises a reconciler check, and the pair that restates provider
admission. Three different relationships, one indistinguishable sentence. The type changes
the disposition — a restatement is a candidate for deletion, a dependency for review, an
enforcement link for keeping — so it is worth one authored sentence per edge.

What the same experiment cut from this stage:

- **One `Because:` line per edge**, because the free evidence from shared commit subjects
  is measurably non-discriminating. The design's claim that those subjects are
  "already-written, never-stale rationale" is measurably weaker than it reads.
- **The clause anchor only where the target has two or more headings.** On
  `message-queue/AGENTS.md` clause scoping is worth about 4.7× — an edge anchored at its
  routing clause fires on 3 of its 14 in-scope revisions rather than all 14. On
  `automation/AGENTS.md`, the hottest markdown file in the repository at 19 in-scope
  revisions, every revision reports one section of one, because the file has exactly one
  heading. A mandatory anchor has no legal answer there, and 12 of the 29 judged candidates
  (41%) point at that file.
- **`Update-when:` as printed prose only**, on the relations that already require it. No
  derived debt is built here; whether any derived-freshness mode ships at all is an open
  owner decision at
  `message-queue/needs-human/decisions/future-blocking-keep-or-drop-the-each-run-freshness-mode.md`.
- **`handbook/` activated alone**, as planned, with edges authored from the ledger's accept
  lines rather than from recollection. Stage 0 recorded 28 accepts, and those accept lines
  are the authoring queue — a fresh report will not re-propose them, because the ledger
  suppresses every decided pair.

Further directory activation — the design's Stage 6 — follows this one directory at a time,
and is not part of this action.

## Done when

The relation vocabulary and its one-question test are contracted, `handbook/` carries edges
authored from the ledger's accept lines within the agreed per-file cap, unit tests cover
the parser, and `python3 automation/reconcile/reconcile.py --check` plus
`python3 automation/run_tests.py` both pass with real output recorded in the task's
`verification.md`.
