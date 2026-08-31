# Design notes — trustworthy question evidence

**Status:** decided

## Problem

The retained upper PR verifies source quotations and carries an unanswerable review into a replacement question. Research reproduced source checks that silently skip missing targets, depend on unstaged symlinks, erase identifier bytes, or skip short quotations. A replacement review can also silently change its boundary or arrive already answered.

## Options considered

### Option A — Repair the existing checks and preserve history
Read captured regular-file bytes through lexical paths, support precise heading or bounded-line selections, and compare faithful wording. Require the replacement to hold the same unanswered review obligation. Keep source quality advisory and lifecycle checks blocking.

### Option B — Drop the upper feature or reconstruct its final snapshot
Dropping it loses useful source visibility and a valid outcome for an unanswerable question. A snapshot loses the review retraction/publication sequence and the creation context of immutable records.

## Chosen

Repair the existing checks above the recovered lower branch and merge the original upper history intact. The ordinary lower-first merge preserves identical content, and a new task branch avoids replaying withdrawn transcripts that were already in main. The original PR remains recoverable and is replaced only after full verification.

Local evidence uses the candidate's regular-file modes and bytes, with lexical file-relative or root-relative resolution. Headings written with hash marks and bounded physical line ranges select source text. Attributed-source links use the same captured lexical target in the ordinary link scan, so a root-name collision or unstaged symlink cannot select different bytes. Quotation comparison preserves identifiers, case, and literal string spacing while permitting paired emphasis, wrapping outside literals, and ordered elisions; all quote lengths are checked. Missing or unsupported local sources produce advisory findings, and external source content is not machine verified. The explicit no-source sentence never substitutes for a local review target.

A new unanswerable-review successor preserves the original-schema timing tuple, full context, exact target and revision, and still-unanswered waiting state. Existing human-authored or frozen question prose remains untouched. Templates and guidance describe these supported limits without adding a schema field.

## Core fit

**Agent substitution:** pass — the rules use ordinary Markdown, Git objects, and Python independently of the writing agent.
**Provider substitution:** pass — source evidence and review lineage remain repository-local; an external provider only projects the canonical item.
**Repository substitution:** pass — unrelated adopted repositories need trustworthy quotations and preservation of unanswered review obligations.
**User-global writes:** none
**Why AgentFold core:** These are scoped repairs to existing portable source and queue lifecycle checks, not provider configuration or an optional product integration.
**Thin adapter:** none

Source comparisons also preserve token boundaries and literal spans. A quoted number or identifier cannot match only part of a longer token. Code and string-literal spacing survives presentation normalization, and prose omission markers cannot cut through a source literal. Actual literal ellipsis characters remain literal text. These are bounded quotation-fidelity rules, not a general Markdown renderer or a claim of semantic relevance.

The literal recognizer deliberately stays lexical. Prefix-shaped apostrophe prose can be indistinguishable from an actual prefixed string, so exact spacing remains the safe fallback instead of weakening literal fidelity. The canonical guide states this advisory limitation. Unicode 16 identifier assignments are recognized on both supported Python versions without treating every unknown character as part of an identifier; later assignments require a deliberate data update. Neither repair changes lifecycle enforcement or claims a general language parser.

## Final delivered candidate

[PR91](https://github.com/QuentinMeow/agentfold/pull/91) is the second layer above [PR90](https://github.com/QuentinMeow/agentfold/pull/90). The final code candidate is `4008f4984ad0e6fc26d7fd1c1e3d6ca28673cc41`; `verification.md` records both Python versions, full-history clones, actual boundary checks and five independent native reviews. `regression-evidence.json` records the added test methods and their failing controls. The final repairs preserve complete triple-quoted literals and Unicode 16 token boundaries. The lexical R-prefix/prose ambiguity and exact-spacing fallback are documented in `templates/README.md`. The parent task owns the separately unexecuted external-review authorization, local preservation inventory and stack recovery decisions. No policy gate was weakened and no product merge to main was performed.
