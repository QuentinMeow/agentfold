# Commit the generated edge-graph artifact as answered, or generate it on demand?

**Status:** waiting
**Filed:** 2026-07-25, by claude, from the Stage 0 gating experiment of the mined co-change layer — `docs/designs/markdown-edge-graph.md`
**Action:** keep the committed byte-exact artifact as answered in N6, or generate it on demand and name the size at which committing is revisited
**Full context:** `memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`
**Resolution evidence:** `memory/decisions/2026-07-25-edge-graph-artifact-storage.md`
**Why-you-might-care:** Committing the artifact is the single most expensive stage in the plan — six separate mechanisms — and the measured graph it would serve currently spans 17 of the repository's 172 in-scope markdown files.
**If-you-do-nothing:** No graph artifact is generated or committed, and in-edges stay answerable only by running a command; at the named boundary the storage question cannot be deferred any further and the artifact work stops there.
**Blocks at:** transition:start-edge-graph-artifact
**Until then:** No artifact is generated, committed, or git-ignored. Relationships are read in the files that declare them.

## What you need to know

You answered question N6 with: commit the generated graph as one text projection, marked
generated, verified byte-exact, with conflicts resolved by regeneration rather than by hand
merging. That answer is recorded in
`memory/decisions/2026-07-25-markdown-edge-graph-architecture.md`, and this item asks you to
keep or amend it now that Stage 0 has measured how much graph there actually is.

The mined candidate set covers **17 of 172 in-scope markdown files**. The other 90% of the
repository produced no coupling above the floors at all, so a committed projection today
would be a mostly empty file describing one subsystem — the eleven queue and workflow
contracts that one task rewrote twelve times.

Against that, Stage 3 as designed is six mechanisms, each of which has to be built, tested,
and maintained: a generator, a byte-exact gate that makes any disagreement unmergeable, a
determinism suite including a run from a fresh clone in a different directory with a
different timezone, locale, and hash seed, a `.gitattributes` entry marking the file
generated so the hosting provider collapses its diff, a writer refusal rule for the case
where a file the generator reads differs between the index and the worktree, and a
regenerate-on-conflict merge procedure. The design also rules out defining a merge driver
(driver definitions live in untracked local config, so fresh clones, CI, worktrees, and
server-side merges all silently fall back to the default) and rules out union merge (it
resurrects deleted entries), so the merge procedure is manual by construction: resolve
source conflicts, stage them, regenerate, stage the artifact.

The query the artifact exists to accelerate is already cheap without it. The in-edge
question — "what depends on this file" — is a `git grep` over the edge sections in the
source files, at the same order of magnitude the design already measured for backticked
path references. The three things committing genuinely buys are real but currently unused:
a bare clone answers in-edge questions with no command run, the hosting provider renders
in-edges so they reach a human reviewer who never runs anything, and the diff shows the
semantic consequence of an edge change during review.

The design's own text already contains the escape hatch: *"if the artifact ever grows past
a few hundred KB, revisit and move to build-not-commit."* This item proposes running that
rule in the other direction while the graph is small.

## Differences

The choice is where a derived fact is allowed to live a second time, and who pays for
keeping the two copies identical. Committing makes disagreement between source and
projection unmergeable rather than merely unlikely — that is what makes a second copy safe —
but the price is six mechanisms and two diffs per edge change, paid now, for a graph that
covers a sixth of the repository. Generating on demand keeps exactly one home for every
fact and costs nothing to maintain, but a bare clone and a provider-rendered pull request
both answer nothing about in-edges until someone runs a command, and a reviewer who reads
only the rendered diff sees the declaring side of an edge and never the receiving side.

The reversible direction matters here. Going from generate-on-demand to committed later is
adding a generator output and a gate. Going from committed to generate-on-demand later
means deleting a tracked file that other tooling and habits may already read.

## Options

### Option A — commit the artifact, byte-exact verified, as answered in N6
One generated text projection is tracked, gated byte-exact, marked generated in
`.gitattributes`, and resolved on conflict by regeneration. All six mechanisms are built as
part of the stage.
*Example consequence:* A reviewer opening a pull request that changes one edge sees two
diffs — the `## Edges` block in the source file and the corresponding lines in the
projection — and the second is collapsed by default. Anyone cloning the repository can read
in-edges immediately. A session that edits an edge and forgets to regenerate cannot commit
until it does, and a merge that touches two edges is resolved by regenerating rather than by
hand.

### Option B — generate on demand, and revisit committing at a stated threshold
Nothing generated is tracked. The join and impact queries read the edge sections in the
source files directly. The threshold for revisiting is written into the decision record
rather than left to judgment: **when declared edges exceed 100 and span more than half the
in-scope markdown files — 86 of the 172 measured today — or when in-edges rendered without
running a command become a real part of someone's review workflow.**
*Example consequence:* A reviewer sees exactly one diff per edge change, and the receiving
side of an edge is found by running the impact query. A bare clone answers "what depends on
this" only after `python3` runs. When the repository later crosses the stated threshold, the
question returns as a new decision with real coverage numbers behind it instead of a
projection of them.

## Recommendation

Option B, with the threshold stated above written into the decision record so that
revisiting is triggered by a number rather than by someone remembering. As with the other
open amendment, choosing B means a new ADR that records the measurement and links
`memory/decisions/2026-07-25-markdown-edge-graph-architecture.md` as the record it amends,
because a decided ADR is never rewritten. The case for B is that the six mechanisms are the
plan's largest single cost, the graph they would protect currently spans 17 of 172 files,
and the direction B forecloses is the cheaper one to reverse.

**Your answer:** choose B for now, but keep A in mind (or mark as not implemented), we might review it later.

<!-- A concrete response is immutable. If it is a counter-question, fold the answer into
Resolution evidence and create a same-timing successor with **Supersedes:** `<this path>`. -->
