# Is the redesigned human-attention format clear enough to use?

**Status:** awaiting-artifact
**Filed:** 2026-07-26, by codex, from the owner's changes-requested review of task `2026-07-23-first-class-message-queue`
**Action:** After the repair is published, review whether every human-attention file states the task first, separates current from proposed behavior, explains choices and consequences, gives a justified recommendation, and keeps references and machine records out of the way.
**Full context:** `handbook/human-action-guide.md`
**Resolution evidence:** `roadmap/current-state.md`
**Why-you-might-care:** This format controls whether a person can understand and safely answer every durable request from an agent.
**If-you-do-nothing:** The repair may be designed, implemented, and tested, but the first-class message-queue task does not merge or complete.
**Review target:** pending
**Review revision:** pending
**Reviewed revision:** ______
**Review outcome:** pending
**Supersedes:** `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md`
**Depends on:** `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`
**Blocks at:** transition:merge task:2026-07-23-first-class-message-queue
**Until then:** Research, implementation, migration, and verification may continue; this item is not ready for human action.

## What you need to know

The existing format reads like a database record: internal status, paths, hashes, and
dependency tokens appear before the question. It often fails to say whether behavior
is historical, current, or merely proposed, and it makes the human infer whether a
list contains choices, background, or review criteria.

The replacement will be reviewed only after it exists as one exact revision. Until
then, this file records a planned review and asks the human to do nothing.

## Differences

- **Approve:** accept the repaired action-first format and its migration as clear
  enough to become the repository standard.
- **Request specific changes:** name the remaining ambiguity; an agent repairs it and
  publishes another exact revision for review.
- **Reject:** withdraw this format and keep the task open for a different design.

## Example

A decision about detector failures should say that no behavior is implemented today,
show each future option with benefits and risks, recommend one after the comparison,
and let the person answer without copying a checksum.

Do not answer this item until its status becomes `waiting` and an exact review target
is present.

**Your review:** ______
