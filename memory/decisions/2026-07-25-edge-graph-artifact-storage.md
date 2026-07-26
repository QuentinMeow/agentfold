# The edge graph is generated on demand; nothing derived is tracked until a stated threshold

**Status:** decided
**Date:** 2026-07-25
**Decided-by:** human (explicit queue answer recorded in commit 5d315f9, claimed in 1a54c4c)
**Description:** Amends N6 of the edge-graph architecture decision: no generated graph projection is committed, gated, or ignored, so the six Stage 3 mechanisms are not built for a graph measured at 17 of 172 in-scope files (9.9%, about one tenth), and committing is recorded as not implemented rather than rejected, returning when declared edges exceed 100 and span more than half the in-scope files or when rendered in-edges become part of a real review workflow
**Review-by:** 2027-03-22

## Context

`memory/decisions/2026-07-25-markdown-edge-graph-architecture.md` recorded the owner's
answer to question N6: commit the generated graph as one text projection, marked
generated, verified byte-exact, with conflicts resolved by regeneration rather than by hand
merging. That ADR is decided and immutable, so this file amends it rather than editing it.

Stage 0 of `docs/designs/markdown-edge-graph.md` then measured how much graph there
actually is. The mined candidate set covers **17 of 172 in-scope markdown files (9.9%,
about one tenth)**; the other ninety percent of the repository produced no coupling above
the floors at all, so a committed projection today would be a mostly empty file describing
one subsystem — the eleven queue and workflow contracts that one task rewrote twelve times.
Against that, Stage 3 as designed is six separate mechanisms to build, test, and maintain:
a generator whose output is tracked, a byte-exact gate that makes any disagreement
unmergeable, a determinism suite including a run from a fresh clone in a different
directory with a different timezone, locale, and hash seed, a `.gitattributes` entry
marking the file generated, a writer refusal rule for index-versus-worktree disagreement,
and a regenerate-on-conflict merge procedure that is manual by construction because merge
drivers and union merge are both ruled out. The measurement was put back to the owner as a
commit-or-generate decision.

The owner answered, verbatim:

> choose B for now, but keep A in mind (or mark as not implemented), we might review it
> later.

## Decision

**Nothing generated is tracked.** The graph is emitted on demand. The join and impact
queries read the `## Edges` sections in the source files directly, so every fact has
exactly one home. No projection is committed, no projection is git-ignored, and no
generated file sits at a fixed path where a stale copy could silently answer for a
different commit. The artifact's format and query surface are not restated here; they live
in `docs/designs/markdown-edge-graph.md`.

**Stage 3 is struck, and its six mechanisms are recorded as not implemented — deferred,
not rejected.** No tracked generator output, no byte-exact gate, no determinism suite
including the foreign-environment run, no `.gitattributes` generated marking, no writer
refusal rule, and no regenerate-on-conflict merge procedure. Determinism rules still bind
whatever on-demand output exists, because reproducible output is cheap; what is deferred is
the machinery that exists only to police a second stored copy.

**The revisit threshold is a number, written down rather than left to judgment.**
Committing returns as a new decision **when declared edges exceed 100 and span more than
half the in-scope markdown files — 86 of the 172 measured today — or when in-edges
rendered without running a command become a real part of someone's review workflow.**

**What this supersedes, precisely.** In the architecture ADR it supersedes exactly N6 —
the committed byte-exact text projection and the regenerate-on-conflict resolution that
went with it — and nothing else. N1 (mine first), N2 (the three-way join), N3 (the
non-optional ledger), N4 (`references` reinstated as graph-only), N7 (the per-file edge cap
with its two-part justified exception), and N8 (retry closure plus discharged-by-filing)
all stand exactly as decided. N5 is amended separately by
`memory/decisions/2026-07-25-edge-graph-freshness-modes-after-measurement.md`.

## Alternatives considered

- **Option A — commit the artifact, byte-exact verified, as answered in N6.** Not
  rejected: deferred and revisitable at the threshold above. It lost now because the six
  mechanisms are the plan's largest single cost and the graph they would protect spans 17
  of 172 files (9.9%).
- **Generate on demand and git-ignore the output.** Rejected for the reason the
  architecture ADR already gave: a stale ignored copy can silently answer for a different
  commit. Generating to ephemeral output has the same cost and none of that failure mode.
- **Commit the artifact without the byte-exact gate.** Rejected: the gate is what makes a
  second copy of a derived fact safe, so dropping it keeps the duplication and discards the
  only thing that justified it.
- **Defer with no stated threshold.** Rejected: the owner asked to keep Option A in mind,
  and a deferral triggered by recollection is not one.
- **Rewrite the N6 answer inside the architecture ADR.** Rejected: a decided ADR is never
  rewritten; a reversal is a new file linking the old one (`memory/AGENTS.md`).

## Consequences

**What is given up, stated plainly.** A bare clone answers "what depends on this" only
after a command runs. A pull request rendered by the hosting provider shows the declaring
side of an edge and never the receiving side, so a reviewer who reads only the rendered
diff sees half the change. Both were real arguments for N6; both are currently unused,
which is why they lose today and why the second half of the threshold names the moment
they stop being hypothetical.

**What is gained.** One home per fact and no maintenance cost: one diff per edge change
instead of two, no gate to keep green, no determinism suite to run in a foreign
environment, and no merge procedure to remember. The in-edge query the artifact would
accelerate is a `git grep` over the edge sections at the same order of magnitude the design
already measured for backticked path references.

**The reversal direction was part of the argument and should stay visible.** Going from
generate-on-demand to committed later is adding a generator output and a gate. Going from
committed to generate-on-demand later means deleting a tracked file that other tooling and
habits may already read. This decision keeps the cheaper direction open.

**The format measurement stays valid and stays deferred, not deleted.** The design's
comparison at 250 nodes and 400 edges — text projection at 56 KB and roughly 16k tokens,
chosen over pretty JSON at 198 KB and roughly 57k, with SQLite disqualified as an optional
CPython module that is not byte-reproducible — still answers the question of *which* format
to commit. It is simply not asked today. When the threshold above is crossed, that table is
the answer, not new work.

**Revisit trigger, restated as one checkable sentence.** Declared edges exceed 100 and
span more than 86 of the in-scope markdown files, or in-edges rendered without running a
command become a real part of someone's review workflow.
