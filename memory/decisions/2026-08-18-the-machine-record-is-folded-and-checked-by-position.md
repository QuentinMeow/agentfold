# A live human question hides its machine record in one sanctioned fold, checked by position

**Status:** decided
**Date:** 2026-08-18
**Decided-by:** agent (delegated: the owner's complaint was rendered volume and the shape is reversible — no live item is edited, and reverting the templates restores the previous layout exactly)
**Description:** Machine fields on new human queue items live below the answer line inside one `<details>`, and the checks that hold that shape are scoped by line position rather than by key name
**Review-by:** 2027-02-14
**Amended-by:** `memory/decisions/2026-08-30-retry-diagnosis-keeps-its-exposed-editable-prose.md` — the queue-frozen-skeleton clause for exposed retry diagnosis

## Context

Every question an agent files the owner ended with ten to fifteen labelled bookkeeping
lines under the line he answers on. Measured across the ten items that predate this
decision: 106 field lines, 7,385 painted characters, 252 lines of screen at 40 columns.
On a phone that is more screen than the question.

Two things made this hard rather than cosmetic. Bold-key metadata renders as one run-on
paragraph unless every line carries a two-space hard break, and those hard breaks cost
their full height wherever they are visible — so hard-breaking the block everywhere makes
it 17–43% taller at 40–100 columns. And a field that a renderer shows in bold but no
parser reads is invisible loss: indent one by a space, or write it as a list item, and it
still looks like a field while every check stops seeing it.

## Decision

The three `needs-human/` templates carry their machine block below the answer line inside
one collapsed `<details>`, whose nine rules are enforced rather than remembered. Hard
breaks survive in exactly that one place, where a closed fold makes their height cost
zero. Four checks hold the shape:

- `record-swallow` blocks a line the record region renders as a bold key and
  `semantic_text()` cannot read. It is scoped by **line position** — above the first
  `## `, or at and below the answer line — never by key name, because `Status`, `Action`,
  `Check`, `Subject` and `Today` are declared fields *and* ordinary English words.
- `fold-shape` holds the nine fold rules, including the two swallow points that take a
  whole record to zero readable fields.
- `check_human_attention`'s blanket raw-HTML ban narrows to admit exactly three anchored
  line shapes, and gains `parsed ⊆ rendered` findings for `display:none`, `hidden` and
  `aria-hidden`, because folding is legal and hiding is not.
- `queue-frozen-skeleton` refuses an edit that leaves `queue_action_identity()` unchanged
  while the raw bytes change. Identity is computed over a subtractive view, so a comment,
  a fence or an indented block could be appended to a frozen record invisibly; the
  skeleton and the exposed mutable values are asserted by test to be a total partition of
  the file's bytes.

No live item is folded. Folding one changes its action identity, which `queue-resolution`
refuses, so the corpus is deliberately mid-migration and `templates/README.md` says to
copy the template and never the nearest existing file.

## Alternatives considered

- **Hard-break the block in place, no fold.** Measured 17–43% *taller* at 40–100 columns:
  N hard-broken lines wrap to the sum of their own wraps, never less than one paragraph's.
- **Move the block to a second file.** Breaks "one item, one file", the property that makes
  a queue item answerable and deletable in one edit.
- **Scope `record-swallow` by key name.** A closed list of machine keys is also a list of
  ordinary words; the naive predicate fired 105 times across the tracked corpus, and
  position scoping took it to 0.
- **Retro-fold the existing items.** Refused by the identity rule, and rightly: it would
  rewrite questions the owner has already been shown. Filed as his decision instead.

## Consequences

The fold ships with zero production exercise and will keep it for the current live items,
because none of them may be folded — the first real use is the next question anyone files.
`--fix-queue-fold` re-emits the block from any malformed shape, and refuses to write a
result it cannot leave clean rather than half-repairing one. Two live items will keep
printing an advisory about values cut mid-sentence until they are answered, which is the
deliberate cost of not going silent about a file nothing may repair.

Revisit if a renderer the repository must support stops collapsing `<details>`, or if the
identity rule gains a sanctioned migration path that makes retro-folding legal.
