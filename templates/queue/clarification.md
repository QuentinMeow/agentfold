<!--
Filename: one delivery prefix, then a kebab-case slug. The three prefixes, what each
one means, and the rule that the filename is canonical (so no separate **Blocking:**
field exists) are stated once in `message-queue/AGENTS.md`, under "Routing: three
independent axes". Slug grammar: `handbook/naming-conventions.md`.

Before you file, check all nine. Lifecycle law lives in handbook/human-action-guide.md.
1. The title is a question the owner can answer without knowing this repository.
2. Exactly three fields above the first heading: Action, Why this matters, If you do nothing.
3. Today / What this would change / What this does not decide are true and specific.
4. Two or more readings, each with a cost and a concrete *Example consequence:*.
5. The axis sentence opens Your choices and says what the readings differ on.
6. My working assumption names one reading shown; its counter-case sits beside it.
7. No machine field, hash, or token appears above the answer line.
8. The source is linked once in the prose; For the record keeps the machine copies.
9. Under 700 words before the answer. Cut background, not choices.

An agent recommending an answer to "what did you mean?" puts words in the owner's
mouth. State what you will assume and do instead.
-->

# <The question the owner can answer, in plain English>

**Action:** <one imperative sentence; handovers copy this verbatim as the link label>
**Why this matters:** <one sentence of consequence in the world, not in the repository>
**If you do nothing:** <one sentence: what stops, and what safely continues>

## What you need to know

**Today:** <what actually happens now — say "nothing is implemented" when that is true>
**What this would change:** <the delta a different reading would produce>
**What this does not decide:** <adjacent things a reader will assume are in scope>

<One or two short value-neutral paragraphs from zero context. Link the source exactly
once, here, as [<descriptive label>](<../../../ path to the file>). This must stand
alone: the reader should be able to answer without opening anything.>

## Your choices

<One sentence naming the axis the readings differ on. Not a restatement of them.>

### Reading A — <short name>
<What this would mean, and what an agent would then do. Name at least one cost.>
*Example consequence:* <a concrete scenario of life after this answer>

### Reading B — <short name>
<Same shape. Two readings is the minimum; never pad one nobody would mean.>
*Example consequence:* <a concrete scenario of life after this answer>

## What I recommend

**My working assumption:** <exactly one of the readings above> — <one sentence why>
**Strongest case against this:** <the best argument for a different reading>
**Confidence:** <high | medium | low> — <what you checked, and what you did not>

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** <waiting | folding>
**Filed:** <YYYY-MM-DD>, by <who>[, from task `<id>`]
**Full context:** `<repo-relative path to the durable source>`
**Resolution evidence:** `<durable non-queue file that folding this answer will change>`
**Answer by:** <UTC YYYY-MM-DD — 90 days from Filed unless something real dates it>
<!-- Then exactly one timing field matching the filename:
blocking-*   -> Blocks now: <task:<id> | transition:<name> | operation:<name>>
future-blocking-* -> Blocks at: <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
non-blocking-* -> neither; If you do nothing above is the unattended outcome.
A needs-human item may bind only transition:start on a 0_backlog task, or
operation:<name> for one act with no undo. Merging, moving a task, and recording it
done never wait on an answer (message-queue/AGENTS.md owns this rule).
Add External assignment / External source only for a provider binding. A concrete
response is immutable: if it is a counter-question, fold the answer into Resolution
evidence and create a same-timing successor naming this path in Supersedes. -->
