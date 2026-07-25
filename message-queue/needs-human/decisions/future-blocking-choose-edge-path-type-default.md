# Should a document edge default to a repo-root path instead of a relative one?

**Status:** folding
**Filed:** 2026-07-25, by claude, from chat — design session for `docs/designs/markdown-edge-graph.md`
**Action:** confirm the repo-root default, or keep the relative default you specified
**Full context:** `docs/designs/markdown-edge-graph-decisions.md`
**Resolution evidence:** `memory/decisions/2026-07-25-document-edge-path-types.md`
**Why-you-might-care:** A relative default requires the checker to rewrite paths whenever a file moves, and this repository's rename detection is measurably unreliable, so a wrong guess would silently repoint a correct link.
**If-you-do-nothing:** No path-type vocabulary is fixed and no checker is written; the proposal stays documentation only.
**Blocks at:** transition:start-markdown-edge-graph
**Until then:** The design and its decision list remain proposals; no checker, template, or contract changes.

## What you need to know

You specified that edges use relative paths by default, with absolute paths only when asked
for, and that the path type is always written out explicitly. The explicit marker is kept
either way, and so are all five types — including `outside-repo` for targets such as
`~/tmp/notes.md` and `logical-id` for targets whose path encodes mutable state. Only the
*default* is in question. Two measurements argue against relative: this repository already
uses 451 backticked repo-root references versus 4 relative markdown links, and relative
targets must be rewritten when a file moves, which needs git rename detection that misses
15% of this repository's real moves.

## Differences

The choice is about who absorbs the cost of a file moving. A repo-root target only breaks
when the *target* moves, and the fix is a plain path edit. A relative target also breaks
when the *declaring* file moves, and fixing it automatically requires the checker to guess
which move happened — where a false guess rewrites a correct path to point somewhere else.

## Options

### Option A — `repo-path` default, `file-relative` still available
Edges name targets from the repository root, in backticks, matching how this repository
already writes almost all of its cross-references. No path rewriting machinery exists, so
no rename-detection guess can corrupt anything.
*Example consequence:* A design doc declares `` `handbook/git-workflow.md` `` and keeps
working when the design doc itself is moved to another folder; the link does not render as
a clickable relative link on GitHub, which is how this repository's other 451 references
already behave.

### Option B — `file-relative` default, as originally specified
Edges name targets relative to the declaring file, which renders as a working clickable
link on GitHub. The checker must re-relativize on moves, or accept that moving a declaring
file breaks all of its edges at once.
*Example consequence:* Moving one design doc into a subfolder invalidates every edge it
declares; the repair is either mechanical guessing that can misfire, or a manual pass.

## Recommendation

Option A — keep the explicit marker and all five types, change only the default, because
relative paths buy rendering and cost a correctness risk this repository's history shows is
real.

**Your answer:** Option A — the repo-root default is approved, keeping the explicit
path-type marker and all five types.
