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

# <Ask the clarification as one clear question>
<!-- human-action-presentation: v2 -->

> **Waiting for your response.**

## What I need from you

**Action:** <Choose the interpretation that matches your intent, correct it, or ask a follow-up question.>

<One sentence saying which uncertainty the answer must resolve.>

## Why this matters

<One compact paragraph explaining the practical consequence. This paragraph and the
`If you do not respond` paragraph are each at most 240 normalized rendered characters
and at most 400 combined. End each in `.`, `?`, `!`, `。`, `！`, or `？`, optionally
before a balanced closing quote or bracket. Multiple sentences are fine. Do not add
links or block Markdown.>

## If you do not respond

If you do not respond, <use one compact paragraph to state the assumption or safe path
that applies. Follow the shared length and punctuation limits above.>

## Current understanding

**Today:** <State what the agent currently believes or is doing. Distinguish observed
behavior from an interpretation.>

**What is unclear:** <State the exact ambiguity or missing intent.>

<!-- Write these fields from zero context. Name what prompted the question and what a
different answer would change. A reader must not need the references to answer. -->

## Possible interpretations

### Interpretation A — <short, neutral name>

**What it would mean:** <Explain this interpretation in plain language.>

**Consequence:** <State what the agent or system will do if this is correct.>

**Example:** <Give one concrete scenario.>

### Interpretation B — <short, neutral name>

**What it would mean:** <Use the same level of detail and frame as Interpretation A.>

**Consequence:** <State what the agent or system will do if this is correct.>

**Example:** <Give a comparable concrete scenario.>

<!-- Add more interpretations only when they are genuinely distinct. Give every
interpretation the same three labels above. -->

## Agent recommendation

**Evidence checked:** <Name the concrete files, observations, or prior decisions you
  actually inspected before recommending this interpretation.>

**Assumptions:** <State the assumptions behind the recommendation.>

**Confidence:** <High, medium, or low, followed by a plain-language reason.>

**Rationale:** <Explain why one interpretation best fits the available evidence and
  stated intent, without revealing the recommendation before its calibration.>

**What could change this recommendation:** <Name information that would change the
  interpretation.>

**Recommendation:** <Write exactly `Use Interpretation X.` for one interpretation shown above and keep this conclusion on one source line so no prose can follow it.>

## Your response

Write the interpretation name, give a corrected interpretation, or write `I need
clarification` and your question. A plain-language answer is enough.

**Your answer:** ______

<!-- A concrete response is immutable. If it is a counter-question, fold the answer
into Resolution evidence and create a same-timing successor with **Supersedes:**
`<this path>`. -->

## References

**Full context:** [<one complete source for deeper detail>](../../../<repo-relative path>)

<!-- Add only sources that materially help the clarification. Link each target exactly
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
**Until then:** <the explicit safe assumption or path while work continues>
Dates are clock-checkable. An event/custom transition is agent-attested unless a
controlled adapter validates and enforces its crossing.

non-blocking-*:
**If unanswered:** <the explicit safe outcome; this message will never stop work>
-->
</details>
