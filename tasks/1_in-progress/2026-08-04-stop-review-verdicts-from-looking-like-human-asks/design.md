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

The final compatibility boundary is an ASCII-only source whitelist rather than a partial
renderer. Claimants and formal reviewers may contain ASCII letters, digits, space, and
only `. , ; ? ! ' " ( ) / @ + -` as punctuation. Colon is excluded because it terminates
the reviewer component. Formal findings use that alphabet plus colon. The em dash belongs
only to the receipt's structural delimiter, outside those components. Every non-ASCII
character is invalid, which excludes Unicode homoglyphs as well as separators, controls,
default-ignorables, and combining marks. Brackets, angle brackets, backslash, backtick,
asterisk, underscore, tilde, braces, and ampersand still exclude links, images, reference
labels, escapes, emphasis, code, HTML, and entities by construction.

The claimant suffix is located on the one literal field in raw `task.md` before any
semantic view is built. That field must start the file or immediately follow a truly
ASCII-blank raw line; a preceding paragraph, blockquote, or list line makes it a lazy
continuation rather than top-level authority. An immediately following raw Setext
underline (`---` or `===`, with CommonMark indentation and ASCII whitespace) also invalidates
the field. Its raw characters pass the source predicate
first. A duplicate field, or any comment, markup, entity, link, image, code span, escape,
control, invisible, or non-ASCII character leaves the task with no review identity. The
already-validated literal line body must remain character-for-character unchanged at the
same logical line index in both the structural Markdown view and the rendered-human view.
Neither view supplies repaired
claimant text. A shared prefix-state check also requires the claimant and exact receipt
heading to begin outside every still-open raw HTML container. Closed containers and
HTML-looking fenced, indented, or inline-code examples remain compatible; unclosed visible,
hidden, non-prose, and custom containers fail closed. CommonMark may expose later Markdown
after a blank line, but nested text is not top-level authority. Pending incomplete
HTML-like start, end, comment, declaration, or processing markers fail closed at the
authority line even when a later line supplies the missing `>`.

Receipt extraction builds source, structural, and rendered-human line arrays once. It
collects exact heading candidates in one linear scan and returns immediately for zero or
multiple candidates, before parsing any prefix. The unique candidate parses its prefix
once. The heading, revision field, and verdicts must each retain their literal line body
at the same logical index in both derived views, which rejects human-invisible evidence
without quadratic prefix reparsing.

Duplicate exact headings fail closed across the document. A second exact full-commit field
fails only while the formal prologue remains contiguous; the first nonblank non-verdict
terminates that receipt. Exact revision fields in later historical panels remain ordinary
history and cannot join, invalidate, or receive neutralization from the earlier receipt.

Formal identity normalization uses one key everywhere: the sorted multiset of case-folded
ASCII alphanumeric characters. Placeholder rejection, claimant comparison, and
duplicate-vote replacement therefore all ignore punctuation, whitespace, token boundaries,
word order, and anagrams. `TBD.`, `D B T`, `none, yet`, `yet none`, and `n/a.` cannot become
voters. This conservative rule deliberately collides anagrams: receipt authors use distinct
stable role labels, not personal or display names.
General human-action detection still applies NFKD and removes Unicode
category-M marks so a malformed non-formal line cannot split an action keyword. Formal
authority source rejects those marks and all other non-ASCII characters before identity or
finding evidence exists. An invalid reviewer or finding ends the formal block, so the
verdict receives no neutralization. The finite ASCII alphabet costs all non-ASCII names and
findings inside the exempt receipt; Unicode explanation remains ordinary prose outside it.

## Core fit

**Agent substitution:** pass — every agent runtime records and reads the same repository receipt grammar
**Provider substitution:** pass — the behavior depends only on repository Markdown, not a review provider
**Repository substitution:** pass — any adopted repository needs completed review evidence kept distinct from pending human asks
**User-global writes:** none
**Why AgentFold core:** this repairs two canonical repository gates whose contradictory classifications prevent valid core-task admission
**Thin adapter:** none
