# Should a document edge be authored on one side and the reverse direction derived?

**Status:** waiting
**Filed:** 2026-07-25, by claude, from chat — design session for `docs/designs/markdown-edge-graph.md`
**Action:** choose Option A or Option B, or state another model
**Full context:** `docs/designs/markdown-edge-graph-decisions.md`
**Resolution evidence:** `memory/decisions/2026-07-25-document-edges-are-authored-once.md`
**Why-you-might-care:** Every later choice about the edge schema, the checker, and the query tool follows from this one, and reversing it means rewriting every declared edge.
**If-you-do-nothing:** No edge schema exists and nothing is built; the proposal stays documentation only.
**Blocks at:** transition:start-markdown-edge-graph
**Until then:** The design and its decision list remain proposals; no checker, template, or contract changes.

## What you need to know

You asked for double-ended links whose metadata lives inside both markdown files, so that
each file states its side of the relationship. Measuring this repository says storing both
sides in the files is not achievable here: `tasks/AGENTS.md`, `message-queue/AGENTS.md`, and
`automation/AGENTS.md` each sit at exactly 60 of 60 lines permitted by the reconciler's
budget check, and the root `AGENTS.md` is referenced by 53 files with 21 lines of headroom,
so writing reciprocal blocks into targets produces a budget failure fixable only by deleting
contract prose. It would also mean one folder writing into another folder's files, against
this repo's isolation rule.

## Differences

Option A keeps the graph fully double-ended as a *checked invariant* — every edge is
visible from both ends through a generated index and a query command — but only one file
contains the authored text. Option B keeps your original shape literally, at the cost of
exempting the highest-traffic contracts from participating as targets, which excludes
exactly the files most worth linking.

## Options

### Option A — author once, derive the reverse
The file carrying the obligation declares the edge. One generated index holds the whole
graph in both directions, verified byte-for-byte, and a query answers "what depends on
this". Nothing is ever written into another folder's files.
*Example consequence:* You open `handbook/git-workflow.md` and it does not list its nine
dependents; you run the impact query, or read the generated index, and get all nine with a
reason and an update condition attached to each.

### Option B — author both sides, cross-check them
Both files declare the edge and the checker verifies the two sides use proper inverse
relations. Budgeted contract files (`AGENTS.md`, `SKILL.md`, root `README.md`) must be
exempted from receiving reciprocals, or their budgets must be raised — and those budgets
enforce a principle in `handbook/principles/progressive-disclosure.md`, so raising them is
itself a separate decision.
*Example consequence:* `services/quote-api/AGENTS.md` gains a `required-by` entry naming
`services/quote-cli`, making the dependency visible in place — but the arrangement inverts
the one-way dependency `handbook/principles/folder-as-a-service.md` deliberately creates,
and the same edge onto `tasks/AGENTS.md` cannot be written at all.

## Recommendation

Option A — it is what Backstage, Sphinx-Needs, DITA, and RFC 8288 each concluded
independently, and it is the only option that leaves this repository committable.

**Your answer:** Option A, strengthened. A bidirectional link is not preferred at all, so
links stay one-directional: only the forward direction (depends-on / reference) is ever
written in a file, and no depended-by side exists to author. A CLI generates the full graph
artifact instead, and that artifact is the core mechanism for finding relevant pieces.
