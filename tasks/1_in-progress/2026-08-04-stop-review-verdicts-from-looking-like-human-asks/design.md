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

Share the core-scope gate's exact named-group grammar, and only in `verification.md`
replace the matched `approve` or `block` token with equal-width whitespace before human-
action classification. A benign completed verdict is inert, while the reviewer identity
and finding remain visible and malformed lookalikes receive ordinary classification.

## Chosen

Option B. The shared grammar prevents the validator and detector from defining competing
receipt shapes. Equal-width token blanking is narrow and reversible: removing one helper
call restores the prior behavior, while broad exemptions would create a hidden-action
surface whose safety would require a new parser.

## Core fit

**Agent substitution:** pass — every agent runtime records and reads the same repository receipt grammar
**Provider substitution:** pass — the behavior depends only on repository Markdown, not a review provider
**Repository substitution:** pass — any adopted repository needs completed review evidence kept distinct from pending human asks
**User-global writes:** none
**Why AgentFold core:** this repairs two canonical repository gates whose contradictory classifications prevent valid core-task admission
**Thin adapter:** none
