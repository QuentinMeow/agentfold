# A document edge names its target from the repository root by default

**Status:** decided
**Date:** 2026-07-25
**Decided-by:** human (explicit queue answer recorded in commit 2abead8)
**Description:** Document edges default to a repo-root target path, keep the explicit path-type marker on every edge, and keep all five path types the design defines
**Review-by:** 2027-01-26

## Context

The proposed markdown edge graph (`docs/designs/markdown-edge-graph.md`, with the
owner-facing summary in `docs/designs/markdown-edge-graph-decisions.md`) records how one
document's edge names its target. The owner had originally specified relative targets by
default, with absolute targets only on request and the path type always written out.

Two measurements argued the other way. This repository already writes 451 backticked
repo-root references against 4 relative markdown links, and a relative target must be
rewritten whenever the *declaring* file moves — which needs git rename detection that
misses 15% of this repository's real moves, so a false guess would silently repoint a
correct link.

## Decision

A document edge names its target from the repository root by default. The explicit
path-type marker stays mandatory on every edge, and all five path types the design defines
stay in the vocabulary — including the two that exist precisely because a repo-root path
cannot express them. The design document remains the single home of the vocabulary and the
record schema; this decision fixes only the default and the marker.

## Alternatives considered

- Keep the relative default as originally specified — rejected because it buys GitHub link
  rendering at the cost of a correctness risk this repository's rename history shows is
  real, and the automatic repair requires a guess that can rewrite a correct path.
- Drop the explicit path-type marker and infer the type from the target string — rejected
  because it was never in question: an inferred type turns an unresolvable target into a
  silent reclassification instead of a finding.
- Reduce the vocabulary to repo-root paths only — rejected because targets outside the
  repository and targets whose identity survives `git mv` have no repo-root spelling.

## Consequences

An edge breaks only when its *target* moves, and the repair is a plain path edit with no
rewriting machinery to get wrong. Edges do not render as clickable links on GitHub, which
matches how the repository's other 451 cross-references already behave.

**One narrow budget concession follows, and its scope is exactly this.** When a directory
is activated, the `agents-budget` line count must exclude the lines of that file's `## Edges`
section and nothing else, because three leaf contracts already sit at exactly 60 of 60
permitted lines and would otherwise be unable to declare an edge at all. The concession is
admitted only for the `## Edges` section of a file inside an activated directory, only for
the line-budget count, and only because those lines are machine-read records rather than
the curated prose the budget exists to ration
(`handbook/principles/progressive-disclosure.md`). It grants nothing to any other section,
any other check, or any other kind of metadata; a later proposal that wants prose, a table,
or a different generated block exempted from a budget needs its own decision and may not
cite this one as precedent.

Revisit if git rename detection becomes reliable enough that relative targets can be
repaired mechanically, or if edge targets start needing to render as links for a human
audience.
