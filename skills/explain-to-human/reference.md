# The craft — explaining work to someone who was not there

`SKILL.md` states the rules. This file says what each one is for, how to apply it, and
what it looks like when applied badly. Read the section you need; nothing here has to be
read in order.

Everything below assumes one reader: a competent engineer who knows general software
engineering, does not know this system, did not watch the work happen, and is deciding
rather than implementing. Write the difference between what they know and what they need
— nothing above that line, nothing below it.

## Contents

- [Why layering, and how to layer](#why-layering-and-how-to-layer)
- [Effect over mechanism](#effect-over-mechanism)
- [Before and after](#before-and-after)
- [Jargon: gloss, or do not use](#jargon-gloss-or-do-not-use)
- [Worked examples: when one is required](#worked-examples-when-one-is-required)
- [Self-containment: what to inline, what to link](#self-containment-what-to-inline-what-to-link)
- [Sentences, paragraphs, and the actor](#sentences-paragraphs-and-the-actor)
- [Tables, lists, and diagrams](#tables-lists-and-diagrams)
- [Saying how sure you are](#saying-how-sure-you-are)
- [Asking for a decision](#asking-for-a-decision)
- [The anti-pattern table](#the-anti-pattern-table)
- [Where these rules come from](#where-these-rules-come-from)

## Why layering, and how to layer

A reader of a screen of text reads roughly a quarter of the words. Whatever is at the
bottom is not read, and a decision at the bottom is a decision nobody made. So the order
is fixed: conclusion first, then context, then evidence.

The three layers are not three lengths of the same text. They answer three different
questions.

| Layer | Answers | Length | Where it lives |
|---|---|---|---|
| 1 | Do I need to do anything? | one sentence | title, first line, `Action` field |
| 2 | What is different, and why? | one paragraph, ≤4 moving parts | the summary block |
| 3 | How exactly, and how do you know? | as long as it needs to be | folded section, linked file |

Layer 2 has a fixed internal order that works every time: **what was true before → what
broke or changed → what is true now → why that was the right response**. If you cannot
write those four sentences, you do not yet understand the change well enough to report it.

A worked layer 2, for a change to a merge check:

> Until this change, a pull request could merge while one of its own review requests was
> still unanswered, because the merge check only looked at reviews filed before the branch
> was cut. A branch that filed its own review therefore blocked itself forever, and three
> branches were stuck that way. The check now skips an action the range itself created and
> reports it again at the next boundary. Nothing that was already answered is skipped, so
> the gate still holds for every review that predates the branch.

Four sentences, no jargon that is not glossed elsewhere in the document, and a reader who
stops there can decide whether to look closer.

**Do not narrate chronologically.** The order in which you discovered things is almost
never the order in which they matter. Rank by what the reader must decide.

## Effect over mechanism

The most common failure in agent-written reports is describing machinery to a reader who
needs behaviour. "Function A now calls function B" is unreadable: the reader does not know
what A or B take, what they return, or what changes as a result. They must guess, and a
guess about a system they cannot see is dangerous.

Whenever you name a function, module, flag, or file, add three things: **what goes in,
what comes out, and what is now different**.

- Mechanism: "`check_queue_schema` now takes `candidate_revision`."
- Effect: "The schema check now reads the queue item as it exists in the commit being
  judged, not as it exists on disk. Before, a check run on an old branch could pass using
  a newer file that branch had never seen."

The same rule applies to the summary of a whole change. "Refactored the projection layer"
names an activity. "A handover is now judged by the rules that existed when it was
written, so an old branch stops failing on a rule invented after it was cut" names an
effect.

**The test:** delete every proper noun from your sentence. If nothing meaningful survives,
you described mechanism.

The test applies to prose. A table row whose first column already names the files is
allowed to describe mechanism in its last column — the row's identity supplies the context
the sentence would otherwise need.

## Before and after

Every claim that something changed owes the reader two states. Without both, the reader
cannot tell whether the change is an improvement, a regression, or a no-op.

The shape is `<what changed> → <observable difference>`. Anything that cannot be written
in that shape is not a summary line; it is an appendix line.

| Instead of | Write |
|---|---|
| Improved queue validation | A queue filename with a space used to create a second, empty item silently. It is now refused with `invalid item name: 'my item.md'`. |
| Various fixes | Three reconciler checks stopped re-reading the same Git object per file; a full check went from 41s to 6s on this repository. |
| Added an index | Dashboard load for accounts with more than 10,000 rows went from about 9s to about 2s. |

For a change with more than one before/after pair, use a two-column table rather than
prose. A reader comparing two states in prose has to hold both in memory; a table holds
them for the reader.

When the change is a *workflow* rather than a value — the steps someone takes, or the
order in which a system does things — show both workflows end to end, not just the step
that changed. A step in isolation cannot be judged.

## Jargon: gloss, or do not use

Assume the reader knows general software engineering and nothing specific to this system.
This is the exemption list — never gloss these, because expanding them reads as
condescension: commit, branch, merge, test, API, cache, race condition, schema, index,
timeout, retry. Everything local to this repository, this domain, or this change gets a
parenthetical gloss the first time it appears in each document.

Rules that keep glossing from becoming noise:

- **Gloss at first use, once per document.** Not once per section, not every time.
- **Use one name for one thing.** Alternating between "queue item", "action file", and
  "message" makes a reader look for three things. Pick one and keep it.
- **Attach a noun to every "this" and "that".** "This retry", not "this".
- **Repeat the noun if it is more than about five words from its pronoun**, and always if
  another noun sits between them.
- **Never verb an acronym.** "Use SSH to connect", not "SSH into".

Bad, then good:

- "The reconciler validates MQ items against the ADR index and it fails if they drift."
- "The reconciler (the script that checks every repository invariant) compares
  message-queue items against the decision-record index. The reconciler fails the commit
  if the two disagree."

If a sentence needs three glosses, the sentence is doing too much. Split it.

## Worked examples: when one is required

An example is the cheapest way to make an abstract claim concrete, and the most expensive
way to pad a document. Both matter, so the rule is conditional.

**Include a worked example when** the claim is a behaviour change the reader cannot
picture; the claim is counterintuitive; the claim is the one the reader must act on; or
the term is new in this document.

**A sentence is enough when** the claim is a magnitude ("three files changed"), the reader
already holds the concept, or the example would only restate the sentence.

**Never write two examples of the same point.** The second one does not reinforce; it
signals that you did not trust the first. Replaying one example twice — once showing the
old behaviour and once the new — is a single example, and is the standard way to show a
change.

A worked example has three parts and no more: the input, what the system did, the output.

> A branch files a review of its own design, then merges. Before: the merge check reported
> that review as unresolved, and the merge was refused forever, because no later commit
> could answer a review the range itself created. After: the merge proceeds, the review
> stays live, and the next boundary — a later merge, or the task's completion — reports it
> again.

## Self-containment: what to inline, what to link

One rule decides every case:

> **Inline anything whose being different would change the reader's answer. Link anything
> that only explains how you know.**

Inline: the ask, the options, what each option costs, the recommendation, the deadline,
the reversibility, the assumptions, and every number that appears in your reasoning.

Link: logs, benchmark runs, transcripts, source files, the prior discussion, the full
analysis, and the derivation of any number you inlined.

A reader deciding whether to approve a change needs the *effect* of the root cause, not
the root-cause investigation. "The lock was held across an I/O call, so two agents could
both pass the check" is inline. The four hours of tracing that established it is a link.

**Every evidence link states what is behind it and why the reader does not have to open
it.** A bare link is an unstated dependency, and a reader who has to open it to understand
the sentence is reading an incomplete document.

The exception is a link the reader is being sent to on purpose — the queue item they are
being asked to answer. That link is the action, not evidence, so its label is the action
and no "you need not open this" is added to it.

There are three rungs, and most writing stops one too early.

- Bare: "See `docs/designs/queue-resolution-order-independence.md`." Backticks render as
  code, so this is clickable nowhere, and it names a whole document without saying which
  part of it matters.
- Annotated: "The full ordering proof is in
  [the queue-resolution design](../../docs/designs/queue-resolution-order-independence.md)
  — you do not need it to answer this; it only shows why the two orders cannot diverge."
- Quoted — the rung to use whenever the reader's answer turns on what that document
  actually says:

  > The gate proves *the deletion commit also touched the named file*. It has never proved
  > that the work happened, and it cannot.
  >
  > — [what the evidence gate actually proves](../../docs/designs/queue-resolution-order-independence.md#finding-1--the-gate-is-already-empty)

Annotated is right for evidence the reader may safely skip. Quoted is required when the
sentence decides the question, because a summary of it is the one thing they cannot check.

Link the heading, never the file: a long document with no anchor is not a pointer, it is a
reading assignment. Quote the sentence that decides it, not the section around it. And
never quote *and* summarize the same passage — the summary is the half the reader cannot
check, so it is the half to cut.

## Sentences, paragraphs, and the actor

These are mechanical and worth applying literally.

| Rule | Threshold |
|---|---|
| One idea per sentence | always |
| Sentence length | average around 15–20 words; rewrite anything over 25 |
| Paragraph | one topic, at most five sentences |
| Moving parts a reader holds at once | at most four; beyond that, split or tabulate |
| Restating an earlier point | always, rather than making the reader scroll back |

**Active voice, and name the actor.** Passive voice hides who did something, and in a
report written by an agent that is exactly the information the reader wants: did you do
it, did the test suite do it, or does the human still have to?

The detector: add "by zombies" after the verb. If the sentence still parses, it is passive.
"The tests were run by zombies" parses — rewrite it. "I ran the tests by zombies" does not
— leave it.

**Free the trapped verb.** Nouns ending in *-tion*, *-ment*, *-ance*, or *-ity* usually
have a verb inside them.

- "Implementation of the validation resulted in a reduction in failures."
- "Validating the input cut failures by 80%."

**Banned words**, because they tell the reader their confusion is their own fault, or say
nothing: *just*, *simply*, *obviously*, *it's easy*, *as discussed*, *various fixes*,
*please note*. Also avoid metaphor and idiom; they are the first things a reader who is
skimming misreads.

## Tables, lists, and diagrams

- **Two or more attributes per item → table.** One attribute → list. No comparison → prose.
- Keep every cell in a column grammatically parallel. Mixing "Fixes the race" with
  "Race condition" in one column forces the reader to re-parse each row.
- Never leave a cell blank. Write `none` or `not applicable`.
- Put the identifying column first.
- **Do not use bullets where two facts are causally linked.** Bullets hide the connective
  tissue: if B happens because of A, write the sentence that says so. Lists of genuinely
  independent items — files, out-of-scope things, options — are exactly what lists are for.

Reach for a diagram only when the thing you are explaining is a *path* — an ordering, or a
branch — rather than a state. For a state comparison, a before/after table is better and
costs nothing. When a diagram genuinely helps:

- **Sequence diagram** for "what talks to what, in what order".
- **Flowchart** for "what happens under which condition".
- **Before/after table** for everything else.

GitHub renders Mermaid diagrams inside a fenced block tagged `mermaid`, including inside a
collapsed `<details>` section, so a diagram can live in the depth layer without costing the
skimming reader anything.

## Saying how sure you are

Vague hedging is worse than either confidence or doubt, because the reader cannot tell
which one you meant. "Serious possibility" once meant 65% to its author and something else
entirely to every reader.

Write a number, a confidence, and the one clause of evidence behind it:

> The remaining two failures are probably environmental (~70%, medium confidence — both
> only fail when the suite runs in parallel, and both pass in isolation on this machine).

Round to multiples of 5. Separate the two things people conflate: **likelihood** is how
probable the outcome is; **confidence** is how good your evidence is. You can be highly
confident that something is unlikely.

**When you have no basis for a number, say that instead.** "Unknown — I did not measure
this" is a complete and honest answer. A number invented to satisfy this rule is a
fabricated measurement, which is worse than the hedge it replaced.

Never report a status as green while an open risk contradicts it. If the status is good
and a risk is open, say what would have to be true for the risk to close.

## Asking for a decision

A decision request that comes back as a question was written wrong. Seven properties make
one answerable; missing any single one produces a predictable failure.

| Property | Failure when missing |
|---|---|
| One named decider | "Who is deciding this?" |
| A closed question — answerable with a choice, not "thoughts?" | "It depends" |
| Two to four options, never more | Deferral |
| A stated recommendation | "What do you think we should do?" |
| Assumptions listed separately from facts | The whole request bounces instead of one assumption |
| The default if nobody answers, and what it costs | Indefinite deferral |
| Reversibility, with the cost of reversing | Over-deliberation on a cheap, reversible call |

Present the options as **one table with a shared set of rows** — the same three to five
criteria for every option — not as one narrative paragraph per option. Narratives are not
comparable, so the reader ends up building the table themselves.

Say the door type in the first three lines: *reversible in about a day behind a flag*, or
*not reversible — undoing it means rewriting published history*. This repository's
schema for those files, and the lifecycle around them, live in `templates/queue/` and
`handbook/human-action-guide.md`; this section only says how to write the prose that fills
them. `scenarios/queue-item.md` connects the two.

## The anti-pattern table

| Anti-pattern | Why it fails | Repair |
|---|---|---|
| "Function A calls function B" | The reader cannot see A or B, so the sentence carries no information | Add what goes in, what comes out, what is now different |
| Unexpanded local term | The writer cannot feel the gap, because they already know it | Gloss at first use |
| Passive voice with no actor | The reader cannot tell whether they still owe something | Zombie test, then name the actor |
| The ask at the bottom | Most readers stop before the bottom | First sentence |
| Narrating your own process in order | Your discovery order is not their priority order | Rank by what they must decide |
| A number with no baseline or unit | Unfalsifiable, so unreadable | Give the before value, the after value, and how it was measured |
| "Various fixes", "improved performance" | Says nothing and cannot be checked | Name the fix and its observable effect |
| A wall of text | Undifferentiated text is skimmed and then abandoned | Headings, ≤5-sentence paragraphs, a summary block |
| Bullets that hide causation | The reader cannot see why B follows A | Write the sentence that links them |
| Two examples of one point | Reads as distrust of the first example | Delete one |
| A bare link mid-argument | An unstated dependency | Say what is behind it and why they need not open it |
| Green status beside an open risk | The reader learns later, and trusts the next report less | State the risk and what would close it |

## Where these rules come from

The rules above are not invented here. They are the durable, repeatedly-validated parts of
several fields that solved the same problem: getting a decision from someone who was not
present.

- **Conclusion first** — US Army writing regulation (bottom line up front) and the Minto
  pyramid principle used in consulting: state the answer, then support it.
- **Layered disclosure** — Nielsen Norman Group's progressive-disclosure work and the
  inverted pyramid from journalism. The measured reading behaviour behind "put it at the
  top" is theirs.
- **Narrative over bullets, and an appendix that is not required reading** — Amazon's
  written-memo culture.
- **Explanation is its own genre**, separate from tutorials and reference material — the
  Diátaxis documentation framework. A status report is explanation: it exists to make
  someone understand, not to teach them to operate anything.
- **The curse of knowledge**, and concrete language as its antidote — Camerer, Loewenstein
  and Weber's original result, popularised in *Made to Stick*.
- **Worked examples, and when they stop helping** — cognitive load theory's worked-example
  effect and the expertise-reversal effect that limits it.
- **Sentence and paragraph thresholds, active voice, freeing trapped verbs** — the Google
  developer documentation style guide, the Microsoft writing style guide, and plain-language
  guidance from plainlanguage.gov and GOV.UK.
- **Structured handover** — the SBAR and I-PASS protocols from medicine, where a handover
  that loses information hurts someone. The measured finding that written handovers survive
  and verbal ones do not is why this repository keeps files, not chat.
- **Calibrated uncertainty** — the IPCC's split between confidence and likelihood, and
  Sherman Kent's work on words of estimative probability.
- **Reversible versus irreversible decisions** — the two-way-door framing, which this
  repository already uses in `handbook/collaboration-modes.md`.
