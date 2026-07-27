<!--
Filename: choose exactly one delivery prefix, then a kebab-case slug:
- blocking-: a named current task, transition, or operation cannot proceed now.
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
- non-blocking-: this message never stops work and names the safe unattended outcome.
The filename prefix is canonical. Do not add a separate **Blocking:** field.
-->

# Pick up the final test-budget investigation

**Status:** open
**Filed:** 2026-07-27, by test-budget filer, from task `2026-07-27-investigate-final-test-budget-7631c3a1b1`
**Action:** Claim the time-budget investigation, preserve its generated evidence, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-27-investigate-final-test-budget-7631c3a1b1/task.md`
<!-- For a provider assignment, add exactly one **External assignment:** <opaque
stable-artifact, role, actor-kind, and principal binding emitted by its adapter>.
Omit it otherwise. -->
<!-- For an active provider source, add exactly one **External source:** <opaque
versioned identity emitted by its adapter>, even when provider prose links here. -->
**Resolution evidence:** `tasks/1_in-progress/2026-07-27-investigate-final-test-budget-7631c3a1b1/task.md`
<!-- Add **Request kind:** task-pickup only for the canonical pickup request of one
unclaimed backlog task. Other request kinds may define their own explicit value. -->
<!-- A changes-requested review successor also adds **Supersedes:** `<old review path>`
and **Follow-up review:** `<new human review path>`. The follow-up is a distinct
awaiting-artifact judgment with **Depends on:** `<this request path>`; do not repeat
this request's repair Action as the review Action. -->

**Request kind:** task-pickup
**If unanswered:** The investigation remains unclaimed in backlog; the gate result and its functional exit status are unchanged.

## What you need to know

The `final` gate exceeded the target stored in `testing.final.target_seconds`. The linked task owns the timing evidence and updates.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its `Queue actions` link have been removed in the claim commit.
