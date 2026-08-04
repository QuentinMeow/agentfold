# Design notes — stop completed review verdicts from looking like human asks

**Status:** decided

## Problem

The core-scope gate requires a completed review line shaped like
`- core-fit / reviewer: approve|block — finding`, but task admission reads the same
`approve` or `block` token as a new human command. The repair must recognize exactly the
receipt grammar the core-scope gate accepts while leaving reviewer and finding prose under
the ordinary human-action detector.

## Options considered

### Option A — exempt review receipts

Skip a matched receipt line, its section, or all of `verification.md`. This removes the
false positive, but a finding such as “owner please approve the release” becomes an
unqueued ask that task admission cannot see.

### Option B — neutralize only the structural verdict token

Share the core-scope gate's exact section, revision-field, and named verdict grammar. Only
for the canonical lowercase task-root `verification.md`, and only after exactly one valid
full-commit field in exactly one real `## Review verdicts` section, replace the matched
`approve` or `block` token with equal-width whitespace before human-action classification.
A benign completed verdict is inert, while the reviewer identity and finding remain
visible and every path or receipt-region lookalike receives ordinary classification.

## Chosen

Option B. A blocked review of the first implementation proved that sharing only the line
regex was insufficient: basename matching and whole-file normalization admitted paths and
regions the core gate would never accept. The shared formal parser now prevents the
validator and detector from defining competing receipt regions as well as competing line
shapes. A second review found that a region ending only at the next ATX H2 still crossed
real ATX H1 and setext H1/H2 boundaries. The parser now preserves the exact H2 opener but
ends at the next real heading of level one or two, excluding the setext heading's content
line while retaining H3 detail inside the section. Equal-width token blanking remains
narrow and reversible: removing one helper call restores the prior behavior, while broad
exemptions would create a hidden-action surface.

## Core fit

**Agent substitution:** pass — every agent runtime records and reads the same repository receipt grammar
**Provider substitution:** pass — the behavior depends only on repository Markdown, not a review provider
**Repository substitution:** pass — any adopted repository needs completed review evidence kept distinct from pending human asks
**User-global writes:** none
**Why AgentFold core:** this repairs two canonical repository gates whose contradictory classifications prevent valid core-task admission
**Thin adapter:** none
