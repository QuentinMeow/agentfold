# Detect restated rule text across contracts without relying on co-change

**Status:** open
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** Build a lexical duplication detector that reports near-identical rule text repeated across markdown contracts, using the text itself rather than git history as its signal.
**Full context:** `docs/designs/markdown-edge-graph.md`
**Resolution evidence:** `automation/AGENTS.md`
**If unanswered:** Duplicated rule text stays invisible unless its copies happen to co-change, and single-sourcing stays a manual reading exercise that nobody performs on a schedule.

## What you need to know

This mechanism is separate from mining because of a limitation the gating experiment ran
straight into. Mining found the fivefold restatement of the queue delivery-prefix rule —
five templates carrying a byte-identical comment, none naming its owner — **only because
those five files co-change with the contract that owns the rule**. Co-change is the entire
signal. A restatement that has never once been edited in the same commit as its owner
produces no support and no confidence at all, and is invisible to the miner no matter how
long the history grows. Worse, the failure mode is silent: the report says nothing, which
reads identically to "nothing is duplicated".

The same experiment showed why that class matters. A restatement's correct disposition is
usually **deletion**, not a declared edge: replacing the duplicated text with a link to its
owner single-sources the fact, removes the coupling entirely, and brings the reference
inside `link-check`'s reach — whereas declaring an edge preserves the duplication and adds a
permanent maintenance duty on top of it. The design's own rejected list already concluded
that declaring duplication needs lexical detection instead.

Two constraints carried from Stage 0's experience. The detector reads rendered prose, not
raw bytes, so fenced code blocks and HTML comments cannot manufacture matches the reader
never sees — `automation/markdown_semantics.py` already supplies that blanking pass.
And it needs the same durable accept/reject ledger discipline the miner uses, because an
intentional restatement dismissed once must never re-surface.

## Done when

One command reports near-identical rule text repeated across two or more markdown files
with the location of each copy, the report reproduces the five-way queue-template
restatement it was designed against, a dismissal is durable, and
`python3 automation/run_tests.py` passes with real output recorded in the task's
`verification.md`.
