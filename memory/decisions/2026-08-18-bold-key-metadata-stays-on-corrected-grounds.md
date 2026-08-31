# Bold-key metadata stays, but two of the reasons given for it are false

**Status:** decided
**Date:** 2026-08-18
**Decided-by:** agent (delegated: this overturns two factual premises and changes no rule; the format itself is unchanged and every check, template and file already reads it)
**Description:** Keeps `**Key:** value` metadata while retiring two false premises — YAML front matter is not invisible on GitHub, and bold-key lines do not render as readable bold text everywhere
**Review-by:** 2027-02-21
**Amends:** `memory/decisions/2026-07-22-bold-key-frontmatter.md` — the "invisible on rendered GitHub pages" premise under Alternatives considered, and the "Renders as readable bold text everywhere markdown renders" clause under Consequences

## Context

`memory/decisions/2026-07-22-bold-key-frontmatter.md` chose `**Key:** value` lines over
YAML front matter. Its decision is right and stands. Two of the facts it rests on do not.

**"YAML frontmatter … invisible on rendered GitHub pages."** GitHub renders a leading
`---` block as a formatted table above the first heading. It is one of the most visible
things on the page, not an invisible one. This observation is inherited from the review
round that raised it and was **not re-measured in this session**; no network call was made
from here, and it is recorded as attributed rather than as something this repository
verified.

**"Renders as readable bold text everywhere markdown renders."** The bold *labels* render;
the *lines* do not. CommonMark joins consecutive non-blank lines into one paragraph unless
each ends in a hard break, so a block of ten `**Key:** value` lines renders as one run-on
sentence of bold-punctuated fragments. This repository already acts on that fact in two
places: `folded_record_block` appends two trailing spaces to every field line but the last
precisely because that is the hard break, and `.gitattributes` opts the queue paths out of
Git's `blank-at-eol` so those spaces survive. A format whose readability depends on
invisible trailing whitespace is not one that "renders as readable bold text everywhere".

## Decision

Bold-key metadata stays, on the two grounds that survive: it parses with one stdlib regex
in a repository that may not take a dependency, and it stays flat key→string, which keeps
structure out of prose files. The two premises above are retired. The 2026-07-22 record
keeps `**Status:** decided`, because everything else in it still binds; it gains only the
`**Amended-by:**` back-link, which is one of the three edits `memory/AGENTS.md` allows a
decided ADR to receive.

Where the run-on rendering actually hurts — a block of machine fields under the line a
person answers on — the repair is the fold, not a change of format:
`memory/decisions/2026-08-18-the-machine-record-is-folded-and-checked-by-position.md`.

## Alternatives considered

- **Rewrite the 2026-07-22 ADR.** Refused by `memory/AGENTS.md`: a decided record is never
  rewritten, and a reader who saw the old reasoning deserves to find it plus its correction.
- **Supersede it outright.** Wrong shape. A supersession says the decision was reversed;
  the decision was not reversed, only two of its reasons.
- **Move to YAML front matter now that "invisible" is false.** It still needs a parser this
  repository will not take on, and it still invites nested structures that belong in the
  body or a real data file. The corrected premise removes one argument against YAML, not
  the two arguments that decided it.

## Consequences

`memory/index.md` marks the 2026-07-22 entry `[amended]`, so a booting agent does not read
an overturned premise as live. Anyone citing "YAML is invisible on GitHub" as a reason for
anything is citing a false fact and should stop. Anyone assuming a block of bold-key lines
is readable as written must supply hard breaks or a fold; the templates now do both.

Revisit if the reconciler ever gains a dependency budget, which would reopen the only
argument the corrected premises leave standing.
