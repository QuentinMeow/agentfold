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

# <What you want, one line>

**Status:** open
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <the concrete action the receiving agent should take>
**Full context:** [<complete source>](<repo-relative path>)
**Resolution evidence:** `<durable file completion will create or change>`
**If unanswered:** <the explicit safe outcome; this message will never stop work>

<!-- Optional fields, added only when they apply. Add **Request kind:** task-pickup only
for the canonical pickup request of one unclaimed backlog task; other request kinds may
define their own explicit value. For a provider assignment, exactly one
**External assignment:** <opaque stable-artifact, role, actor-kind, and principal binding
emitted by its adapter>. For an active provider source, exactly one **External source:**
<opaque versioned identity emitted by its adapter>, even when provider prose links here.
A changes-requested review successor also adds **Supersedes:** `<old review path>` and
**Follow-up review:** `<new human review path>`. The follow-up is a distinct
awaiting-artifact judgment with **Depends on:** `<this request path>`; do not repeat this
request's repair Action as the review Action. -->

## What you need to know

<A self-contained summary of why the action is needed and the relevant current state.
The Full context link supplies depth rather than missing prerequisites.>

## Done when

<An observable result the receiving agent can verify before deleting the request.>
