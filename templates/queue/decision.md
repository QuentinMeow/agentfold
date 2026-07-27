<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

<!-- Match the notice to Status exactly:
waiting: `> **Waiting for your response.**`
folding: `> **Response received. No further response is needed.**`
-->

# <Ask the decision as one clear question>
<!-- human-action-presentation: v2 -->

> **Waiting for your response.**

## What I need from you

**Action:** <Choose Option A or Option B, or describe another choice.>

<One sentence saying what answer is needed. Use the same names as the options below.>

## Why this matters

<One compact paragraph explaining the practical consequence. This paragraph and the
`If you do not respond` paragraph are each at most 240 normalized rendered characters
and at most 400 combined. End each in `.`, `?`, `!`, `。`, `！`, or `？`, optionally
before a balanced closing quote or bracket. Multiple sentences are fine. Do not add
links or block Markdown.>

## If you do not respond

If you do not respond, <use one compact paragraph to state exactly what continues,
stops, or happens by default. Follow the shared length and punctuation limits above.>

## Situation

**Today:** <Describe current behavior. Do not mix in a proposal or desired future.>

**Future behavior being decided:** <Describe the change this decision would authorize.
Say explicitly when it is not implemented yet.>

<!-- Write these fields from zero context. Name the part of the system, why the
question came up now, and what the answer will change. A reader must not need the
references to understand the choice. -->

## Options

### Option A — <short, neutral name>

**What it means:** <Explain the option in plain language.>

**Benefits:** <State the main benefits in complete sentences.>

**Costs and risks:** <State the main costs and risks in complete sentences.>

**Example consequence:** <Give one concrete scenario showing life after this choice.>

### Option B — <short, neutral name>

**What it means:** <Use the same level of detail and the same frame as Option A.>

**Benefits:** <State the main benefits in complete sentences.>

**Costs and risks:** <State the main costs and risks in complete sentences.>

**Example consequence:** <Give a comparable concrete scenario.>

<!-- Add more options only when they are genuinely distinct. Give every option the
same four labels above. Do not make the recommended option more detailed than the
others. -->

## Agent recommendation

**Evidence checked:** <Name the concrete files, tests, observations, or prior decisions
  you actually inspected before recommending this option.>

**Assumptions:** <State the assumptions that make this recommendation reasonable.>

**Confidence:** <High, medium, or low, followed by a plain-language reason.>

**Rationale:** <Explain why one option best fits the stated goal and trade-offs, without
  revealing the recommendation before the evidence and uncertainty.>

**What could change this recommendation:** <Name evidence or a changed priority that
  would lead to a different recommendation.>

**Recommendation:** <Write exactly `Choose Option X.` for one option shown above and keep this conclusion on one source line so no prose can follow it.>

## Your response

Write the option name, describe another choice, or write `I need clarification` and
your question. A plain-language answer is enough.

**Your answer:** ______

<!-- A concrete response is immutable. If it is a counter-question, fold the answer
into Resolution evidence and create a same-timing successor with **Supersedes:**
`<this path>`. -->

## References

**Full context:** [<one complete source for deeper detail>](../../../<repo-relative path>)

<!-- Add only sources that materially help the decision. Link each target exactly
once in this file. References add depth; they must not supply missing prerequisites. -->

<details>
<summary>Tracking details</summary>

**Status:** <waiting | folding>
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Resolution evidence:** `<durable file that folding this answer will change>`
<!-- For a provider assignment, add exactly one **External assignment:** <opaque
stable-artifact, role, actor-kind, and principal binding emitted by its adapter>.
Omit it otherwise. -->
<!-- For an active provider source, add exactly one **External source:** <opaque
versioned identity emitted by its adapter>, even when provider prose links here. -->

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
</details>
