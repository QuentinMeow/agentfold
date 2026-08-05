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
receipt. The compatibility neutralizer keeps equal-width token blanking narrow and
reversible: it removes only the structural `approve` or `block`. Task-action
classification uses a stricter derived view: it blanks each accepted formal verdict line
from ordinary prose and scans its exact reviewer and finding components as separate
detection units. A start-anchored command therefore cannot hide behind the receipt prefix,
while source bytes and the receipt exemption remain unchanged. The owner's authorization
approves this parser/template boundary, not a review outcome.

The shared command grammar treats `block` like the existing ambiguous authority commands
`merge`, `release`, `review`, and `vote`: an addressed unit such as `Owner, block this
release.` is actionable, while a declarative summary such as `Block size is 4096 bytes.`
remains inert. There is no punctuation-based exception after the general `block` token:
`Owner, block — this release.` and the no-space or ASCII-hyphen variants stay ordinary
actions. Task-record authority uses the same declarative-summary guard.

Historical compatibility is confined to the task-root `verification.md` classification
view and grants no receipt authority. Before rendering task-action units, that view removes
only a literal visible list line shaped as lowercase `adversarial panel / <stable reviewer>:
approve|block — <nonempty same-line finding>`. The stable reviewer is exactly `reviewer`,
`reviewer N`, or an ASCII word/hyphen label ending in `reviewer`. Its reviewer and finding
remain separate detection units, so hostile component prose stays actionable. Uppercase
verdicts, missing whitespace, ASCII hyphens, wrong panel or reviewer labels, missing slash,
and out-of-region `core-fit` lookalikes receive ordinary action classification. Structural
receipt verdict tokens are removed
before component detection, so a benign formal `approve` or `block` remains completed
evidence rather than a new action.

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
fails only before the first valid verdict, while the formal prologue is still waiting for
evidence. The first valid verdict ends that prologue. Afterward, the first nonblank
non-verdict — including an exact revision field immediately after the verdict — terminates
the receipt without erasing the verdict already collected. Exact revision fields in later
historical panels remain ordinary history and cannot join, invalidate, or receive
neutralization from the earlier receipt.

Verdict neutralization builds semantic line-start offsets once and walks the already
ordered verdict matches with a monotone line cursor. Mapping therefore costs O(n + k) for
document length n and k verdicts, rather than rescanning the semantic prefix for every
verdict. The existing CommonMark LF/CRLF/CR normalization remains the classification-view
boundary; this change does not rewrite repository source.

Formal reviewer normalization uses a fixed 36-bin count vector ordered by ASCII `0-9` and
`a-z`. This is the bounded representation of the same case-folded alphanumeric multiset:
equality, containment, anagram, and character-distance decisions remain unchanged, while
each comparison always visits 36 bins instead of both source identities. Duplicate-vote
replacement still uses that one exact reviewer key, so distinct stable role labels are not
merged merely because one contains another.

Claimant authority additionally recognizes explicit co-claimant separators `/`, `+`, `;`,
`,`, and the standalone case-insensitive ASCII word `and`. It validates the unchanged raw
source first, strips ASCII spaces around components, and rejects the whole claimant if any
component is empty, invalid, punctuation-only, or a placeholder. The whole key is the
elementwise 36-bin multiset union of every component key, including repeated-component
multiplicity;
separator characters and the letters of structural `and` never enter it. The helper returns
that whole key plus every distinct component key. Thus `/` and `and` produce identical
authority, while `D/B/T`, `D and B and T`, `N/A`, adjacent separators, and `C++` all fail
closed. A composite claimant may contain at most 16 components; a larger label fails closed
with no claimant authority, so no verdict can establish independent review. The canonical
verification template states both the numeral and this consequence. That finite ceiling
and the fixed-size component representation bound independence comparisons even when
identities are long and every verdict names a unique reviewer.

A reviewer must be distinct from the whole claimant and every component. Equality,
punctuation or word-order aliases, either-direction character-multiset containment, and a
multiset symmetric difference of at most two characters all reject independence. This
closes component, prefix, suffix, extended-role, and one-substitution shapes such as
`codex planner reviewer`, `author`/`auth0r`, and `codex planner`/`codex plannez`.
These conservative rules deliberately create false collisions: formal receipts use
distinct stable role labels, not personal or display names, and identity text is not an
authenticated principal. Commas in display-name order, plus or slash in labels, standalone
`and`, and nearby spellings therefore sacrifice convenience to fail-closed authority.
General human-action detection still applies compatibility decomposition and removes
Unicode category-M marks so a malformed non-formal line cannot split an action keyword.
Action identity normalization is separate: it applies NFKC/casefold, retains category-M
marks inside word tokens, and removes only default-ignorables. Counter keys use the same
mark-preserving view, so composed and decomposed spellings of `José` compare equal while
`José` and `Jose` remain different actions. Formal authority source rejects marks and all
other non-ASCII characters before identity or finding evidence exists. An invalid reviewer
or finding ends the formal block, so the verdict receives no exemption. The finite ASCII
alphabet costs all non-ASCII names and findings inside the exempt receipt; Unicode
explanation remains ordinary prose outside it.

The final independence pass derives claimant keys once, normalizes each distinct reviewer
source once, and memoizes independence by reviewer key. Both the core-scope validator and
the action classifier consume those shared accepted `(verdict, reviewer key)` pairs.
Repeated votes therefore perform one claimant-component comparison. For an all-unique
panel, source scanning is linear in total identity bytes and each reviewer performs at most
17 comparisons (the whole claimant plus at most 16 components) over a fixed 36-bin
representation, so long identities cannot restore the
old quadratic total-input work.

Completed-review action classification has a narrower compatibility boundary than
ordinary task prose. An accepted reviewer or finding component is still classified on
its own, but gains only one extra conjunction rule: after an ASCII `and` boundary, a
suffix beginning with the existing `please`/`kindly` courtesy-command grammar is an
action. This catches `Could not break it and please approve the release.` without
turning `and approved`, `and approval was recorded`, or `Agents review and approve.`
into asks. The general task and provider grammars do not gain this rule.

Historical completed adversarial panels remain classification compatibility, never
review authority. An exact visible lowercase `approve` or `block` token is replaced by
equal-width spaces while the full panel line continues through the ordinary rendered
task-prose path. The finding's human-visible view resolves inline-image labels, defined
reference-link labels, and inline-code contents in the full document context before
classification. Reviewer and finding components are checked as structured units too.
Whole-line and component matches collapse to at most one Counter entry for each panel
occurrence, while two repeated hostile panel lines remain two occurrences. Exact casing,
reviewer shape, delimiter, and visibility checks stay unchanged, so malformed and
core-fit lookalikes remain ordinary prose.

## Core fit

**Agent substitution:** pass — every agent runtime records and reads the same repository receipt grammar
**Provider substitution:** pass — the behavior depends only on repository Markdown, not a review provider
**Repository substitution:** pass — any adopted repository needs completed review evidence kept distinct from pending human asks
**User-global writes:** none
**Why AgentFold core:** this repairs two canonical repository gates whose contradictory classifications prevent valid core-task admission
**Thin adapter:** none
