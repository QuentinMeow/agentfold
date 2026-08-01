# Is the redesigned human-attention format clear enough to use?

**Status:** awaiting-artifact
**Filed:** 2026-07-31, by claude, from the owner's changes-requested review of task `2026-07-23-first-class-message-queue`
**Action:** After the repair is published as one exact revision, judge whether every human-attention file is understandable and answerable on its own, and approve it, name the remaining ambiguity, or reject the format.
**Full context:** `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`; `message-queue/AGENTS.md`; `handbook/principles/files-as-messages.md`
**Resolution evidence:** `roadmap/current-state.md`
**Supersedes:** `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md`
**Depends on:** `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`
**Review target:** pending
**Review revision:** pending
**Reviewed revision:** ______
**Review outcome:** pending
**Blocks at:** transition:merge task:2026-07-23-first-class-message-queue
**Until then:** Implementation, tests, and independent review may continue.
**Why-you-might-care:** This format controls whether you can understand and safely answer every durable request an agent ever makes of you.
**If-you-do-nothing:** The repair may be designed, implemented, and tested, but the redesigned format does not become the standard and the task does not merge.

## What you need to know

You already judged the first-class message-queue contract. You accepted what it does and
rejected how it reads. This item holds the second half of that answer: the promise that
the repaired format comes back to you before it becomes the repository standard.

There is nothing to answer yet. The repair does not exist, so this file is deliberately
`awaiting-artifact` — it exists so the review boundary you asked for cannot be quietly
dropped while the work happens.

## Differences

- **Approve:** the repaired format becomes the standard for every human-attention file.
- **Request specific changes:** name what is still unclear; an agent repairs it and
  publishes another exact revision for review.
- **Reject:** the format is withdrawn and the redesign restarts from a different premise.

## Example

A decision about detector failures should open with what it needs from you, say plainly
that no behavior is implemented today, show each option with its benefit and its risk,
recommend one and say why, and let you answer without copying a checksum.

Do not answer this item until its status becomes `waiting` and an exact review target is
present.

**Your review:** ______
