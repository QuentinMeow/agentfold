# Build the deferred edge-graph viewer in the order the evidence supports

**Status:** open
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** Whenever the deferred viewer is built, build a faceted node table first, then a local neighbourhood panel, then a directory-by-directory matrix — not a force-directed graph, and with no vendored JavaScript.
**Full context:** `docs/designs/markdown-edge-graph.md`
**Resolution evidence:** `roadmap/current-state.md`
**If unanswered:** No viewer exists. Edges are read in the files that declare them and through the join report, which is the state the owner deferred to.

## What you need to know

The owner deferred the viewer explicitly, and nothing measured since reopens it. This action
exists only so that a future session starting on it does not start on the wrong thing — the
constraints below are evidence-backed and were paid for once already.

**The order.** A faceted node table, then a local neighbourhood panel implementing
search-then-expand-on-demand, then a directory-by-directory matrix, which is the view that
answers "which folders depend on which".

**Not a force-directed graph.** Controlled studies find adjacency matrices outperform
node-link diagrams on most tasks above roughly twenty vertices, with path finding the
consistent exception. This repository is around 250 nodes — 244 tracked markdown files
today — twelve times that threshold. Practitioners of the closest comparable tool report the
global view becoming useless as the corpus grows, and using only the local neighbourhood
view.

**No vendored JavaScript.** The generator can precompute a layered layout in Python and emit
coordinates, leaving the page as static markup. Vendoring several hundred kilobytes of
minified JavaScript into a repository whose rule is no dependencies would be a dependency
wearing a costume, and it would be the largest file in the repository by an order of
magnitude.

One scoping note from Stage 0: the mined candidate set currently spans 17 of 172 in-scope
markdown files, so a global view has little to show until declared edges cover materially
more of the repository. The neighbourhood panel is useful long before the matrix is.

## Done when

A viewer exists whose first three views are the table, the neighbourhood panel, and the
directory matrix, its page loads with no external script or network request, its layout is
computed by the generator rather than in the browser, and the task's `verification.md`
records the real output of generating it.
