# Is the revised edge-graph architecture right, and which of its eight options do you pick?

**Status:** waiting
**Filed:** 2026-07-25, by claude, from chat — design session for `docs/designs/markdown-edge-graph.md`
**Action:** approve the revised architecture and answer decisions N1 to N8, or request a named change
**Full context:** `docs/designs/markdown-edge-graph.md`
**Resolution evidence:** `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`
**Why-you-might-care:** A measurement reversal means mining git history — not declared links — is now the cheap half that ships first, and decision N1 decides whether it gets to prove the schema unnecessary before the schema is built.
**If-you-do-nothing:** Nothing is built and no pre-existing file changes; the design and its decision list stay proposals.
**Review target:** `docs/designs/markdown-edge-graph-decisions.md`
**Review revision:** sha256:f66ef620df17a07499d9389df1626f3ea01b00cf7a9cc9321e91d006976c27af
**Reviewed revision:** sha256:f66ef620df17a07499d9389df1626f3ea01b00cf7a9cc9321e91d006976c27af
**Review outcome:** approved
**Blocks at:** transition:start-markdown-edge-graph
**Until then:** Both artifacts remain documentation; no checker, template, contract, or existing markdown file changes.

## What you need to know

An earlier review of the v1 direction was approved in chat, together with a redirect: keep
links one-directional, make a CLI-generated graph artifact the core mechanism, generate
recommended actions when a file changes, gate with tests, and accept that agents forget so
long as a retry loop converges. That approval is recorded in the two answered decision items
alongside this one. Since the reviewed artifact was rewritten rather than amended, the earlier
binding was retired rather than falsely re-pointed at bytes you have not seen. The revision
under review also corrects a rejected conclusion: co-change mining was dismissed on a
precision figure measured against the wrong reference set, and re-measurement showed textual
mention and real coupling are roughly 95% disjoint here, so mining is now layer zero.

## Differences

Approving accepts a feature whose blocking checks validate only structure, whose freshness
signal is derived from git rather than stored, and whose completeness is permanently partial
and says so in every answer. The most consequential single option is N1: whether to ship the
mined co-change layer plus anchor validation first and let a written experiment decide whether
the typed schema earns its place, or to build the schema directly.

## Example

If N1 is answered yes, the next session ships about 200 lines that need no annotation and no
migration, then records for two hot files whether each top-ranked mined coupling is real and
whether a hand-authored edge would add anything to the mined pair plus its shared commit
subjects. A sufficient mined list stops the project there, having spent an afternoon. If N1 is
answered no, the next session begins with the vocabulary, parser, and tests, and the schema's
value is judged after it exists.

**Your review:** Approved, with two named modifications. *Agent transcription by claude of
the owner's chat instruction on 2026-07-25 — a paraphrase of intent, not the owner's words.*
The owner wrote answers to N1 through N8 by hand into the review target and then directed
this session to build an execution plan and implement the most important pieces. N1, N2, N3,
N4, N6, and N8 take the recommended answer. **N5 is modified:** all three freshness
mechanisms must exist — derived each run, an absolute re-review window, and advisory-only —
configurable per folder independently, defaulting to a review window of 7 days. **N7 is
modified:** the per-file edge cap stands, but a file may exceed it when the agent supplies a
written justification naming both why that file needs to go beyond the cap and why decoupling
it would be worse. The owner's own answer lines are committed to the review target unaltered
in the commit that follows this fold.
