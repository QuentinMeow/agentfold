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
6. My working assumption repeats one shown reading's `### ` label text; its
   counter-case sits beside it. The check compares text, so paraphrasing fails.
7. No machine field, hash, or token appears above the answer line.
8. Each decisive source is quoted and linked at its heading or selected lines;
   optional background and machine copies stay in For the record. See the source
   excerpt guidance in templates/README.md.
9. Under 800 words before the answer, and you never have to guess where you are:
   `python3 automation/reconcile/reconcile.py --word-count <this file>` prints
   your count against the budget. Four choices cost about 700 on their own, so
   cut background, never a choice, its example consequence, or a quoted source.

Three shapes a checker enforces that nothing else shows you:
- Every **Key:** value and every *Example consequence:* is read one physical line at
  a time. Wrap one onto a second line and the reader sees the whole sentence while
  every check sees only its first half. Keep each on one line, however long.
- Confidence is exactly `high`, `medium` or `low`, then a space, an em dash (U+2014),
  a space, and what you checked and did not. A hyphen or a bare adjective is refused.
- There is no **Look-at:** field. Say where to look in the prose, and put the
  machine copy in Full context.

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

<One or two short value-neutral paragraphs from zero context. This must stand alone: the
reader should be able to answer without opening anything.>

> <the source's own words — the sentence that decides this, copied, not paraphrased>
>
> — [<what this passage says>](<../../../ path to the file.md#heading-anchor>)

<Quote each decisive source; a comparison quotes both sides. Link a Markdown heading,
or bounded lines with #Lx or #Lx-Ly for text or code. Preserve wording and case; wrapping,
emphasis, and marked omissions in source order are allowed. If no source wording decides
the answer, replace this whole source block with exactly
`> No source document — everything you need is above.` A local-file review still quotes
its target. Put optional background below the answer, inside the fold.>

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

Answer in plain words — one sentence is enough. You never need to copy anything; the agent
that folds it shows you how it read your words before acting. If this page did not give you
enough to decide, say so and say what is missing — that is a complete answer, not a
rejection.

**Your answer:** ______

## For the record

<details>
<summary>For the record — bookkeeping the reconciler reads. Nothing here needs you.</summary>

**Status:** waiting  
**Filed:** < YYYY-MM-DD >, by < who >[, from task `<id>`]  
**Full context:** `<root-relative path to the durable source>`  
**Resolution evidence:** `<durable non-queue file that folding this answer will change>`  
**Answer by:** < UTC YYYY-MM-DD — 90 days from Filed unless something real dates it >

</details>

<!-- Status ships as `waiting`, the only status a newly filed item may hold; the
folding agent moves it to `folding` on its claim edge.
Then exactly one timing field matching the filename:
blocking-*   -> Blocks now: <task:<id> | transition:<name> | operation:<name>>
future-blocking-* -> Blocks at: <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
non-blocking-* -> neither; If you do nothing above is the unattended outcome.
A needs-human item may bind only transition:start on a 0_backlog task, or
operation:<name> for one act with no undo. Merging, moving a task, and recording it
done never wait on an answer (message-queue/AGENTS.md owns this rule).
Add External assignment / External source only for a provider binding. A concrete
response is immutable: if it is a counter-question, fold the answer into Resolution
evidence and create a same-timing successor naming this path in Supersedes. -->
