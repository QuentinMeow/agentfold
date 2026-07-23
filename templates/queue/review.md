<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

# <The review judgment needed, one line>

**Status:** <awaiting-artifact | waiting>
**Filed:** <YYYY-MM-DD>, by <who>, from <task id — link>
**Action:** <approve, request a named change, or state another disposition>
**Full context:** [<complete source, diff, or artifact>](<repo-relative path>)
**Review target:** <pending while awaiting-artifact | exact repo file or HTTPS artifact>
**Review revision:** <pending | sha256:<64 hex> | git:<full id> | git:<base>...<head>>
**Reviewed revision:** ______

<!-- Replace this comment with exactly one block matching the filename:
blocking-*:
**Blocks now:** <task:<id> | transition:<name> | operation:<name>>

future-blocking-*:
**Blocks at:** <YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
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

<!-- When answering, copy Review revision into Reviewed revision. A changed target or
revision invalidates any older response until both response fields are cleared. -->
