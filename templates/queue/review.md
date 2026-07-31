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

# <The review judgment needed, one line>

**Status:** waiting
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <approve, request a named change, or state another disposition>
**Full context:** [<stable design, ADR, or evidence>](<repo-relative path>)
**Why-you-might-care:** <one sentence explaining the practical consequence>
**If-you-do-nothing:** <one sentence stating the boundary or unattended outcome>
**Resolution evidence:** `<non-queue path distinct from Review target>`
**Review target:** `<repo-relative path to the exact file being judged>`
**Review revision:** sha256:<64 hex digits of that file's bytes>
**Reviewed revision:** ______
**Review outcome:** pending
**If unanswered:** <the explicit safe outcome; this message will never stop work>

<!-- `Reviewed revision` and `Review outcome` are the folding agent's to fill, never the
human's. The agent copies `Review revision` into `Reviewed revision` and classifies the
committed response in the one claim commit that moves the status from `waiting` to
`folding`; both are write-once and cannot be recorded before the response exists.
See `handbook/human-action-guide.md`. -->

<!-- Optional fields, added only when they apply. For a provider assignment, exactly one
**External assignment:** <opaque stable-artifact, role, actor-kind, and principal binding
emitted by its adapter>. For an active provider source, exactly one **External source:**
<opaque versioned identity emitted by its adapter>, even when provider prose links here. -->

<!-- Other target kinds, instead of the local file above. A Git range uses
**Review target:** git:<base>...<head> with an identical **Review revision:**. An HTTPS
artifact uses one URL with a sha256 revision. Before the artifact exists, file the item
with **Status:** awaiting-artifact and both target and revision literally `pending`, then
publish the binding in one later commit that moves the status to waiting. Full context
explains the judgment; it is never the target. -->

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

<!-- Answering is one edit: replace the blank above with a sentence and commit while the
status is still `waiting`. Nothing else on this page is yours to fill in, and a path you
name in that sentence never has to exist. The first response freezes the binding forever.
If an unanswered waiting target goes stale, retract it in one commit — status
awaiting-artifact, target and revision pending, response and Reviewed revision blank,
outcome pending — then republish in a later commit. Neither edge may add a response. -->
