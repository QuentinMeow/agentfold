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

Nothing inside the receipt section is skipped in silence. One loose recognizer — a
`core-fit /` line under an optional list marker of any kind — is applied both inside the
block and after it, so a verdict that misses only on its marker (`1.`, `1)`, `•`, none)
or only on its dash (hyphen, en dash) is reported instead of being read as the ordinary
prose that closes the block. Any error yields zero verdicts, so the core-scope gate
reports it and the action gate grants no exemption at all.

Both gates parse `semantic_text` of the same bytes, so neither can accept a receipt the
other refuses. The action gate then finds each accepted verdict's own line in
`rendered_human_text` by literal search — the way it already finds a projected queue
link — and blanks the token at that offset. That is why raw HTML rendering as a heading
cannot claim a receipt: `rendered_human_text` is never the parse view, which its own
docstring requires.

The exemption belongs only to a path matching `tasks/<status>/<task-id>/verification.md`
in full, because that is the artifact `--require-review` validates. A receipt in the
task's worklog, or in a verification record nested one directory deeper, gets ordinary
classification.

The claimant and reviewer identity comparison is `check_core_scope.identity_key`
unchanged: a case-folded, order-insensitive set of word tokens. The parser rejects a
reviewer that produces no such token, because that verdict would otherwise parse and
then vanish from the tally.

## Known residue

Three things still leave the tally without an error, all by prior design and none of
them this parser's to change: a verdict inside a code fence or an HTML comment, which
`test_fenced_review_example_is_not_a_verdict` requires to be inert; a second verdict from
an identity already recorded, which the core-scope gate replaces under its "latest
verdict per reviewer" rule; and a verdict outside the one `## Review verdicts` section,
which is not in the receipt at all. A non-`core-fit` lens verdict written with `approve`
is still an unqueued action, unchanged from the default branch, because the authorized
grammar covers `core-fit` lines only.

## Core fit

**Agent substitution:** pass — every agent runtime records and reads the same repository receipt grammar
**Provider substitution:** pass — the behavior depends only on repository Markdown, not a review provider
**Repository substitution:** pass — any adopted repository needs completed review evidence kept distinct from pending human asks
**User-global writes:** none
**Why AgentFold core:** this repairs two canonical repository gates whose contradictory classifications prevent valid core-task admission
**Thin adapter:** none
