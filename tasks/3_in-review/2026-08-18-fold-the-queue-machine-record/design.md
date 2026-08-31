# Design notes — fold the machine record on new human queue items

**Status:** decided

## Problem

The owner reads queue items on a phone. Every `needs-human` item ends with ten to fifteen
labelled bookkeeping lines directly under the line he answers on — status, dates, paths, a
64-character checksum — none of which he acts on. He asked for that volume to shrink
without losing anything a check reads.

Three constraints make the obvious repairs illegal. An HTML comment cannot carry the
record, because `semantic_text()` blanks comments before `fields()` parses, so a
comment-hidden `**Status:**` does not exist to any gate. Two trailing spaces on every field
line make the block **taller** when it is visible, because *N* hard-broken lines wrap to
`sum(ceil(len_i/W))` and a run-on paragraph wraps to `ceil(total/W)`. And a live item may
not be reformatted at all: folding changes `queue_action_identity()`, which
`queue_mutation_problem` refuses.

## Options considered

### Option A — hard-break every field line on every live item
Rejected. Measured on this repository's own live items it adds 17–43 % rendered height at
40–100 columns — the opposite of the request — and it edits 64 identity-frozen files.

### Option B — a `<details>` fold, new items only, enforced by shape
Chosen. A collapsed `<details>` paints only its `<summary>`, so the record costs one line
until tapped, and the fields below the blank line after `</summary>` stay ordinary Markdown
that every existing check reads unchanged. Nothing is added to any parser view, which is
the property that keeps `semantic_text()`'s subtractive consumers correct.

### Option C — a typed field grammar, as a tracked field schema
Deferred, not refuted. Its decisive argument was that a closed key set would make a
blocking visibility check legal; the check adopted here consults no key name at all, so
that argument is gone. Queryability remains a real motive and belongs in its own task.

## Chosen

Option B, implemented exactly as the external specification **SPEC v0.2** describes. That
document is a session artifact rather than a repository record, so it is identified here by
content rather than by path: `sha256:fbf28242ee10ac06ae73ebbf00d1d167b304305b59b8af244da5bab3ca18c7f5`,
titled *"SPEC v0.2 — the AgentFold queue item format"*. Its three load-bearing decisions,
stated once each and not restated anywhere else in this repository:

1. **The fold is the mechanism; the hard break is a detail inside it.** Two trailing spaces
   survive only inside the collapsed fold in the three human templates, where their height
   cost is zero. Zero live items and zero agent items are edited.
2. **Field visibility is policed by position, not by key name.** A queue item's *record
   region* is every line above the first `## ` heading plus every line at or below the
   answer line; prose lives strictly between them and no check looks there. Key-name
   scoping cannot work, because the declared keys — `Status`, `Action`, `Check`, `Subject`,
   `Today` — are ordinary English words with dozens of legitimate in-tree uses as prose
   labels.
3. **Identity is not integrity.** `immutable_action_text()` computes identity over
   `semantic_text()`, which blanks comments, fences and indented code, so those constructs
   can be appended to a frozen record carrying the owner's committed answer without
   changing its identity. `queue-frozen-skeleton` compares raw lines instead.

The fold's nine shape rules and the record-region definition are written down once, in
`templates/README.md`, and are enforced by code rather than restated in any `AGENTS.md`.

One deliberate deviation from the specification, recorded because it is a behaviour
difference and not a wording one: the specification's attack table expects
`record-swallow` to fire alongside `fold-shape` on a fold that swallows the answer line.
It does not, because a swallowed answer line makes the answer line unfindable and the
record region's lower half is defined *by* the answer line. Extending the region to the
whole file whenever the answer line is missing would police prose and reintroduce the
false positives that killed the key-scoped predicate, so the region stays empty and the
attack is refused by `fold-shape` alone. `verification.md` records both facts.

## What review changed, and what it could not

A red-team pass and an independent authoring measurement found two kill shots and nine
defects in the first implementation. Three of the resulting decisions are design-level
rather than repairs, and are recorded here because a reader who only sees the diff would
have to re-derive them.

**Identity is not integrity, and the integrity view has to be total.** The first
implementation compared raw lines with lifecycle-mutable field lines dropped, which was
correct on the structural axis and blind on one: a payload appended to the *end* of
`**Answer by:**` left with the line. The repair does not make the skeleton compare mutable
values — it cannot, because their whole purpose is to change — it requires them to be
*exposed*: byte-identical to the value `semantic_text` parses, and free of raw-HTML
tokens. Every byte of the file is then either frozen in the skeleton or inside an exposed
value, which is a total partition and is asserted as one by a test. The human's own
response line keeps the raw-HTML exemption, because a person may type an angle-bracketed
word and their answer commit is the one edit no rule may refuse.

**A repair a check names must be a repair that works.** `--fix-queue-fold` was named by
three findings it could not fix, and on one of them it destroyed the item — harvesting
`**Your review:**` into the fold, which the same check calls its worst state, with no way
back. The rule adopted: an emitter refuses to write any result that is still malformed,
and a finding whose repair is structural says what to move rather than naming a command.
Naming a command that cannot help is worse than naming none, because a weak model runs it.

**The fold has zero production exercise, and will keep it.** `queue-resolution` refuses a
retro-fold, so all 15 live human items stay unfolded permanently; the fold path is
exercised only by items filed from today's templates, and none has been filed yet. That is
not a gap to close later — it is the direct consequence of the safety rule this design
chose, and it means the mechanism ships tested against fixtures and untested against use.

**What could not be repaired.** The branch's first commit creates its task directly in
`1_in-progress`, which the `--range` landing gate refuses. The documented repair — file in
`0_backlog`, claim in a second commit — needs a canonical pickup request under
`message-queue/needs-agent/requests/`, and this session was instructed to treat that tree
as frozen. It is recorded in `verification.md` with the exact refusal rather than worked
around.

**Repaired by the landing session, once that constraint was narrowed.** The first commit is
now two: a `0_backlog` filing carrying the canonical pickup request, and a claim
coordination commit that resolves it. The landing gate passes. Two consequences are worth
carrying forward. Splitting an implementation commit means the record-only halves inherit
whatever `main` was — so the two coordination commits are 14/15 on Python 3.14.6, because
the `ast.Str` guard rides on the code commit and `main` was already red there. And one line
of `design.md` had to change to make the split legal: `check_core_scope.is_placeholder`
reads any value containing `<` as unfilled, so a `Provider substitution` reason that named
the fold by its tag failed the hook on its own staged diff.

**A budget is a threshold nobody can see.** The 700-word ceiling was reverted to on a
training-set length ratchet, then a held-out gate measured the same prose at pass^2 0.750
under 800 and 0.375 under 700, with a natural mean of 724.7 words. Both readings are kept
on the constant, because they answer different questions: the ratchet measures how long
authors write, the held-out gate measures whether the threshold refuses good work, and only
the second is what a budget is for. The deeper defect was neither number — an author could
not measure themselves before the gate refused them, so `--word-count` prints the count
against the budget for any file, committed or not.

## Core fit

**Agent substitution:** pass — every mechanism is a Python check over committed Markdown bytes; no agent runtime, model, or prompt participates in producing or evaluating the fold.
**Provider substitution:** not-applicable — nothing here reads a hosting provider; the fold is CommonMark-sanctioned raw HTML that any Markdown renderer either collapses or shows inline.
**Repository substitution:** pass — an adopted repository that files human questions has the same problem (bookkeeping under the answer line) and inherits the same templates, the same fold rules, and the same three gates without configuration.
**User-global writes:** none
**Why AgentFold core:** the queue item format is the harness's human interface, and the three gates close silent field loss and a tamper hole in the immutability machinery that every adopter inherits; none of it is personal setup, product code, or a single-provider workflow.
**Thin adapter:** none
