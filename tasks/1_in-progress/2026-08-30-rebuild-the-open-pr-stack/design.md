# Design notes — recover the open PR stack

**Status:** decided

## Problem

Two dependent PRs contain useful queue authoring and validation changes, but the lower PR conflicts with newer main and both contain correctness defects. The owner authorized replacement PRs and exclusion of discarded experiments. The existing staged merge is already fully recoverable from a preserved probe commit; it contains no unique final source behavior.

## Options considered

### Option A — Preserve original commits and repair forward
Merge the original PR histories into the current-main recovery branch and repair defects in new commits. Task claims and the review retraction/publication remain attached to their actual historical transitions; the four lower-layer conflicts are resolved explicitly.

### Option B — Reconstruct final deltas and lifecycle transitions
Reconstruct final source deltas and recreate every necessary task and review transition in new commits. This can exclude old records from the new tree, but a single snapshot fails the review-binding lifecycle and can give old handovers a different creation context.

## Chosen

Preserve both histories and repair forward in a shallow two-layer stack. Independent research found no unique useful local experiment. An update of the old upper branch would replay two withdrawn legacy transcript edges already present on main; a new bounded child task starts at the repaired lower layer and retains the old upper history through a merge. The ordinary hooks and exact first-push and PR ranges admit that history without changing receipt rules. Keep current main task-completion moves, regenerate indexes from their sources, and correct current-state prose without rewriting immutable history. The lower layer repairs retry-note mutability and moves authoring comments into the guide so genuine copy-and-fill preserves the sanctioned fold; the upper layer repairs source citations and the replacement-question lifecycle.

The notes exception is limited to exposed diagnostic prose inside a semantic Agent notes section; hidden markup and structural boundaries remain protected. Ordinary mutable fields also prove their source line is outside enclosing HTML or code. Only the three validated human-fold tag lines are neutralized in that exposure view. A narrow first-response comparison preserves all other source bytes, including line endings; it does not hide later metadata changes. Invisible entity detection recognizes complete CommonMark references and escapes without changing the shared parser or the frozen source. A replacement for an unanswerable review keeps the original timing tuple, stable context, exact target/revision, and an unanswered review state. Source comparisons preserve identifiers and use candidate bytes rather than unstaged symlink resolution.

The owner checkout, original branches, probes, and backups stay preserved. Only verified replacement PRs supersede existing PRs; no product changes merge to main. Auto-review refused direct-main coordination publication, so the filing and claim commits are carried by this PR instead. This follows the permitted safer publication path without bypassing any repository hook.

## Core fit

**Agent substitution:** pass — queue Markdown, Git history, and Python checks have no dependency on the writing agent.
**Provider substitution:** pass — source and lifecycle checks operate on repository bytes; GitHub only hosts the review surface.
**Repository substitution:** pass — any adopter needs editable diagnostic notes, trustworthy source quotations, and preserved unanswered obligations.
**User-global writes:** none
**Why AgentFold core:** These are repairs to existing portable queue invariants and authoring protocols. Orchestration state and machine-specific backups remain outside the tracked repository.
**Thin adapter:** none

The retry-note boundary partially amends the earlier frozen-skeleton decision; its canonical rationale is `memory/decisions/2026-08-30-retry-diagnosis-keeps-its-exposed-editable-prose.md`. The live-human HTML rule is unchanged.

The complete source inventory and original staged-file listing are in `recovery-inventory.md`; the owner’s exact request is in `requirements.md`. Unsupported historical measurement rhetoric is omitted from active guidance and code comments, while original immutable records remain intact.

The new invisible-byte predicate pins Unicode 16 `General_Category=Cf` ranges so Python 3.9 and 3.14 classify the same source bytes. Its existing non-format default-ignorable ranges remain; the older NFKC prose-normalization helper is unchanged. Future Unicode assignments require an explicit data update, rather than silently changing this guard with the interpreter. Source: [Unicode 16 category data](https://www.unicode.org/Public/16.0.0/ucd/extracted/DerivedGeneralCategory.txt).
