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
stays exact; widening it is how the withdrawn implementation grew. The rejector's only
power is to refuse — widening it can never accept anything new, only report more — so it
is made as permissive as it can be: any decoration before `core-fit`, any short run of
non-letters inside it or before the slash, any dash. One rejector is applied by one loop
on both sides of the block end, so the two cannot drift apart. Any error yields zero
verdicts, so the core-scope gate reports it and the action gate grants no exemption.

The claim that holds exactly: inside the receipt section, any line the rejector matches
and the acceptor does not is reported with its line number. Not more than that — see
Known residue.

Both gates parse `semantic_text` of the same bytes, so the action gate never neutralizes
a receipt the core-scope gate would refuse. The converse does not hold, on purpose: the
action gate additionally requires the artifact path and a rendered line still opening
with the verdict's own prefix, and when either fails it blanks nothing. That prefix
search — the technique the gate already uses for a projected queue link — is also why
raw HTML that merely renders as a heading cannot claim a receipt: `rendered_human_text`
is never the parse view, which its own docstring requires.

The exemption belongs only to a path matching `tasks/<status>/<task-id>/verification.md`
in full, because that is the artifact `--require-review` validates. A receipt in the
task's worklog, or in a verification record nested one directory deeper, gets ordinary
classification.

The claimant and reviewer identity comparison is `check_core_scope.identity_key`
unchanged: a case-folded, order-insensitive set of word tokens. The parser rejects a
reviewer that produces no such token, because that verdict would otherwise parse and
then vanish from the tally.

## Known residue

Three shapes reach for a verdict and fall outside even the widened rejector, so they end
the block in silence: no slash at all (`- core-fit reviewer: approve — …`), a letter
fused to the token (`- core-fitt / …`), and a homoglyph inside the word itself. Catching
those needs character-similarity judgement, which
`memory/decisions/2026-08-07-withdraw-the-first-review-receipt-implementation.md`
forbids.

Five further routes out of the tally are prior design, not this grammar's:

- a verdict inside a code fence or an HTML comment is blanked before any gate sees it,
  which `test_fenced_review_example_is_not_a_verdict` requires;
- a second verdict from an identity already recorded replaces the first, under the
  core-scope gate's latest-verdict-per-reviewer rule;
- a verdict whose reviewer matches the claimant is dropped by
  `check_core_scope.same_reviewer_as_claimant`;
- two different reviewer names whose word tokens form the same set collapse to one
  entry, because `check_core_scope.identity_key` is order-insensitive;
- a verdict outside the one `## Review verdicts` section is not in the receipt at all.

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
