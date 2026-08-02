# Three changes shipped before the reviews they required were answered — what should happen to those requests now?

**Action:** Choose option A, B, or C for all three stranded merge reviews, or state another disposition.
**Why this matters:** Three core changes are live today without the review each of them declared mandatory before shipping, and nothing anyone does now can satisfy that requirement.
**If you do nothing:** The three requests stay open and answerable, their tasks finish without them, and the fact that the gate was crossed stays visible in the project's history.

## What you need to know

**Today:** all three changes are merged and running. Each filed a request saying it must not ship until you reviewed it; all three are still open and unanswered, and all three of their tasks are parked in review.

**What this would change:** nothing about the code. This picks how the three unanswerable requests close out, and whether their tasks can move on.

**What this does not decide:** whether any of the three changes is good, and whether future work may ship past its own unanswered review. Both stay as they are.

Permission to ship is only meaningful before something ships, so no approval written now can take effect. That is why an agent should not pick for you: the real choice is between recording a judgment you never gave, dropping the request for it, and asking a question that can still be answered. The rules behind this are in [the guide to asking a human for something](../../../handbook/human-action-guide.md).

## Your choices

The choices differ on whether the judgment you were asked for is still collected, and whether the three parked tasks can ever finish.

### Option A — Answer them exactly as written
Write a real verdict into each of the three. The cost is that it changes nothing mechanically: the requests stay open and the tasks stay parked, because permission to ship needs a shipping moment and there is none left. A negative verdict would also mean unwinding live code.
*Example consequence:* your judgment is recorded and permanent, you spend the effort of three reviews, and a month later the same three tasks are still sitting in review.

### Option B — Record that the gate was crossed, then retire all three
A short permanent note states that these three shipped without the review they required and that the shipped code stands; the requests are then deleted against that note. The cost is that the judgment you were asked for is never given.
*Example consequence:* the queue stops carrying questions nobody can act on and the three tasks finish, but if one of those designs is wrong, it is found later by accident rather than by your review.

### Option C — Ask the question that is still answerable
Each request is withdrawn and replaced by one asking about the code as it exists now: does this stay, get revised, or get reverted? The cost is three fresh reviews of large changes, and the original question — may this ship — is retired unanswered.
*Example consequence:* you still get to judge all three, and answering "revise" actually causes something, because the code is live and can be changed.

## What I recommend

**Recommendation:** Option C — it is the only choice that neither invents an answer you never gave nor throws away the request for one, and the only one that leaves the three tasks with an ending they can reach.
**Strongest case against this:** three fresh reviews of large, already-working code is real effort, and Option B buys the same tidy queue for none of it. If you would have approved all three anyway, C is the expensive route.
**Confidence:** low — I am reading the file a previous session wrote rather than the three changes themselves; I confirmed all three tasks are still parked in review, but not how much a fresh review would catch.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-07-31, by claude, from task `2026-07-30-clear-the-stuck-queue-items`
**Full context:** `handbook/human-action-guide.md`; `memory/decisions/2026-07-23-live-queue-obligations-only-weaken-with-evidence.md`; `memory/decisions/2026-07-23-queue-resolution-preserves-review-intent.md`
**Resolution evidence:** `memory/decisions/2026-07-31-merge-boundaries-crossed-unreviewed-disposition.md`
**Answer by:** 2026-10-29
