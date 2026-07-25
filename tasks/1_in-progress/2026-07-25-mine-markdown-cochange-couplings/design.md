# Design notes — mine markdown co-change couplings and validate heading anchors

**Status:** decided

## Problem

The architecture is already settled in `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`,
so this task chooses nothing about edges, vocabulary, or freshness. Three narrower choices
were still open, and each of them decides where code and state live:

1. Where the mined co-change layer runs. The design describes it as "one reconciler check
   of roughly 120 stdlib lines", which would make it a `CHECKS` entry.
2. Where the accepted/rejected ledger lives, given that it has to outlive every agent that
   writes to it and stay readable on a bare clone.
3. How heading-anchor validation reaches the existing link check without changing what that
   check already reports.

The files this task creates, none of which exist yet:

```
automation/mine_cochange.py             the mining and ledger CLI
automation/cochange-ledger.txt          the append-only verdict ledger
automation/tests/test_mine_cochange.py  CLI unit tests
automation/tests/test_reconcile_links.py  anchor-validation unit tests
```

## Options considered

### Option A — mining as a reconciler `CHECKS` entry

What the design text suggests. Every finding in `automation/reconcile/reconcile.py` blocks
the commit, because findings carry no severity yet — that is exactly the gap the separate
backlog task 2026-07-22-severity-tiers-for-reconciler-findings exists to close. A mined
coupling is a suggestion with a measured false-positive rate in the 10–25% band that the
design's own governance rules call "probation". Shipping suggestions through a blocking gate
converts an advisory into ~2 hard stops per fifth commit, which is the failure mode the
rejected digest-pin mechanism died of. There is a second cost: a whole-history `git log` walk
inside a check is quadratic here, because `check_task_admission_history` re-enters the check
registry once per admitted Git edge under `git_revision_candidate`.

### Option B — mining as a standalone advisory CLI (chosen)

A separate `automation/` tool whose report verb always exits 0. It runs when an agent or CI
asks for it, walks history once, and costs the pre-commit path nothing. The reconciler keeps
its ~5-second budget and its property that every finding is structural. The advisory tier
can move into the reconciler later, without rewriting the miner, once severities exist.
Honest cost: an ignored advisory leaves no trace in the repository until repair-item filing
exists, and repair-item filing is deferred past this task.

### Option C — ledger under `memory/`

The ledger is durable project knowledge, so `memory/` is the obvious home. It is the wrong
one. Entries there carry `Review-by` dates and are re-verified, compacted, or deleted by the
memory-gardener pass; a rejected coupling is a permanent verdict, not an expiring fact.
Machine-appended rows would also churn `memory/index.md` on every dismissal.

### Option D — ledger as a tracked text file beside the tool (chosen)

`automation/core-scope-paths.txt` is the standing precedent: a tracked, plain-text data file
that lives next to the gate that reads it, with no schema ceremony and no expiry. The
ledger follows it — append-only, one line per verdict, diffable, and present on a bare
clone. The rejection count is then a `wc`-able number rather than a derived query, which is
what makes the governance threshold self-measuring.

### Option E — anchor validation as a new check versus inside `check_links`

A new check id would report anchors separately from paths, and would double the work of the
`live_markdown_files` walk. The hole is inside `check_links` itself:
`re.fullmatch(r"[\w./-]+", cand)` rejects any candidate containing `#`, so today a link
whose path *and* anchor are both wrong produces no finding at all. Fixing it where it broke
keeps one check id — which matters, because retry filenames embed check ids
(`memory/lessons/automation/deterministic-finding-keys.md`) — and it makes the fix a strict
increase in what `link-check` catches rather than a new surface.

## Chosen

Option B, Option D, and Option E. Mining is a standalone advisory CLI with a
report verb that always exits 0; its ledger is an append-only tracked text file beside it;
anchor validation lands inside the existing `check_links` and keeps the `link-check` id.

The fragment half reuses `semantic_text` from `automation/markdown_semantics.py`, so fenced
code blocks and HTML comments cannot donate headings the renderer never emits — the same
blanking pass the rest of the reconciler already trusts. Slugs follow GitHub's algorithm
because that is the renderer every reader of this repository actually uses.

Nothing here is a one-way door under `handbook/collaboration-modes.md`: no `templates/`
schema changes, no `handbook/principles/` file changes, no dependency added, and both new
files can be deleted without migrating anything. The one-way-door decisions this stage
depends on are already recorded as ADRs.

## Core fit

**Agent substitution:** pass — the report is derived from the repository's own Git history by a stdlib script and a tracked ledger file, so any runtime that can run `python3` and `git` reproduces the same ranked pairs and the same verdicts; nothing depends on a model, a prompt, or one agent's recollection
**Provider substitution:** not-applicable — both halves read the local Git object store and the working tree, and no hosting provider supplies, gates, or versions either input; CI merely invokes the same local commands
**Repository substitution:** pass — every adopted repository accumulates markdown whose real dependencies are recorded nowhere and whose cross-file heading links rot silently; the miner learns its couplings from that repository's own history, and the floors are flags rather than constants fitted to this one
**User-global writes:** none
**Why AgentFold core:** `check_links` is the mechanism that keeps this framework's file-based coordination honest, and its `#`-fragment blind spot means a contract can cite a heading that no longer exists and no gate notices; the miner is the evidence source that decides whether the declared-edge schema is ever built, so keeping it in a private overlay would move the harness's own next design decision out of the repository that has to live with it
**Thin adapter:** none

## The gating experiment

Step 9 of `plan.md` is what makes this stage falsifiable, and its result is written back
into this section. For the two hottest markdown files, each top-ranked coupling gets two
recorded judgments: whether it is a real dependency, and whether a hand-authored edge would
have said anything the mined pair plus its shared commit subjects did not. A finding that
the mined list is already sufficient ends the project at Stage 1 — the advisory is then the
whole feature, and the typed schema, the artifact, the join, and the viewer are all
unjustified. The verdict is empty until the experiment runs.

One limitation applies to every number the experiment produces. This repository holds four
days of history and roughly 107 in-scope markdown-touching commits, while the published work
this technique borrows from discards the first few hundred change records as warm-up. Every
support, confidence, and precision figure is therefore provisional and will move as history
grows, in a direction nobody can predict from here. Mining is also indifferent to quality:
it learns established bad practice as readily as good, so a reported coupling may be a
duplication worth removing rather than a dependency worth declaring.
