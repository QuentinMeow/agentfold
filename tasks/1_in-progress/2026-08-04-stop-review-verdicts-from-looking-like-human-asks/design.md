# Design notes — stop completed review verdicts from looking like human asks

**Status:** decided

## Problem

The core-scope gate requires a completed review line shaped like
`- core-fit / reviewer: approve|block — finding`, but task admission reads the same
`approve` or `block` token as a new human command. The repair must recognize exactly the
receipt grammar the core-scope gate accepts while leaving reviewer and finding prose under
the ordinary human-action detector.

## Options considered

### Initial option A — exempt review receipts

Skip a matched receipt line, its section, or all of `verification.md`. This removes the
false positive, but a finding such as “owner please approve the release” becomes an
unqueued ask that task admission cannot see.

### Initial option B — neutralize only the structural verdict token

Share the core-scope gate's exact section, revision-field, and named verdict grammar. Only
for the canonical lowercase task-root `verification.md`, and only after exactly one valid
full-commit field in exactly one real `## Review verdicts` section, replace the matched
`approve` or `block` token with equal-width whitespace before human-action classification.
A benign completed verdict is inert, while the reviewer identity and finding remain
visible and every path or receipt-region lookalike receives ordinary classification.

## Chosen

The owner-authorized closed form recorded in
`memory/decisions/2026-08-04-review-receipt-parser-authorization.md`. The first three
implementations showed that a basename check, a broad section, and a CommonMark heading
boundary all admitted shapes the core gate should not trust. The accepted parser therefore
does not infer Markdown structure: it recognizes one exact top-level `## Review verdicts`
line, one exact full-commit field as the first content, and one or more consecutive exact
core-fit verdict lines. Blank lines may separate those elements; the first nonblank
non-verdict ends the receipt. Duplicate exact headings or full-commit fields fail closed.

Only an exact lowercase task-root `tasks/<status>/<id>/verification.md` may use the
receipt. Equal-width token blanking remains narrow and reversible: it removes only the
structural `approve` or `block`, while reviewer identity and finding text remain visible to
the human-action detector. Removing one helper call restores the prior behavior; the
owner's authorization approves this parser/template boundary, not a review outcome.

The final compatibility boundary is an explicit source-text whitelist rather than a
partial renderer. Claimants, formal reviewers, and formal findings may contain Unicode
letters, marks, and numbers; ASCII space; and only `. , ; : ? ! ' " ( ) / @ + - —` as
punctuation. Tabs, non-ASCII separators, controls, default-ignorables, and every other
character are invalid. In particular, brackets, angle brackets, backslash, backtick,
asterisk, underscore, tilde, braces, and ampersand exclude links, images, reference
labels, escapes, emphasis, code, HTML, and entities by construction.

The claimant suffix is located on the one literal top-level field in raw `task.md` before
any semantic view is built. Its raw characters pass the same source predicate first; a
duplicate field, or any comment, markup, entity, link, image, code span, escape, control,
or invisible character in the suffix leaves the task with no review identity. A later
structural equality check only proves that the already-validated raw line was not hidden
inside code or HTML; it never supplies repaired claimant text.

After source validation, identity and action text use NFKD and remove every Unicode
category-M mark before casefolding and tokenization. Composed and decomposed spellings
therefore compare equally, combining marks cannot mint voter aliases or split an action
keyword, and a mark-decorated placeholder collapses back to the rejected placeholder.
This deliberately treats accent-only identity distinctions as equal at this authority
boundary. An invalid reviewer or finding still ends the formal block, so the verdict
receives no neutralization. The finite alphabet and conservative mark folding cost
Markdown formatting, uncommon punctuation, and accent-distinct identities, but avoid
predicting how an extensible renderer displays source.

## Core fit

**Agent substitution:** pass — every agent runtime records and reads the same repository receipt grammar
**Provider substitution:** pass — the behavior depends only on repository Markdown, not a review provider
**Repository substitution:** pass — any adopted repository needs completed review evidence kept distinct from pending human asks
**User-global writes:** none
**Why AgentFold core:** this repairs two canonical repository gates whose contradictory classifications prevent valid core-task admission
**Thin adapter:** none
