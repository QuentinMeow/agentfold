# Writing decisions humans can actually answer

A decision file is an interface between an agent with full context and a human with none.
Most unanswered decisions are unanswerable: they assume knowledge the reader does not have,
or they ask for a judgment the agent should have made itself.

This guide covers only what is specific to a *decision*. The rules every human action
shares — who may be asked, the order of the file, how one edit answers it, how it resolves —
are in `handbook/human-action-guide.md`. The fields to copy are in
`templates/queue/decision.md`. How to write the prose is
`skills/explain-to-human/scenarios/queue-item.md`.

## Assume this reader

They are not an expert in this domain. They have not read the code. They will read one
screen and answer from their phone. Everything below follows from that.

## The five things a decision file owes

**1. A question in the title.** Answerable in a word or two, by someone who does not know
this repository, and carrying no verdict.

**2. Context from zero.** Two or three sentences: what part of the system this touches, and
why the question came up now. Link every source — the link is depth, never a prerequisite.

**3. Options with example consequences.** For each option: what it means in plain language,
then a *concrete scenario* of life after choosing it — "if we pick A and a user does X, then
Y happens". The example consequence is the most important part of the file. It is how a
non-expert experiences the difference between two options they cannot otherwise compare.

Two options is the minimum. Four is the maximum: past that, readers defer rather than
choose. Never pad the list with an outcome nobody would pick.

**4. A recommendation.** One sentence saying which you would pick and why, placed after the
options so it cannot anchor them, with the strongest case against it beside it.

**5. What happens if nobody answers.** The safe default, and what it costs. "Nothing stops"
is a complete answer and often the true one.

## A worked example

> **Should the quote API store quotes in a JSON file or SQLite?**
>
> **Option A — JSON file.** Human-readable, and reviewable in a pull request.
> *Example consequence:* two agents writing quotes at the same time can corrupt the file;
> you would see quotes occasionally disappear with no error.
>
> **Option B — SQLite.** Safe concurrent writes.
> *Example consequence:* the data stops being reviewable in a pull request; inspecting it
> needs a tool.
>
> **Recommendation:** A — our writes are single-threaded today.
> **If you do nothing:** we proceed on A from 2026-08-01 and the question stays answerable.

Notice what the example consequences do that the option descriptions cannot: they name
something the reader would *see happen*. "Safe concurrent writes" is a property; "quotes
occasionally disappear with no error" is an experience.

## Where the background lives

Durable background belongs in the task's `design.md` or in `memory/`, and this file links
it. The queue file uniquely owns the unresolved action, its timing, its status, and any
answer — nothing else. Delete it only when those are folded or explicitly disposed of.

## When the answer is a counter-question

A counter-question is a valid answer, and like every other concrete response it is
immutable. Treat it as a disposition: claim the item, fold the answer into the durable
evidence it named, then file a new same-timing item whose `Supersedes` names the old path.
Never edit what the human wrote.

## After the answer

Fold the answer into the affected documents, record an ADR in `memory/decisions/` (schema:
`templates/memory/adr.md`), then delete the resolved item in that same commit. Git history
archives the completed delivery; it does not replace live state.
