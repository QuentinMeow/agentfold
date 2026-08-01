# Writing decisions humans can actually answer

A decision file is an interface between an agent with full context and a human with
none. Most unanswered decisions are unanswerable — they assume knowledge the human
doesn't have. General rules for every human action:
`human-action-guide.md`; schema: `templates/queue/decision.md`. This guide adds the
decision-specific content.

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
4. **A recommendation and dependency timing.** Say which option you'd pick and why in
   one sentence. The filename and its matching timing block carry when the choice stops
   work; `message-queue/AGENTS.md` owns that rule.
5. **The answer slot is literal**: end with `**Your answer:** ______`. Accept a letter,
   sentence, or counter-question; the first concrete response is immutable. For a
   counter-question, claim and fold that disposition, answer it in the named durable
   evidence, then create a new same-timing item whose `Supersedes` names the old path.
   Never edit human text; claim `folding` with a status-only commit.
6. **Background is reconstructable; delivery state is not.** Durable background belongs
   in the task's `design.md` or `memory/`, linked from here — never written only here.
   The live file uniquely owns the unresolved action, timing, status, and any answer;
   do not delete it until those are folded or explicitly disposed.

## Example (abridged)

> **Should the quote API store quotes in a JSON file or SQLite?**
> Option A — JSON file: human-readable, diffable in git. *Example consequence: two
> agents writing quotes at the same time can corrupt the file; you'd see occasional
> lost quotes.* Option B — SQLite: safe concurrent writes. *Example consequence: the
> data stops being reviewable in a pull request; you'd need a tool to inspect it.*
> Recommendation: A, our writes are single-threaded today. Default path: A, starting
> 2026-08-01.

## After the answer

Fold the answer (or the answer to a counter-question) into the affected docs, record an
ADR in `memory/decisions/` (schema: `templates/memory/adr.md`) when a decision was made,
then delete the resolved item. A counter-question also gets the linked successor above;
Git history archives completed delivery but does not replace live state.
