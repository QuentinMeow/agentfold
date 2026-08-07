# The review check can report a rejected change as an approved one. Repair it, or withdraw it to something smaller?

**Action:** Choose whether the review-receipt work is repaired in place, withdrawn and rebuilt to the smaller shape you authorized, or left exactly as it is.
**Why this matters:** The check that decides whether independent reviewers approved a change can count a panel that rejected it as a panel that approved it.
**If you do nothing:** Nothing stops. The current branch stays unpublished and unmerged, the default branch stays green and unchanged, and three finished repairs stay unreleased.

## What you need to know

**Today:** The work sits on its own branch, never merged; nothing runs it. On 2026-08-04 you authorized a narrow change: receipts would use one closed contiguous
block, and the parser would become, in the recorded decision's words, deliberately smaller
and fail-closed.

**What this would change:** Whether that branch is repaired again, restarted from the
smaller idea, or kept as it stands.

**What this does not decide:** It does not reverse your 2026-08-04 decision, change who may
review, alter merge policy, or touch the two repairs behind it.

Three reviewers examined the branch this morning in separate checkouts, blind to each
other. All three rejected it. The most serious finding: a reviewer's verdict is
discarded without warning when their one-line explanation contains a character outside a
narrow allowed set, and every verdict after it is discarded too. A panel of one approval and
two rejections is therefore reported as one approval and zero rejections, which reads as
approval. The banned characters include the underscore, the number sign, and the backtick,
so a reviewer cannot name a Python file, cite an issue number, or quote code. One reviewer
measured thirteen of fourteen realistic explanations rejected this way; I reproduced it.

This is the sixteenth review round; each has found new holes and widened the parser, now
roughly 495 lines against the twenty it replaced. The
[session handover](../../../history/conversations/2026-08-07-1030PDT-resume-multi-worktree-improvements/handover.md)
records every finding and how to re-run it.

## Your choices

The choices differ on whether the current implementation is worth continuing to repair.

### Option A — Withdraw it and rebuild to the authorized shape

Discard the branch's parser and template changes and restart from the narrow closed block
you approved, with the alphabet restriction, the reviewer-similarity rule, and the second
undocumented receipt grammar left out unless something forces them back. The cost is that
sixteen rounds of work is spent, and the two dependent repairs wait longer.
*Example consequence:* A reviewer writes an explanation naming a Python file, it is counted
normally, and a rejection stays a rejection.

### Option B — Repair the current implementation in place

Keep the branch and fix the three blocking findings on top of it. The cost is that the
sixteen previous rounds are evidence this surface produces a new hole per repair, and the
implementation already exceeds what you authorized.
*Example consequence:* A seventeenth panel runs; if it finds a new hole, the same choice
returns with more code behind it.

### Option C — Leave it as it stands

Change nothing and stop here. The cost is that the two finished repairs behind it stay
unpublished, because they cannot record their own review evidence without it.
*Example consequence:* The stale-base and bootstrap fixes stay on branches, the reason
written down but not repaired.

## What I recommend

**Recommendation:** Option A — the failure direction is toward approval, the restrictions
that cause it were never part of what you authorized, and sixteen rounds of widening is
evidence about the approach rather than about any single bug.
**Strongest case against this:** Option B keeps real work that already passes its full test
suite, and the three findings are individually fixable without discarding anything.
**Confidence:** medium — I reproduced the counting failure directly and confirmed the
character restrictions myself, and I did not design the smaller replacement or estimate
what rebuilding it would cost.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-08-07, by claude opus 5, from task `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`
**Full context:** `history/conversations/2026-08-07-1030PDT-resume-multi-worktree-improvements/handover.md`
**Resolution evidence:** `memory/decisions/2026-08-04-review-receipt-parser-authorization.md`
**Answer by:** 2026-11-05
