<!--
Filename: one delivery prefix, then a kebab-case slug. The three prefixes, what each
one means, and the rule that the filename is canonical (so no separate **Blocking:**
field exists) are stated once in `message-queue/AGENTS.md`, under "Routing: three
independent axes". Slug grammar: `handbook/naming-conventions.md`.
-->

# <What you want, one line>

**Status:** <open | in-repair>
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <the concrete action the receiving agent should take>
**Full context:** [<complete source>](<repo-relative path>)
<!-- For a provider assignment, add exactly one **External assignment:** <opaque
stable-artifact, role, actor-kind, and principal binding emitted by its adapter>.
Omit it otherwise. -->
<!-- For an active provider source, add exactly one **External source:** <opaque
versioned identity emitted by its adapter>, even when provider prose links here. -->
**Resolution evidence:** `<durable file completion will create or change>`
<!-- Add **Request kind:** task-pickup only for the canonical pickup request of one
unclaimed backlog task. Other request kinds may define their own explicit value. -->
<!-- A changes-requested review successor also adds **Supersedes:** `<old review path>`
and **Follow-up review:** `<new human review path>`. The follow-up is a distinct
awaiting-artifact judgment with **Depends on:** `<this request path>`; do not repeat
this request's repair Action as the review Action. -->

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

<A self-contained summary of why the action is needed and the relevant current state.
The Full context link supplies depth rather than missing prerequisites.>

## Done when

<An observable result the receiving agent can verify before deleting the request.>
