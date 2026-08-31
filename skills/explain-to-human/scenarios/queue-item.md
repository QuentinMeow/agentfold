# Scenario — a decision, review, or clarification for the owner

A queue item under `message-queue/needs-human/` is the only place this repository is
allowed to ask its owner for something. It is read once, on a phone, by someone who has not
opened the repository, and it is answered by replacing one blank with one sentence. If they
have to open another file to know what they are agreeing to, the item failed.

**This file does not define the format.** The fields, their order, and the lifecycle around
them are owned elsewhere and must not be restated here:

- Before copying, read the authoring checklist in `templates/README.md`.
- The exact schema to copy: `templates/queue/decision.md`, `templates/queue/review.md`,
  `templates/queue/clarification.md`.
- What a human action must contain and how it resolves: `handbook/human-action-guide.md`.
- Decision-specific content rules: `handbook/decision-guide.md`.
- Filename timing prefixes and what each one blocks: `message-queue/AGENTS.md`.

What this file owns is the prose that goes in those slots, and the test of whether it is
good enough. Read `../reference.md` for the craft behind each rule.

## The one test

> Could someone who has never seen this repository answer correctly, from this file alone,
> without wanting to ask a question first?

## Write the title as the question, not the verdict

The title is the whole notification on a phone. It is a question the owner can answer
without knowing this repository, and it never states which answer you want.

- No: `Fix the merge gate` — that is a verdict, and it is not a question.
- No: `Should we relax `queue_deletion_problem` for `transition:merge` ranges?` — that is a
  question only its author can parse.
- Yes: `Should a branch be allowed to merge while a review it filed itself is unanswered?`

## Say what happens today before you say what would change

The most common failure in these files is describing the proposal twice: once as "today"
and once as "the change". If nothing is implemented, "Today" says *nothing is implemented*.
The owner cannot judge a delta without knowing the state it is a delta from.

Separate three things, and never let them blur:

- **Today** — what actually happens right now, in the world, if nobody does anything.
- **What this would change** — the delta being judged, stated as a proposal.
- **What this does not decide** — the adjacent thing the reader will assume is in scope
  and is not.

## Show the source's own words

The owner needs the effect, not the investigation that found it. But when the answer turns
on what another document says, they need that document's own words: your summary of them is
the one thing they cannot check. Quote every source whose wording determines the answer,
and give the quotation its own attribution link.

> A legitimate exception is finding-specific, content-bound, attributable, reasoned,
> expiring, and visible. The producing agent cannot self-approve a confirmed critical finding.
>
> — [what the design says an exception must be](../../../docs/designs/risk-tiered-agent-guardrails.md#make-escape-hatches-narrower-than-the-rule)

Link a Markdown passage at its heading, or select text or code with `#Lx` or `#Lx-Ly`.
Line numbers start at one, stay within the file, and run forwards. An attribution may use
an ordinary destination or CommonMark angle brackets, such as
`[selected lines](<../../../docs/source notes.txt#L2-L4>)`. A backticked path alone is not
a clickable citation. Quote the decisive passage without repeating it in a summary.

Preserve wording, identifier spelling, and case, however short the quotation. Wrapping,
Markdown emphasis, and marked omissions are allowed; the remaining passages keep their
source order. When the question is "does X still match Y", quote both sides.

If no source wording determines the answer, replace the source block with
`> No source document — everything you need is above.` A local-file review must still
quote the file it asks about; that sentence cannot waive its evidence. Put optional
annotated background links below the answer, inside the existing record fold. They need
no quotation when the reader can safely skip them.

## Give the choices a shared axis, then make each one concrete

Open the choices with one sentence naming what they differ on. Without it, two options
read as two paragraphs and the reader has to build the comparison themselves.

Then, for each option: what it accepts, at least one cost, and an *example consequence* —
a concrete scenario of life after that answer. The example consequence is the most
important sentence in the file, because it is how a non-expert experiences the difference.

## Recommend, then argue against yourself

The recommendation comes *after* the choices, so it cannot anchor them, and it names
exactly one of the options shown. Beside it, two things:

- **The strongest case against it** — the real best argument for a different answer, not a
  hedge. An agent can satisfy this slot with confident mush, and no check can tell; this is
  the one place where the honesty is entirely yours.
- **Confidence** — high, medium, or low, plus what you checked and what you did not.
  "Medium — I verified the three stuck branches and read the check, but did not simulate a
  branch that files two reviews" is useful. "Medium confidence" alone is not.

## Ask for one thing

One file, one answerable judgment. Two questions in one file produce an answer to one of
them, and there is no repair, because the first concrete response is immutable.

Never ask the owner to copy a hash, a revision, a field name, or any offered vocabulary. A
plain-English sentence is a complete answer; the agent that folds it does the bookkeeping
and shows the owner how it read their words before acting.

One answer is not the only answer. If the file did not carry enough to decide, the owner may
say so in the same blank, in their own words, with no vocabulary to copy. That is a defect
report about your item rather than a verdict on its question: it is folded as a disposition,
and you owe a fresh item carrying what was missing (`handbook/decision-guide.md`). Say on the
form that the option is there; an affordance nobody is told about is not one.

## Before you file it

Run the nine authoring checks in `templates/README.md` before filing the copied template.
Three things no template can check are yours: every repository-local term glossed at first
use, every source the answer turns on quoted here and linked at its heading or selected
lines, and a recommendation naming one shown option with a real counter-case beside it.

## Part of this is reported back to you

The reconciler's `explanation-shape` check reports, as an **advisory** finding, a section
missing from the item's own template, a section out of that template's order, and any
`### ` choice with no concrete `*Example consequence:*` line under it. In the commit that
creates an item it also checks local citations against the captured candidate's regular
file bytes. It reports altered quotations, including short ones; invalid headings or line
ranges; missing, escaping, nonregular, or binary sources; local links above the answer with
no quotation; and a local-file review that never quotes its target. An item with neither
an attributed quotation nor the exact no-source sentence also receives an advisory.

Source paths resolve within the repository, relative to the item or the repository root;
unstaged files and symlinks cannot change the captured evidence. External content is not
fetched or machine-verified. A matching local quotation does not prove its relevance or
truth. Advisory means the finding prints with an `(advisory)` marker and is counted;
it never fails an ordinary commit or merge
(`memory/decisions/2026-08-02-readability-enforcement-disposition.md`).

It does not read every live item. One written under an earlier field spelling is judged by
the schema it was written under, because a record is immutable; those are skipped, and
named together in one finding that asks for a fresh item rather than an edit. A diagnostic
does not authorize rewriting or replacing a live ask; its ordinary lifecycle still applies.

What no check can see is whether the sentence you quoted is the one that matters, or
whether the counter-case is real rather than hedged. The shape is caught; the rest is yours.
