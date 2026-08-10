# Design notes — Stop indented prose from hiding from every repository check

**Status:** decided

## Problem

`strip_indented_code` in `automation/markdown_semantics.py` blanks a line whenever it
begins with four spaces or a tab. CommonMark blanks far fewer lines than that. An
indented code block cannot interrupt a paragraph, and inside a container the code
threshold is measured from the container's content column, not from column zero. So the
two most ordinary shapes in this repository's records — a wrapped paragraph and a
continuation line under a list item — are prose a human reads and a blank line every gate
reads.

`semantic_text` composes `strip_indented_code`, so the blind spot is inherited by the
reconciler, the core-scope gate, and the action-projection gate;
`automation/check_action_projection.py` applies it a second time to an explicitly
rendered-human view. Three consequences were reproduced end to end (transcripts in
`verification.md`): a live queue item can be rewritten without tripping
`queue-resolution`, an unqueued human ask in a task record escapes `task-action-origin`,
and `link-check` misses a broken link one level inside a list. `task_tokens`,
`task_status_references`, `human_header_block`, `human_attention_above_fold`,
`field_counts`, `section_body` and `level_two_section_body` read the same view and are
blind in the same way.

The constraint that makes this delicate is symmetric. Blanking too much hides prose, which
is the bug. Blanking too little turns a genuine code example into evidence, and every path
or field inside one would then satisfy a structural check — the exact failure
`strip_indented_code` exists to prevent. The change has to move the line to where
CommonMark draws it, not merely to a place where the reported cases pass.

## Options considered

### Option A — Interim: require a preceding blank line and no open list item

Blank a four-space line only when the previous line is blank and no list item is open.
Two lines of state, no container model. It fixes both reported shapes: `- a` followed by
`    text` keeps `text` because an item is open, and `para` followed by `    text` keeps
`text` because the previous line is not blank.

Its cost is that it stops recognising indented code that really is indented code inside a
list item. `- a`, blank, then six spaces of `code` is a code block by the spec and would
now be read as prose, so a path inside a step-by-step list's own code example becomes a
live link claim. That is a new false-positive class introduced by the fix, in a repository
whose plans and skills are mostly numbered lists with indented examples.

### Option B — Correct: track paragraph state and the open list item's content column

Walk the lines once, carrying two pieces of state: whether an open paragraph would swallow
the next line, and the stack of content columns of the list items currently open. A line
is code when its indentation is at least four columns past the innermost open item's
content column and no paragraph is open. Block-quote lines keep their current treatment
(never blanked) and only update paragraph state, so this change cannot alter how quoted
source is read.

Everything the interim route gets right, this gets right for the same reason, and the
list-item code block stays code because the threshold moves with the container instead of
disappearing.

## Chosen

Option B. The interim route trades one blind spot for one false-positive class, and the
false-positive class lands on the most common shape in `plan.md`, `SKILL.md`, and the
handbook: a numbered step with an indented example under it. Nothing about the correct
route turned out to be out of reach — it is a single-pass walk over lines that were
already being walked, with a list of integers and one boolean added.

Two deliberate limits, both stated in the new docstring:

- A line carrying its own list marker is never blanked, even in the one shape where
  CommonMark would (`-` followed by five or more spaces and then text, which opens the
  item with an indented code block). That shape is vanishingly rare, and preserving the
  current answer for it keeps the change strictly about continuation lines.
- Block-quoted lines keep their existing treatment: a line whose first non-space character
  is `>` was never blanked and still is not. Blanking indented code inside a quote is a
  separate widening with its own risk of hiding quoted prose, and this task is about
  over-blanking.

**On reusing `section_entries`.** The brief suggested reusing both
`check_action_projection.indentation_width` and `section_entries`. `indentation_width` is
reused: it moves into `automation/markdown_semantics.py`, `check_action_projection.py`
imports it, and there is exactly one implementation of CommonMark column arithmetic.
`section_entries` is deliberately not rewired. It answers a different question — which
top-level list entries a "What to review" section contains — and its content-indent
arithmetic (`indent + len(marker) + width(spacing)`) is not the CommonMark rule: it ignores
the clause that pins the content column to `marker end + 1` when the marker is followed by
five or more spaces or by nothing. Sharing one function would silently change which
continuation lines belong to a projection entry, which is a behaviour change to the
pull-request boundary check with no bug behind it. The shared piece is the column
arithmetic; the rule that consumes it stays where its contract is.

## Core fit

**Agent substitution:** pass — the change is a pure text-view function in the repository's
own Python; no agent runtime supplies, configures, or observes it, so any runtime running
the same gates gets the same verdict.
**Provider substitution:** pass — `strip_indented_code` reads Markdown bytes only. It
never consults GitHub or any other provider, and the gates that call it keep their
existing provider adapters unchanged.
**Repository substitution:** pass — every adopted repository writes Markdown records, and
in every one of them a list-item continuation line is prose a human reads. An adopter
whose records use indented continuations is exactly the adopter whose queue items,
task records, and links are currently unchecked.
**User-global writes:** none
**Why AgentFold core:** `automation/markdown_semantics.py` is the shared view three
tracked gates read their evidence through. The invariant being restored — a check sees
what a human sees — is the harness's own guarantee, not local configuration, not product
behaviour, and not something an overlay could hold, because the false answer is produced
inside core and inherited by everything downstream.
**Thin adapter:** none
