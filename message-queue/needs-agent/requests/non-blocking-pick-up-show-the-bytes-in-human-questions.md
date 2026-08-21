# Pick up making a human question answerable from its own bytes

**Status:** open
**Filed:** 2026-08-21, by claude, from chat — the owner rejected four live review items as unanswerable
**Action:** Claim `tasks/0_backlog/2026-08-21-show-the-bytes-in-human-questions`, move it to `1_in-progress`, and resolve this request in the claim commit.
**Full context:** `tasks/0_backlog/2026-08-21-show-the-bytes-in-human-questions/task.md`
**Resolution evidence:** `tasks/1_in-progress/2026-08-21-show-the-bytes-in-human-questions/worklog.md`
**Request kind:** task-pickup
**If unanswered:** The four rejected review items stay unanswerable and the checker keeps skipping the ten items that provoked the complaint; nothing stops.

## What you need to know

Four live `needs-human/reviews/` items were read by the owner and could not be answered.
Measured, they are 241-297 words against an 800-word budget, carry no anchor-precise
pointer, and ask for a verdict on a 710-line design without reproducing one line of it.
The rules that would have caught this already exist in `skills/explain-to-human/`; the
check that enforces them skips every item not written under the current template, which
is exactly the ten items the owner rejected.

## Done when

The task folder sits in `tasks/1_in-progress/`, its `task.md` names a claimant, and this
file is deleted in the same commit.
