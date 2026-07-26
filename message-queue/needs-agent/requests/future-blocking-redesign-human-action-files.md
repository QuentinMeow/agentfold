# Redesign every file that asks for human attention

**Status:** in-repair
**Filed:** 2026-07-26, by codex, from the owner's changes-requested review of task `2026-07-23-first-class-message-queue`
**Action:** Research, design, implement, and verify an action-first format that makes every human-attention file self-contained, distinguishes current from proposed behavior, presents clear choices with rationale and consequences, and gives an evidence-backed agent recommendation.
**Full context:** `handbook/human-action-guide.md`
**Resolution evidence:** `templates/queue/review.md`; `automation/reconcile/reconcile.py`
**Supersedes:** `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md`
**Follow-up review:** `message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md`
**Blocks at:** transition:merge task:2026-07-23-first-class-message-queue
**Until then:** Research, implementation, migration, and verification may continue; the task does not merge or complete.

## What you need to know

The current queue format puts machine bookkeeping before the human's task and uses
labels such as `Why-you-might-care`. Several live reviews mix past, current, proposed,
and already-answered states, repeat the same source link, and describe alternatives
without saying what the person is choosing.

The repair must cover templates, guidance, validation, handover projections, and every
unanswered live human-review file. It must preserve the exact response and immutable
revision binding in the already answered detector-failure review.

## Done when

Independent research and design agents agree on the interaction model, the templates
and checks enforce it, live unanswered reviews are migrated safely, only actionable
items are surfaced to the human, focused and complete verification pass, and the
follow-up review is bound to the exact repaired revision.
