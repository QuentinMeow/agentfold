# Pick up separating template blanks from human answers

**Status:** open
**Filed:** 2026-08-01, by claude, from the human-action format redesign — `automation/reconcile/reconcile.py`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-stop-reading-none-as-an-unanswered-field/task.md`
**Request kind:** task-pickup
**If unanswered:** The checker keeps reading "none", "n/a", "tbd", "todo" and "unknown" as unanswered wherever it asks whether a human replied; no live item currently carries such an answer, so nothing stops.

## What you need to know

`has_concrete_value` rejects "none", "n/a", "na", "tbd", "todo", "unknown" and any
angle-bracketed text as placeholders. That is correct for a template slot and wrong for a
reply: "none" is the natural answer to a review asking the reader to name a missing
obligation. Everything that protects a committed response keys on
`first_concrete_response`, so such an answer would leave its item looking unanswered and
still mutable.

The rule to land: anything keyed on whether a human responded keys on the field being
non-blank and not the literal `______` blank, and nothing more.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
