# Give decided ADRs the byte-integrity gate queue items and handovers already have

**Status:** open
**Filed:** 2026-08-18, by claude, from chat
**Action:** Add a check that refuses an edit to a decided record under `memory/decisions/` other than the lineage fields and `Review-by` bump `memory/AGENTS.md` allows, computed over raw bytes rather than a subtractive parse view.
**Full context:** [the memory contract that declares records immutable](memory/AGENTS.md)
**Resolution evidence:** `automation/reconcile/reconcile.py`
**If unanswered:** Nothing stops. Decided ADRs stay editable without any check noticing, exactly as they are today, and the queue and handover gates keep holding their own record classes.

## What you need to know

`memory/AGENTS.md` states that a decided ADR is never rewritten: adding `Superseded-by`,
`Amends`/`Amended-by`, and bumping `Review-by` are the only edits one may receive. Nothing
enforces it. Measured on this branch, in a throwaway clone with the hook installed, by
appending to `memory/decisions/2026-07-22-bold-key-frontmatter.md` and running the gate:

| appended at end of file | `reconcile --check` |
|---|---|
| visible prose | 0 blocking |
| HTML comment | 0 blocking |
| fenced block | 0 blocking |
| indented code | 0 blocking |

The same probe under `--check --range <base>...<head>`, with the append committed, is also
0 blocking. For comparison, the identical HTML-comment append to a handover is refused by
`handover-queue-projection` ("handover record was modified after queue-projection
adoption"), and to a live queue item by `queue-frozen-skeleton`.

So the gap is not the one the original finding described. That finding was about an
identity view being *subtractive* — computed over `semantic_text`, which blanks comments,
fences and indented code, so those could be appended invisibly. `queue-frozen-skeleton`
closed that for queue items on this branch, and its totality is asserted by a test. What
remains is narrower and blunter: for `memory/decisions/` there is no integrity check at
all, and the boot sequence sends every agent to read that folder.

A byte-exact freeze is the wrong shape on its own, because it would refuse the three edits
the contract explicitly permits. The queue's own repair is the model: freeze a skeleton of
raw lines and let a named, closed set of mutable fields carry their exposed values.

## Done when

An edit to a decided ADR that is not one of the permitted lineage edits is a blocking
finding, the permitted edits are proved legal by tests, and appending an HTML comment,
a fenced block, or an indented block to a decided ADR is refused with real output recorded.
