# Repair the handover projection so a code-spanned queue field can be copied

**Status:** open
**Filed:** 2026-07-25, by claude, from the end-of-session handover of the markdown edge graph Stage 0 work — `docs/designs/markdown-edge-graph.md`
**Action:** Normalise both sides of the handover projection's context comparison so an inline code span in a queue item's Why-you-might-care or If-you-do-nothing field can be copied into a handover entry, then commit the blocked session's handover at a fresh conversation path.
**Full context:** `history/AGENTS.md`
**Resolution evidence:** `automation/reconcile/reconcile.py`
**Blocks now:** operation:session-handover

## What you need to know

The expected context is built from the queue item's raw field bytes, which keep their
backticks. The handover entry it is compared against is read through a helper that blanks
every closed code span, delimiters included. The two sides differ by exactly the code spans,
so the entry is reported as not copying the creation-snapshot fields, and no handover text
can satisfy both: a backtick survives the stripping only when its run finds no closing run of
equal width, and the required literal is a closed pair by construction.

Five encodings were tried and all five failed against both comparison variants. The queue
item cannot be edited or deleted instead, because both fields sit inside the immutable action
identity and an unanswered human item cannot be resolved without a response. The exact
findings, the ruled-out escapes, and the live item that triggers it are recorded in task
2026-07-25-fix-handover-projection-code-span-copy.

This is not confined to one session. Every session's end-of-session handover is blocked for
as long as that item stays live, so the repair is the gate on the ritual itself.

## Done when

A new handover whose Needs your attention entry copies a code-spanned queue field passes
`python3 automation/reconcile/reconcile.py --check`, a regression test covers both fields and
fails against the pre-fix checker, and the blocked session's handover is committed at a fresh
conversation path.
