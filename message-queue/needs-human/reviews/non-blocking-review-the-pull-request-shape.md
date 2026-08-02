# Does a pull request in this shape tell you what you need without scrolling?

**Action:** Say whether this pull-request shape works for you, or name the section to move, add, or drop.
**Why this matters:** This is the shape of every pull request you are asked to look at from now on, and it decides what you see before you have to click anything.
**If you do nothing:** The shape stands and every later pull request uses it; nothing stops, and changing it later means editing two files and one test.

## What you need to know

**Today:** only one section of a pull-request body has a defined shape — the machine-checked list of things that need you. Everything else is invented per pull request, so you have to hunt for what changed and what it means.

**What this would change:** a fixed order. Title, then a numbered summary where each item says what it was before and what it is now, then your own to-do list ranked with the consequence of ignoring each, and only then the depth: the full explanation, the file table, and the verification output, each folded so it costs you nothing unless you want it.

**What this does not decide:** what gets asked of you or when. Nothing here changes which questions reach you or whether they hold anything up.

Three details are judgment calls you may disagree with. Each folded section keeps a visible heading above its fold, so you can see what exists without expanding it — this also happens to be required, because a fold with no heading is misread by the boundary check as part of your to-do list. The file table has one row per *reason*, so several files changed for one reason share a row rather than getting one each. And the summary is capped at six items, which means genuinely large changes push detail into the folded section rather than the summary.

The schema is [the pull-request schema](../../../templates/pull-request.md); a matching skeleton pre-fills every pull request opened in the browser, and ten tests hold the two in agreement.

## Your choices

The choices differ in whether this shape becomes the default now or after a named change.

### Approve
Every later pull request uses this order and these folds.
*Example consequence:* you open a pull request on your phone, read four numbered lines and a ranked list of two things that need you, and close it — or expand one fold and get the whole story without opening the repository.

### Request changes
Name the section that is wrong. Common versions: you want the file table visible rather than folded, you want verification above the fold because you check it every time, or you want the summary uncapped.
*Example consequence:* if you say verification should be visible, every later pull request shows its real test output on the first screen and the body gets roughly ten lines longer.

### Reject
You would rather agents wrote pull-request bodies freely.
*Example consequence:* the schema is deleted and bodies vary by author again; the machine-checked to-do list stays, because a separate check requires it.

## What I recommend

**Recommendation:** Approve — the order puts the two things you always need, what changed and what you owe, above everything optional, and folding the rest is what keeps the body short without deleting anything.
**Strongest case against this:** folded sections are sections most people never open, so anything important that lands in a fold is effectively invisible. If you routinely want the verification output, folding it is the wrong default for you specifically.
**Confidence:** medium — the shape is proven against the boundary check by ten tests, and three real defects were caught that way, but no pull request has yet been read by you in this shape.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your review:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** awaiting-artifact
**Filed:** 2026-08-01, by claude, from task `2026-08-01-standardize-pull-request-bodies`
**Full context:** `skills/explain-to-human/scenarios/pull-request.md`
**Resolution evidence:** `memory/decisions/2026-08-02-the-pull-request-shape-disposition.md`
**Review target:** pending
**Review revision:** pending
**Reviewed revision:** ______
**Review outcome:** pending
**Answer by:** 2026-10-30
