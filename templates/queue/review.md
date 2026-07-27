<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

<!-- Match the notice to Status exactly:
awaiting-artifact: `> **Not ready yet. No action is requested.**`
waiting: `> **Waiting for your response.**`
folding: `> **Response received. No further response is needed.**`
-->

# <Ask for one clear review judgment>
<!-- human-action-presentation: v2 -->

> **Waiting for your response.**

## What I need from you

**Action:** <Approve the current review target, request specific changes, or reject it.>

<One sentence naming the judgment needed. Do not ask the human to copy a revision or
edit tracking fields.>

<!-- While Status is awaiting-artifact, prefix the explanatory paragraph above with
exact sentence `No action is needed yet. The review target has not been published.` on
its own source line. Keep Action and the paragraph's remaining explanation stable when publishing. Its recommendation must be exact sentence
`Wait for the exact target before deciding.` until publication. -->

## Why this matters

<One compact paragraph explaining the practical consequence. This paragraph and the
`If you do not respond` paragraph are each at most 240 normalized rendered characters
and at most 400 combined. End each in `.`, `?`, `!`, `。`, `！`, or `？`, optionally
before a balanced closing quote or bracket. Multiple sentences are fine. Do not add
links or block Markdown.>

## If you do not respond

If you do not respond, <use one compact paragraph to state exactly what continues,
stops, or remains unapproved. Follow the shared length and punctuation limits above.>

## What changed

**Before this change:** <Describe the relevant behavior before the reviewed change.>

**Current state:** <Say whether the exact target is absent, published, implemented,
merged, approved, or still awaiting approval. Do not call merged behavior proposed.>

**Change under review:** <Describe exactly what this review will accept, revise, or
reject.>

**Not included:** <Name excluded or future work; write `Nothing; the review target
contains the complete change.` when true.>

**Additional context:** <Explain why judgment is needed now and what it can affect.
  Write from zero context so the reader does not need the references to understand the
  review.>

## Review outcomes

### Approve

**What it means:** <Explain what the exact bound revision is accepted to do.>

**Consequence:** <State which work or boundary approval allows to proceed.>

**Example:** <Give one concrete scenario after approval.>

### Request changes

**What it means:** <Explain that the named changes must be made and reviewed again.>

**Consequence:** <State what remains stopped and what repair work begins.>

**Example:** <Give a scenario comparable to the approval example.>

### Reject

**What it means:** <Explain that the current proposal will not be pursued.>

**Consequence:** <State how the target is withdrawn or restored.>

**Example:** <Give a scenario comparable to the other outcomes.>

## Agent recommendation

**Evidence checked:** <Name the concrete diff, files, tests, or prior decisions you
  actually inspected before recommending this outcome. Do not put an unverified core
  claim here or hide it as an assumption.>

**Assumptions:** <State the assumptions behind the recommendation.>

**Confidence:** <High, medium, or low, followed by a plain-language reason.>

**Rationale:** <Explain why one presented outcome best fits the evidence and stated
  goal, without revealing the recommendation before its calibration.>

**What could change this recommendation:** <Name evidence or a changed priority that
  would lead to another outcome.>

**Recommendation:** <While Status is waiting, write exactly `Approve.`, `Request changes.`, or `Reject.`. While Status is awaiting-artifact, write exactly `Wait for the exact target before deciding.`. Keep this conclusion on one source line so no prose can follow it.>

## Your response

Write `approve`, `request changes`, `reject`, or `I need clarification` followed by
your question. A plain-language answer is enough; the agent manages revision tracking.

**Your review:** ______

<!-- While Status is awaiting-artifact, replace this section's instruction and visible
field with exact sentence `No response is needed until the review target is published.`
Move the still-blank Your review field into Tracking details. When publishing to
waiting, move it back here and restore the plain-answer instruction above. -->

## References

**Full context:** [<one complete source for deeper detail>](../../../<repo-relative path>)

<!-- Link each target exactly once in this file. Full context explains the judgment;
the exact Review target remains machine-managed below and may name the same source
without creating a second visible link. -->

<!-- For a Git commit or range target, add exactly one visible field here:
**Exact review artifact:** [Open the immutable Git artifact](<supported provider commit
or compare URL for this repository, or a repo-relative readable text artifact containing
exact field `**Git review target:** git:<the bound commit or range>`>)
Omit it for a local-file or HTTPS target. This link is the human-readable review
surface; the machine-managed target below is not a substitute. -->

<details>
<summary>Tracking details</summary>

**Status:** <awaiting-artifact | waiting | folding>
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Resolution evidence:** `<non-queue path distinct from Review target>`
**Review target:** <pending | `repo/path` | git:<full id or base...head> | one HTTPS URL>
**Review revision:** <pending | sha256:<64 hex> | git:<full id> | git:<base>...<head>>
**Reviewed revision:** ______
**Review outcome:** <pending | approved | changes-requested | rejected | abandoned>
<!-- While Status is awaiting-artifact, place blank **Your review:** ______ here. -->
<!-- Reviewed revision is machine-managed. A human supplies only Your review; the
agent or adapter binds that response to Review revision while transcribing it. -->
<!-- `abandoned` is agent-managed lifecycle state for pursuit that ends without a human
review judgment. Do not present it as a human review outcome. -->
<!-- For a provider assignment, add exactly one **External assignment:** <opaque
stable-artifact, role, actor-kind, and principal binding emitted by its adapter>.
Omit it otherwise. -->
<!-- For an active provider source, add exactly one **External source:** <opaque
versioned identity emitted by its adapter>, even when provider prose links here. -->

<!-- awaiting-artifact uses pending target/revision. Waiting binds exactly one target:
a local file or HTTPS artifact uses its sha256; a Git target repeats the identical
git:<...> value as Review revision. Full context explains; it is not the target. -->

<!-- approved accepts the bound revision and is response-terminal with no successor.
Keep a future-blocking review folding and live through its boundary; approval may
satisfy the boundary only while fresh. A task start/review/complete boundary reviews
one stable local artifact; its task must remain past the exact receipt transition.
A merge boundary instead reviews git:<base>...<head>; only queue tail commits stay
fresh, and cleanup needs its receipt-carrying merge in the already-admitted target.
Dates close when reached. Named events/custom transitions first escalate to blocking;
custom operations are already blocking. Without a controlled adapter, changed
Resolution evidence is only agent attestation, not independent or hard proof.
changes-requested preserves the boundary. Before deleting, add **Successor action:**
`<new needs-agent queue path>` here. That new same-timing open action owns the repair
in Action, keeps Full context, predeclares non-queue Resolution evidence, and points
back with Supersedes. It must also link one distinct same-timing **Follow-up review:**
that is newly awaiting-artifact, points back with Supersedes, and names the repair in
Depends on. The follow-up Action is the later judgment, never a copy of the repair.
rejected declines the proposal and ends its pursuit. Agent-managed abandoned records a
pursuit that ended without a human judgment; neither outcome authorizes a boundary.
Cleanup removes a task pursuit, restores a Git candidate to its base, or
changes/removes a local target, then changes the distinct Resolution evidence. Legacy
**Review outcome:** not-approved remains accepted as changes-requested. -->

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

<!-- Status-folder task paths move and are not durable context. Git revisions must name
locally available commit objects. If an unanswered waiting target becomes stale,
retract it in one commit: set Status to awaiting-artifact, target/revision to pending,
and keep response/reviewed blank with outcome pending. Publish the replacement in a
later awaiting-artifact -> waiting commit. Neither lifecycle edge may add a response;
the first response freezes the binding forever. -->
</details>
