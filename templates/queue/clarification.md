<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

# <The clarification, one sentence>

**Status:** <waiting | folding>
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <answer the question or correct the stated understanding>
**Full context:** [<complete source>](<repo-relative path>)
**Why-you-might-care:** <one sentence explaining the practical consequence>
**If-you-do-nothing:** <one sentence stating the boundary or unattended outcome>
**Resolution evidence:** `<durable file that folding this answer will change>`

<!-- Replace this comment with exactly one block matching the filename:
blocking-*:
**Blocks now:** <task:<id> | transition:<name> | operation:<name>>

future-blocking-*:
**Blocks at:** <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
**Until then:** <the explicit safe assumption or path while work continues>

non-blocking-*:
**If unanswered:** <the explicit safe outcome; this message will never stop work>
-->

## What you need to know

<2–3 sentences from zero. Explain what prompted the question, the current understanding,
and what a different answer changes. This summary must stand alone; the Full context
link supplies depth rather than missing prerequisites.>

## Differences

<Describe at least two meaningful answers or interpretations and the consequence of
each. Make the distinction concrete enough that the reader knows what they are choosing.>

## Example

<One small scenario showing how the alternatives produce different behavior or work.>

**Your answer:** ______
