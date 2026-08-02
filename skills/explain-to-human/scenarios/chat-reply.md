# Scenario — the chat reply that ends a session

Chat is the only channel that reaches the owner without them going looking. It is also the
only one that disappears. So the reply carries no state of its own: everything it says is
already a file, and the reply is the notification that those files exist and what they
mean.

The reader is a manager, not a bystander. They did not watch the work, they will not read
the diff, and their job is to decide — so the reply is written the way an engineer reports
to someone who is accountable for the outcome and has ten other things to think about.

Read `../reference.md` for the craft. This file owns what goes in the reply and in what
order.

## The order

1. **Whether anything is blocked, and whether anything needs them right now.** One line.
   If nothing is blocked, say that first — an owner who does not have to act should learn
   it in the first sentence, not after four paragraphs.
2. **What was done**, as outcomes. Three to six lines, each a before and an after.
3. **What was decided for them**, each with the reason and how expensive it is to reverse.
4. **What they owe**, in priority order, each with its consequence and a recommendation.
5. **Where it all is** — pull requests, branches, task state — so they can go look.

That order is not negotiable and it is the same order as the three layers: the first line
is layer 1, the "what was done" block is layer 2, and everything after it is layer 3.

## 1. The first line

State the trajectory and the ask together.

- "Nothing is blocked. Four pull requests are open and two decisions are waiting on you,
  neither of them urgent."
- "One thing is blocked: the migration cannot start until you decide whether the old
  column is dropped. Everything else landed."

Never open with process ("I started by exploring the repository…"). Never open with a
question. Never claim a clean result while an open risk contradicts it — if the status is
good and a risk is open, say what would have to be true for the risk to close.

## 2. What was done

Outcomes, not activity. Each line is `<what is different> — <how it was before>`. Group by
what the owner cares about, not by the order the work happened in.

- No: "Refactored the projection layer and updated four call sites."
- Yes: "A handover written last week no longer fails a rule invented this week. Before,
  every branch cut before a rule change became permanently unmergeable."

Name the actor. If a check did something, say the check did it. If the owner still has to
do something, that belongs in section 4, not here.

## 3. What was decided for them

The owner is accountable for decisions an agent made on their behalf, so they hear about
every one of them, even the ones that were obviously right. One line each:

**what was chosen — why — what it would cost to undo.**

> Chose to keep the merge gate advisory rather than enforcing it in CI. A hard gate would
> have blocked three branches that are already merged and cannot be un-merged. Reversing
> this is one line in `handbook/git-workflow.md` plus a workflow change — about an hour.

If a decision was expensive to reverse, it should have been a queue item rather than a
decision, and the reply says so plainly.

## 4. What they owe

This section is a projection. Every entry already exists as a file under
`message-queue/needs-human/`; the reply never invents an ask, and never carries a second
copy of an answer slot. The exact set of items and the link format come from the handover's
"Needs your attention" section, which `history/AGENTS.md` and `templates/handover.md` own.

Order by consequence, most consequential first. For each item give four things, in this
order, and nothing else:

1. **The ask**, as a clickable link whose label is the item's `Action`.
2. **Why it matters** — the consequence in the world.
3. **If you do nothing** — the safe outcome, said plainly, including "nothing stops".
4. **What I would pick, and why** — one sentence. A recommendation is evidence, not
   permission to hide the alternative, so name the strongest reason against it too.

A bare item name is not an entry. Neither is a link with no context: if the owner has to
open the file to know whether they care, the entry failed.

Repeat every still-open item in every reply, including ones you surfaced last time.
Repetition is the mechanism; an unanswered item that stops being mentioned is an item that
silently died.

When the list runs long, group it — the ones this session created, then the ones that were
already waiting — and give the older group one line each instead of four. Grouping is
presentation; dropping an item is not, and the set is fixed by the handover.

## 5. Where it is

Last, short, and concrete: pull-request numbers and titles, the branch each one is on, and
which tasks moved. This is the section the owner uses when they decide to go look, so it
carries links, not descriptions.

## Rules for the whole reply

- **Gloss every repository-specific term at first use.** The owner knows software; they do
  not have this repository's vocabulary loaded.
- **Never make the owner ask "what is this".** If a name appears, it is explained on the
  spot or it does not appear.
- **Never make the owner ask "what do I need to do".** Section 4 exists for exactly that,
  and if it is empty, say "Nothing needs you" in section 1.
- **Do not restate the diff.** Anything the owner could reconstruct by reading the code is
  not worth their attention.
- **No unexplained numbers.** Every number gets its unit, its baseline, and where it came
  from.
- **Length is a budget, not a virtue.** Long is fine when each line earns its place; a
  short reply that hides an open decision is worse than a long one that surfaces it.

## A worked reply

> Nothing is blocked. Two pull requests are open and one decision is waiting on you; the
> work continues either way.
>
> **What changed**
> - The reconciler (the script that checks every repository rule before a commit) stopped
>   re-reading the same Git objects for every file. A full check went from 41 seconds to 6.
> - A handover written before a rule existed is now judged by the rules that existed when
>   it was written. Before, one rule change made every older branch unmergeable.
>
> **Decided for you**
> - Cached Git reads in memory rather than on disk, because a disk cache would need
>   invalidation rules we have no way to test yet. Undoing it is deleting one function.
>
> **Waiting on you**
> 1. [Approve the caching change](<link>) — it changes how every check reads Git, so a
>    wrong call here is felt everywhere. If you do nothing: the change stays merged and
>    the review stays answerable; nothing stops. I would approve it — the risk is a stale
>    read inside one process, and the strongest case against is that we have no test that
>    proves staleness cannot happen across a fork.
>
> **Where it is**
> - #61 *Cache reconciler Git object reads* — branch `task/2026-07-30-cache-reconciler-git-object-reads`
> - Task moved to `3_in-review`.

## Done when

The owner can act without asking a single follow-up question: they know whether anything
is blocked, what is different now, what was decided without them, what they owe, in what
order, and where to look.
