<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

# <The decision, one sentence, answerable in a word or two>

**Status:** <waiting | folding>
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <choose one option, or state another choice>
**Full context:** [<complete source>](<repo-relative path>)
<!-- For a provider assignment, add exactly one **External assignment:** <opaque
stable-artifact, role, actor-kind, and principal binding emitted by its adapter>.
Omit it otherwise. -->
<!-- For an active provider source, add exactly one **External source:** <opaque
versioned identity emitted by its adapter>, even when provider prose links here. -->
**Why-you-might-care:** <one sentence explaining the practical consequence>
**If-you-do-nothing:** <one sentence stating the boundary or unattended outcome>
**Resolution evidence:** `<durable file that folding this answer will change>`

<!-- Replace this comment with exactly one block matching the filename:
blocking-*:
**Blocks now:** <task:<id> | transition:<name> | operation:<name>>

future-blocking-*:
**Blocks at:** <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
**Until then:** <the explicit safe path while work continues>
Dates are clock-checkable. An event/custom transition is agent-attested unless a
controlled adapter validates and enforces its crossing.

non-blocking-*:
**If unanswered:** <the explicit safe outcome; this message will never stop work>
-->

## What you need to know

<2–3 sentences from zero — no domain expertise assumed. What part of the system,
why the choice came up now, and what the answer will change. This summary must stand
alone; the Full context link supplies depth rather than missing prerequisites.>

## Differences

<Compare the meaningful alternatives in plain language. Name the trade-off or boundary
that changes; do not merely repeat the option labels.>

## Options

### Option A — <short name>
<What it means in plain language.>
*Example consequence:* <concrete scenario of life after choosing A.>

### Option B — <short name>
<Same shape.>
*Example consequence:* <concrete scenario.>

## Recommendation

<A or B, one sentence why.>

**Your answer:** ______

<!-- A concrete response is immutable. If it is a counter-question, fold the answer into
Resolution evidence and create a same-timing successor with **Supersedes:** `<this path>`. -->
