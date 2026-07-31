<!--
This template is filled in for a `non-blocking-<slug>.md` filename — the delivery class
that never stops work, and the one live timing may always escalate away from. To file
`blocking-` or `future-blocking-` instead, swap the `If unanswered` line below for that
class's fields; all three are shown once in `templates/README.md`. The filename prefix
is canonical: never add a separate **Blocking:** field. Every field line here is real
Markdown, so a filled copy of this file is a valid item exactly as it stands. Guidance
that is not a field stays inside comments like this one, which the reconciler blanks
before parsing and a filing agent may delete.
-->

# <The decision, one sentence, answerable in a word or two>

**Status:** waiting
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <choose one option, or state another choice>
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

<!-- Answering is one edit: replace the blank above with a sentence and commit while the
status is still `waiting`. Nothing else on this page is yours to fill in. A concrete
response is immutable. If it is a counter-question, the folding agent answers it in
Resolution evidence and creates a same-timing successor with **Supersedes:** `<this path>`. -->
