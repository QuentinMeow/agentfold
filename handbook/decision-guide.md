# Writing decisions humans can actually answer

A decision file is an interface between an agent with full context and a human with
none. Most unanswered decisions are unanswerable — they assume knowledge the human
doesn't have. Schema: `templates/queue/decision.md`. This guide is about the content.

## The contract with the reader

Assume the human: is not an expert in this domain, has not read the codebase, skims one
screen, and will answer from their phone. Therefore:

1. **The question fits in the title**, answerable with a word or two.
2. **Context from zero.** Two or three sentences: what part of the system this touches,
   why the question came up now. Link every source (the task, the code, the doc) — the
   link is for depth, never a requirement.
3. **Options with example consequences.** For each option: what it means in plain
   language, then a *concrete scenario* of life after choosing it — "If we pick A and a
   user does X, then Y happens." The example consequence is the most important part of
   the file: it is how a non-expert experiences the difference between options.
4. **A recommendation and a default path.** Say which option you'd pick and why in one
   sentence. State what happens if the human never answers (`async` mode: you proceed
   on the default after the stated date; a `Blocking: yes` decision instead says what
   stays stopped).
5. **The answer slot is literal**: end with `**Your answer:** ______`. Accept anything
   written there — a letter, a sentence, a counter-question. A counter-question gets
   answered in the file, with examples, and the item stays open.
6. **The file is disposable context, not an artifact.** Durable background belongs in
   the task's `design.md` or `memory/`, linked from here — never written only here. A
   well-made decision file could be deleted and regenerated from its sources; the only
   thing it ever uniquely holds is the human's answer, which folding moves into docs
   and an ADR before the file is deleted.

## Example (abridged)

> **Should the quote API store quotes in a JSON file or SQLite?**
> Option A — JSON file: human-readable, diffable in git. *Example consequence: two
> agents writing quotes at the same time can corrupt the file; you'd see occasional
> lost quotes.* Option B — SQLite: safe concurrent writes. *Example consequence: the
> data stops being reviewable in a pull request; you'd need a tool to inspect it.*
> Recommendation: A, our writes are single-threaded today. Default path: A, starting
> 2026-08-01.

## After the answer

Fold the answer into the affected docs, record an ADR in `memory/decisions/` (schema:
`templates/memory/adr.md`) so the reasoning survives, then delete the queue file — git
history is the archive.
