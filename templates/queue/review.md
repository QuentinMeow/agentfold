<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

# <The review judgment needed, one line>

**Status:** <awaiting-artifact | waiting | folding>
**Filed:** <YYYY-MM-DD>, by <who>, from task <task id>
**Action:** <approve, request a named change, or state another disposition>
**Full context:** [<stable design, ADR, or evidence>](<repo-relative path>)
<!-- For a provider assignment, add exactly one **External assignment:** <opaque
stable-artifact, role, actor-kind, and principal binding emitted by its adapter>.
Omit it otherwise. -->
<!-- For transcribed or structurally triaged provider content, add exactly one **External source:** <opaque
versioned source identity emitted by its adapter>. Omit it otherwise. -->
**Why-you-might-care:** <one sentence explaining the practical consequence>
**If-you-do-nothing:** <one sentence stating the boundary or unattended outcome>
**Review target:** <pending | one repo file | git:<full id or base...head> | one HTTPS artifact>
**Review revision:** <pending | sha256:<64 hex> | git:<full id> | git:<base>...<head>>
**Reviewed revision:** ______
**Review outcome:** <pending | approved | changes-requested | rejected | abandoned>

<!-- approved accepts the bound revision and is response-terminal with no successor.
Keep a future-blocking review folding and live through its boundary; approval may
satisfy the boundary only while fresh. A Git-range approval permits queue-lifecycle
tail changes on the same base. Historical future timing survives any later escalation.
Post-merge deletion requires an exact receipt-carrying merge already in the
adapter-supplied target base; a candidate-local merge does not qualify.
changes-requested preserves the boundary. Before deleting, add **Successor action:**
`<new needs-agent queue path>` here. That new same-timing open action owns the repair
in Action, keeps Full context, predeclares non-queue Resolution evidence, and points
back with Supersedes. It must also link one distinct same-timing **Follow-up review:**
that is newly awaiting-artifact, points back with Supersedes, and names the repair in
Depends on. The follow-up Action is the later judgment, never a copy of the repair.
rejected declines the proposal and abandoned ends pursuit; neither authorizes a future
boundary. Legacy
**Review outcome:** not-approved remains accepted as changes-requested. -->

<!-- Replace this comment with exactly one block matching the filename:
blocking-*:
**Blocks now:** <task:<id> | transition:<name> | operation:<name>>

future-blocking-*:
**Blocks at:** <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
**Until then:** <the explicit safe path while work continues>

non-blocking-*:
**If unanswered:** <the explicit safe outcome; this message will never stop work>
-->

## What you need to know

<2–3 sentences from zero. Explain what changed or is proposed, why judgment is needed,
and what the review can affect. This summary must stand alone; the Full context link
supplies depth rather than missing prerequisites.>

## Differences

<Describe the meaningful review dispositions and what each causes. For example, explain
the difference between accepting the current boundary and requesting a specific change;
do not use unexplained approval shorthand.>

## Example

<One small scenario showing the practical consequence of two different review outcomes.>

**Your review:** ______

<!-- Status-folder task paths move and are not durable context. When answering, copy
Review revision into Reviewed revision. Git revisions must name locally available
commit objects. If an unanswered waiting target becomes stale, retract it in one commit:
set Status to awaiting-artifact, target/revision to pending, and keep response/reviewed
blank with outcome pending. Publish the replacement in a later awaiting-artifact ->
waiting commit. Neither lifecycle edge may add a response; the first response freezes
the binding forever. -->
