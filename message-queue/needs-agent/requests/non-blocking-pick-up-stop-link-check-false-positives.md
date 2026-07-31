# Pick up stopping link-check false positives

**Status:** open
**Filed:** 2026-07-30, by claude, from task `2026-07-30-stop-link-check-false-positives`
**Action:** Claim the task to fix the five reproduced link-check defects and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-stop-link-check-false-positives/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; `check_links` keeps reporting ordinary prose as broken paths and no current work is blocked by leaving it unclaimed.

## What you need to know

An audit reproduced five confirmed defects in `check_links` (link-check): prose false
positives, an indented-code false positive, two fail-open false negatives from an
unanchored skip-prefix check, an anchor-slug false positive on a linked heading, and a
false positive whenever a cited queue action is resolved (deleted). The task file has
the full list and acceptance criteria.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
