<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

# <What you want, one line>

**Status:** <open | in-repair>
**Filed:** <YYYY-MM-DD>, by <who>, from <task id / context — link>
**Action:** <the concrete action the receiving agent should take>
**Full context:** [<complete source>](<repo-relative path>)
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

non-blocking-*:
**If unanswered:** <the explicit safe outcome; this message will never stop work>
-->

## What you need to know

<A self-contained summary of why the action is needed and the relevant current state.
The Full context link supplies depth rather than missing prerequisites.>

## Done when

<An observable result the receiving agent can verify before deleting the request.>
