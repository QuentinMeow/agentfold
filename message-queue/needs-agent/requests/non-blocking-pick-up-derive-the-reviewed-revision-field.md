# Pick up deriving the Reviewed revision field

**Status:** open
**Filed:** 2026-08-01, by claude, from the human-action format redesign — `handbook/human-action-guide.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-derive-the-reviewed-revision-field/task.md`
**Request kind:** task-pickup
**If unanswered:** The field stays where it is, below the answer line, maintained by agents and asked of nobody; the redesign already removed every instruction telling a human to copy it.

## What you need to know

`Reviewed revision` is forced equal to `Review revision` whenever a response exists, so
it carries no information of its own. The staleness guarantee rests on `Review revision`
being frozen at the first response plus a re-hash at the deletion edge, not on this field.

Deleting it is not a small edit: it opens `human_response_fields`, `claim_identity`,
`immutable_action_text`, and three branches of the review-binding lifecycle, which is the
write-once response boundary. That is why it was kept out of the presentation redesign
and given its own task and its own review.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
