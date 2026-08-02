# Design notes — rewrite the human-facing guidance

**Status:** decided

## Problem

`handbook/human-action-guide.md` instructs agents to write for a non-expert who will answer
from a phone, in 178 lines that no non-expert can read. Its paragraphs chain provider-adapter
identity, review binding, merge-queue replay, and GitHub ruleset names with no heading,
example, or gloss between them. `message-queue/AGENTS.md` has the same shape in its
"Lifecycle and content" list, under a 60-line budget that makes density feel obligatory.

The risk in fixing it is obvious: a readability rewrite of a normative document silently
drops rules. Every rule in these two files is one an agent could violate.

## Options considered

### Option A — Rewrite against a rule inventory
Enumerate every normative statement first, then restructure, then check the rewrite back
against the inventory row by row.
*Example consequence:* the inventory is committed as task evidence, so a later reader who
suspects a rule went missing can check rather than guess — and an independent audit can be
run against it without redoing the enumeration.

### Option B — Rewrite in place, incrementally
Improve a paragraph at a time over several sessions.
*Example consequence:* the document keeps its structure, which is the actual problem: the
depth is interleaved with the everyday rules, and no amount of sentence-level editing
separates them.

### Option C — Split the document into several files
*Example consequence:* the ask "read the human action guide" stops resolving to one file,
and every other contract that links it needs updating. The depth split inside one file gets
the same separation without the churn.

## Chosen

Option A, with the depth split from Option C applied inside the single file. The guide now
carries an explicit "stop above this line unless you need it" divider: everything needed to
write an ordinary decision or clarification is above it, and the two situations that need
more — a review holding a boundary open, and an item bound to an external provider — are
below.

Two statements were corrected rather than merely restructured, because they were false:

1. `not-approved` was described as equivalent to the terminal outcomes. The reconciler
   registers it as the legacy alias for `changes-requested`, which carries different
   obligations (a repair action plus a re-review, rather than ending pursuit).
2. `message-queue/AGENTS.md` said a review "binds a stable local file". A merge review binds
   a Git range, and an HTTPS artifact is also permitted, so the flat claim contradicted both
   the guide and the template. It is now a pointer rather than a restatement.

Six other statements were restatements of rules another file owns, and became pointers.
Everything else is the same rule in different prose.

## What was found but not fixed

The rewrite surfaced a contradiction it did not resolve: the same timing rule is stated in
both `handbook/human-action-guide.md` and `message-queue/AGENTS.md`. That is the shape task
`2026-07-31-collapse-restated-contract-rules` already owns, and duplicating it here would
create a second live action for one problem.

## Core fit

**Agent substitution:** pass — both files are prose contracts read by any agent runtime, and
nothing in the rewrite names a runtime.
**Provider substitution:** pass — the provider-specific rules were not changed, only moved
below the depth divider and labelled as GitHub-specific, which makes them easier for a
non-GitHub adopter to identify and replace.
**Repository substitution:** pass — an adopted repository gets the same two contracts and
needs them equally.
**User-global writes:** none
**Why AgentFold core:** these two files are the contract for the one thing this harness
exists to do well — ask a human for something in a way they can answer. Their readability is
the mechanism, not decoration.
**Thin adapter:** none
