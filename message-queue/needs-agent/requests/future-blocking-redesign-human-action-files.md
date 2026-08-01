# Redesign every file that asks a human for attention

**Status:** open
**Filed:** 2026-07-31, by claude, from the owner's changes-requested review of task `2026-07-23-first-class-message-queue`
**Action:** Research human–AI interaction, then design, implement, and verify an action-first format in which every human-attention file states the requested action first, separates historical from current from proposed behavior, presents each choice with its rationale and consequence, carries an evidence-backed agent recommendation, and keeps machine bookkeeping out of the reader's way.
**Full context:** `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`; `message-queue/AGENTS.md`; `handbook/principles/files-as-messages.md`
**Resolution evidence:** `templates/queue/review.md`; `handbook/human-action-guide.md`
**Supersedes:** `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md`
**Follow-up review:** `message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md`
**Blocks at:** transition:merge task:2026-07-23-first-class-message-queue
**Until then:** Implementation, tests, and independent review may continue.

## What you need to know

The owner reviewed the first-class message-queue contract and answered
`changes-requested` on 2026-07-23's exact merged range. The contract itself was accepted;
the presentation was not. In the owner's words, the files "read like a database record":
machine status, paths, hashes, and dependency tokens appear before the question, past and
current and proposed behavior are not distinguished, and a list may be choices or
background or review criteria without saying which.

That verdict was committed on 2026-07-26 but only onto a branch that was never pushed, so
this repair has never been visible from `main`. Meanwhile `templates/queue/*.md` continued
to be refined in the rejected flat-field shape.

An earlier implementation exists on the task/2026-07-23-first-class-message-queue branch and is
useful as design input, not as a merge candidate: its 1,849-line rewrite of
`automation/markdown_semantics.py` was blocked by its own adversarial parser lens across
three review rounds and has never been tested against the current reconciler.

## Done when

`templates/queue/review.md`, its sibling templates, and `handbook/human-action-guide.md`
describe and enforce one action-first format; every live unanswered human-attention file
is migrated to it without altering any committed human response; the reconciler validates
the format; and the follow-up review is bound to the exact repaired revision.
