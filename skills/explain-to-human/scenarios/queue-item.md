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

Every rule below exists to make that answer yes.

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

## Give the choices a shared axis, then make each one concrete

Open the choices with one sentence naming what they differ on. Without it, two options
read as two paragraphs and the reader has to build the comparison themselves.

Then, for each option: what it accepts, at least one cost, and an *example consequence* —
a concrete scenario of life after that answer. The example consequence is the most
important sentence in the file, because it is how a non-expert experiences the difference.

> **Option A — Keep the gate hard.** No branch merges while any review it names is open.
> *Example consequence:* the three branches that filed their own reviews stay unmergeable
> until you answer three reviews, and any future branch that files a review blocks itself
> the same way.
>
> **Option B — Skip an action the range itself filed.** A branch may merge past a review it
> created; the review is reported again at the next boundary.
> *Example consequence:* a change merges before you have judged its design, and you find
> out at the next merge rather than at this one. The undo is `git revert -m 1`.

Two options is the minimum. Four is the maximum: past that, readers defer instead of
choosing. Never pad the list with an outcome nobody would pick — if declining is not
actually available, say so in the axis sentence instead of writing a fake third option.

When the options differ on more than one dimension, put them in one table whose rows are
the same criteria for every option. Prose paragraphs are not comparable.

## Recommend, then argue against yourself

The recommendation comes *after* the choices, so it cannot anchor them, and it names
exactly one of the options shown. Beside it, two things:

- **The strongest case against it** — the real best argument for a different answer, not a
  hedge. An agent can satisfy this slot with confident mush, and no check can tell; this is
  the one place where the honesty is entirely yours.
- **Confidence** — high, medium, or low, plus what you checked and what you did not.
  "Medium — I verified the three stuck branches and read the check, but did not simulate a
  branch that files two reviews" is useful. "Medium confidence" alone is not.

## Inline the effect, link the evidence

The owner needs the effect to decide. They do not need the investigation that found it.

- Inline: the ask, the options, each cost, the recommendation, the default if nobody
  answers, the reversal cost, and every number your reasoning uses.
- Link: the logs, the failing run, the design document, the code, the transcript.

Link the source exactly once, in the prose, with a label that says what is behind it and
why the reader does not need to open it. Machine-readable copies of paths belong below the
answer line, with the rest of the bookkeeping.

## Ask for one thing

One file, one answerable judgment. Two questions in one file produce an answer to one of
them, and there is no repair, because the first concrete response is immutable.

Never ask the owner to copy a hash, a revision, a field name, or any offered vocabulary. A
plain-English sentence is a complete answer; the agent that folds it does the bookkeeping
and shows the owner how it read their words before acting.

## Before you file it

- [ ] The title is a question, answerable in a word or two, with no verdict in it.
- [ ] `Today` describes reality, not the proposal.
- [ ] Every option has a cost and a concrete example consequence.
- [ ] The recommendation names one option shown, with a real counter-case beside it.
- [ ] Nothing above the answer line requires opening another file.
- [ ] No hash, field name, or machine token appears above the answer line.
- [ ] Every uncommon term is glossed at first use.

## Part of this is reported back to you

The reconciler's `explanation-shape` check reports, as an **advisory** finding, a section
missing from the item's own template, a section that sits out of that template's order, and
any `### ` choice with no concrete `*Example consequence:*` line under it. Advisory means it
prints with an `(advisory)` marker and is counted, and never fails a commit or a merge
(`memory/decisions/2026-08-02-readability-enforcement-disposition.md`).

It does not read every live item. An item written under an earlier field spelling is judged
by the schema it was written under, because a record is immutable — eleven of the fifty-four
live items are in that state today and are skipped. Anything you file now is checked,
including a new item that copies an older neighbour's field names.

Nothing else on the checklist above is checked. Whether the title is really a question,
whether `Today` describes reality, and whether the counter-case is real rather than hedged
are judgments a program cannot make — an item can satisfy every rule a machine can see and
still be unanswerable. The advisory line catches the shape; the rest is still yours.
