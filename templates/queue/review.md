<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

# <The review judgment needed, one line>

**Status:** <awaiting-artifact | waiting | folding>
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <approve, request a named change, or state another disposition>
**Full context:** [<stable design, ADR, or evidence>](<repo-relative path>)
**Resolution evidence:** `<non-queue path distinct from Review target>`
<!-- For a provider assignment, add exactly one **External assignment:** <opaque
stable-artifact, role, actor-kind, and principal binding emitted by its adapter>.
Omit it otherwise. -->
<!-- For an active provider source, add exactly one **External source:** <opaque
versioned identity emitted by its adapter>, even when provider prose links here. -->
**Why-you-might-care:** <one sentence explaining the practical consequence>
**If-you-do-nothing:** <one sentence stating the boundary or unattended outcome>
**Review target:** <pending | `repo/path` | [label](repo/path) | git:<full id or base...head> | one HTTPS URL/link>
**Review revision:** <pending | sha256:<64 hex> | git:<full id> | git:<base>...<head>>
**Reviewed revision:** ______
**Review outcome:** <pending | approved | changes-requested | rejected | abandoned>

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
rejected declines the proposal and abandoned ends pursuit; neither authorizes a
boundary. Cleanup removes a task pursuit, restores a Git candidate to its base, or
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
