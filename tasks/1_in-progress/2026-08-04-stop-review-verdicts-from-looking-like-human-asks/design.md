# Design notes — stop completed review verdicts from looking like human asks

**Status:** decided

This file described the first implementation, which
`memory/decisions/2026-08-07-withdraw-the-first-review-receipt-implementation.md`
withdrew. Everything that decision names as out of scope — the closed character
alphabet, the 36-bin reviewer vector and its containment and edit-distance rules, the
composite claimant separators and their sixteen-component ceiling, the second
`adversarial panel` grammar, the raw-HTML container and Setext claimant rules, the
structural-versus-rendered agreement check, and the widened `block` vocabulary — is
gone from the code and from this file. What follows is the shipped design.

## Problem

The core-scope gate requires a completed review line shaped like
`- core-fit / reviewer: approve|block — finding`, but task admission reads the same
`approve` token as a new human command. The repair must recognize exactly the receipt
grammar the core-scope gate accepts while leaving reviewer and finding prose under the
ordinary human-action detector.

## Options considered

### Option A — exempt review receipts

Skip a matched receipt line, its section, or all of `verification.md`. This removes the
false positive, but a finding such as "owner please approve the release" becomes an
unqueued ask that task admission cannot see.

### Option B — neutralize only the structural verdict token

Share one receipt grammar between the two gates and replace only the matched `approve`
or `block` token with equal-width spaces before human-action classification. A completed
verdict is inert; the reviewer identity and the finding stay visible.

## Chosen

Option B, in the closed form recorded in
`memory/decisions/2026-08-04-review-receipt-parser-authorization.md`.

`automation/review_receipt.py` holds the whole grammar and both gates import it. A
receipt is one exact top-level `## Review verdicts` heading — no trailing text — then
one `**Reviewed revision:** <full commit id>` field as the section's first nonblank
line, then one or more `- core-fit / <reviewer>: <approve|block> — <finding>` lines.
Only blank lines separate those elements, and the block ends at the first other nonblank
line. Zero or several headings, a revision field that is not first, a second revision
field anywhere in the section, and a reviewer with no word character each refuse the
receipt.

A finding is `.+` — any nonempty prose. Constraining it was the fail-open the withdrawal
decision names: a rejected finding ended the receipt and dropped its verdict together
with every verdict after it.

Two regexes point in opposite directions, and the direction is the design. The acceptor
stays exact; widening it is how the withdrawn implementation grew. The rejector can only
refuse — whatever it newly matches becomes a reported error, never an accepted verdict —
so it is kept loose and, since the nineteenth panel, unbounded: searched anywhere in the
line rather than anchored, tolerant of any run of decoration around and inside
`core-fit`, of any dash, and of slash-like characters beyond ASCII. It locates `core…fit`
with a pattern and then looks for the slash by plain string search over the rest of the
line, which is linear and cannot backtrack, so no length limit is needed. It runs twice,
over the structural view and over the section's own raw lines, because the structural
view blanks fenced, commented, indented and HTML-wrapped lines before any rejector could
see them. Any error yields zero verdicts, so the core-scope gate reports it and the
action gate grants no exemption.

**Refusal-only is not the same as safe.** Both passes can only add an error, so widening
either is free — but that argument covers what they do, not what they fail to do.
Declining to refuse is permission. A pass that returns early, a bound that clips a run,
or a view that dropped a line before the pass ran are all fail-open, whichever direction
the pass itself points. A sixteen-character cap on the run before the slash was exactly
that: seventeen zero-width spaces produced a line visually identical to a canonical
verdict — the raw, rendered and structural forms all differ, but a reader sees no
difference and `normalized_action_tokens` returns the same tuple — that neither half
looked at. Nothing in the rejector is bounded now. Removing the bounds cost speed rather
than saving it, on some shapes by more than double, so coverage rather than cost is the
reason; the measurement is in `verification.md`. Bounding it again would be a coverage
decision to record, not an optimization to take.

**The rule, not an inventory.** Inside the receipt section, a line whose structural or
raw form the rejector matches and the acceptor does not refuses the whole receipt. A line
the rejector does not match still ends the block silently: the rejector is a pattern over
`core`, `fit` and a slash, not a judgement about what a writer meant, and no pattern of
that kind sees a shape that keeps none of those three.

Both gates call this parser, so it reaches the same verdict for whatever text each hands
it — though they need not hand it the same bytes, since the core-scope gate reads the
file through Git with universal newlines and the action gate decodes it without. That is
why the raw scan derives its line numbering from `commonmark_lines` rather than from a
newline split. Everything after that is each gate's own, and the two do diverge:
the core-scope gate applies claimant, identity, majority and revision-freshness rules the
action gate never sees, so a receipt this parser accepts can still be refused there and
neutralized here. The action gate for its part requires the artifact path and a rendered
line still carrying the verdict, and blanks nothing when either fails. Placement follows
the line number the parser recorded — never a scan from the top of the document, which
once let a superseded lookalike above the receipt absorb the blanking and lose seven
characters of its own text. That the parse view is structural is also why raw HTML
rendering as a heading cannot claim a receipt: `rendered_human_text` is never the parse
view, which its own docstring requires.

The exemption belongs only to a path matching `tasks/<status>/<task-id>/verification.md`
in full, because that is the artifact `--require-review` validates. A receipt in the
task's worklog, or in a verification record nested one directory deeper, gets ordinary
classification.

The claimant and reviewer identity comparison is `check_core_scope.identity_key`
unchanged: a case-folded, order-insensitive set of word tokens. The parser rejects a
reviewer that produces no such token, because that verdict would otherwise parse and
then vanish from the tally.

## Known residue

Stated as rules, because every earlier attempt to state it as a numbered list was
falsified by the next reviewer, and a closed list invites exactly that.

**A verdict the rejector cannot match ends the block in silence.** The rejector needs
`core`, then `fit` after any run of non-letters, then a slash-like character anywhere
after it. A line keeping none of those — no slash, a letter fused to the token, a
homoglyph inside the word — passes it. Some of that could be chased with more pattern; the rest needs
character-similarity reasoning, which
`memory/decisions/2026-08-07-withdraw-the-first-review-receipt-implementation.md`
forbids. Neither is claimed as covered.

**A verdict the core-scope gate declines to count leaves the tally by that gate's rules,
not this parser's.** It refuses a reviewer it cannot tell apart from the claimant or from
another reviewer under `check_core_scope.identity_key`, and it keeps only the later of
two verdicts from one identity. Those rules are `main`'s and unchanged.

**A verdict outside the one `## Review verdicts` section is not in the receipt.** The
parser reads one section and nothing else.

**The action gate blanks nothing when it cannot place a verdict.** If the rendered view
rewrote anything inside the verdict's prefix — the marker, the reviewer, or the token —
the line is left alone and the completed verdict is reported as an ordinary action. That
refuses the commit rather than hiding anything, and
`templates/task/verification.md` tells writers to keep that prefix plain.

One asymmetry remains between the gates and it fails closed: a verdict whose reviewer
carries raw HTML is counted by the core-scope gate but not neutralized by the action
gate, because the rendered line no longer opens with the verdict's prefix. The completed
verdict is then reported as an ordinary action, which refuses the commit rather than
hiding anything. Markup in the *finding* is fine — the prefix stops at the token — and
`templates/task/verification.md` asks writers to keep raw tags out of a finding anyway.

## Core fit

**Agent substitution:** pass — every agent runtime records and reads the same repository receipt grammar
**Provider substitution:** pass — the behavior depends only on repository Markdown, not a review provider
**Repository substitution:** pass — any adopted repository needs completed review evidence kept distinct from pending human asks
**User-global writes:** none
**Why AgentFold core:** this repairs two canonical repository gates whose contradictory classifications prevent valid core-task admission
**Thin adapter:** none
