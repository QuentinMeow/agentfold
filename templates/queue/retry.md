<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

# <The broken invariant, one line>

**Status:** <open | in-repair>
**Filed:** <YYYY-MM-DD>, by <reconciler | agent/session — link>
**Action:** <repair or explicitly reject the finding>
<!-- For a provider assignment, add exactly one **External assignment:** <opaque
role-and-identity binding emitted by its adapter>. Omit it otherwise. -->
<!-- For transcribed provider prose, add exactly one **External source:** <opaque
versioned source identity emitted by its adapter>. Omit it otherwise. -->
**Check:** <reconciler check id, or "manual">
**Subject:** <file/folder the invariant is about — link>
**Resolution evidence:** `<required for manual retries: durable non-queue file completion will create or change; generated retries use finding clearance>`

<!-- Replace this comment with exactly one block matching the filename:
blocking-*:
**Blocks now:** <task:<id> | transition:<name> | operation:<name>>

future-blocking-*:
**Blocks at:** <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
**Until then:** <the explicit safe path while work continues>

non-blocking-*:
**If unanswered:** <the explicit safe outcome; this message will never stop work>
-->

## Broken invariant

<What must be true and isn't — state the end state, not the history.>

## Fix

<Idempotent repair steps — running them twice must be harmless. If the fix is a
judgment call, say what to consider. Reconciler-filed content in this section refreshes
while the finding changes.>

## Agent notes

<Actor-owned diagnosis, claim notes, or rejection reason. A rejected repair moves any
durable judgment to a decision/review item before deletion. Mechanical writers preserve
this section on rerun.>
