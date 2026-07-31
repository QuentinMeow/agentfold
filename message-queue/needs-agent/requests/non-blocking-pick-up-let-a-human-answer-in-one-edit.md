# Pick up the one-edit human answer task

**Status:** open
**Filed:** 2026-07-31, by claude, from chat
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-31-let-a-human-answer-in-one-edit/task.md`
**Request kind:** task-pickup
**If unanswered:** Humans keep being unable to commit their own answers, every queue template stays copy-invalid, and no current work is blocked.

## What you need to know

A human who answers a review the way root `AGENTS.md` instructs has their own commit
rejected by two `queue-schema` findings, and by a third from `link-check` if they name a
path. Separately, no file in `templates/queue/` survives being copied and filled in,
because every timing field lives only inside an HTML comment that `semantic_text()`
blanks before `fields()` parses.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
