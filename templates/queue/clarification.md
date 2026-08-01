<!--
Filename: one delivery prefix, then a kebab-case slug. The three prefixes, what each
one means, and the rule that the filename is canonical (so no separate **Blocking:**
field exists) are stated once in `message-queue/AGENTS.md`, under "Routing: three
independent axes". Slug grammar: `handbook/naming-conventions.md`.

This file ships filled in for `non-blocking-`, the one class live timing may always
escalate away from, so a copy is valid before you have decided anything about timing.
To file `blocking-` or `future-blocking-` instead, swap the `If unanswered` line below
for that class's fields, shown once in `templates/README.md`. Every field line here is
real Markdown, so a filled copy of this file is a valid item exactly as it stands;
guidance that is not a field stays inside comments like this one, which the reconciler
blanks before parsing and a filing agent may delete.
-->

# <The clarification, one sentence>

**Status:** waiting
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <answer the question or correct the stated understanding>
**Full context:** [<complete source>](<repo-relative path>)
**Why-you-might-care:** <one sentence explaining the practical consequence>
**If-you-do-nothing:** <one sentence stating the boundary or unattended outcome>
**Resolution evidence:** `<durable file that folding this answer will change>`
**If unanswered:** <the explicit safe outcome; this message will never stop work>

<!-- Optional fields, added only when they apply. For a provider assignment, exactly one
**External assignment:** <opaque stable-artifact, role, actor-kind, and principal binding
emitted by its adapter>. For an active provider source, exactly one **External source:**
<opaque versioned identity emitted by its adapter>, even when provider prose links here. -->

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

<!-- Answering is one edit: replace the blank above with a sentence and commit while the
status is still `waiting`. Nothing else on this page is yours to fill in. A concrete
response is immutable. If it is a counter-question, the folding agent answers it in
Resolution evidence and creates a same-timing successor with **Supersedes:** `<this path>`. -->
