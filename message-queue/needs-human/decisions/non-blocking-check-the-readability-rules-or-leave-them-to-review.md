# Should the repository start refusing messages that break the readability rules?

**Action:** Choose whether readability rules stay judgment, become advisory warnings, or become commit-blocking checks.
**Why this matters:** Nothing currently stops an agent from ignoring the whole standard, so the quality you get still depends on which agent wrote the message.
**If you do nothing:** The rules stay written-only and enforced by review; agents that follow them produce better messages and agents that do not are caught only when you notice.

## What you need to know

**Today:** the readability standard is prose in a skill. Two things near it are already checked — a pull-request body must carry a list of your open items with a real link each, and a queue item must stay under 700 words before its answer line. Everything else is unenforced.

**What this would change:** which of the remaining rules, if any, a program starts checking, and whether failing one stops a commit or only prints a warning.

**What this does not decide:** the rules themselves. That is a separate question about whether the standard is right, not about whether it is enforced.

Some rules have a shape a program can see: are the pull-request sections present and in order, does every choice end with an example consequence, does the summary have three to six items. Others do not: whether an explanation is clear, whether the counter-argument is real or hedged. The risk in checking the visible ones is that an agent learns to satisfy the check — a body can have all seven sections and still tell you nothing.

The full reasoning is in [the design for explaining work to the owner](../../../docs/designs/explaining-work-to-the-owner.md), and the standard itself is [the explanation skill](../../../skills/explain-to-human/SKILL.md).

## Your choices

The choices differ in what happens when a message breaks a rule: nothing, a warning, or a refused commit.

### Option A — Leave it to review
No new checks. A bad message is caught when a person reads it.
*Example consequence:* an agent in a hurry writes a pull-request body with no summary and only the required list of your items. It merges; you notice when you open it and have no idea what changed, and the repair is a comment rather than a rejected commit.

### Option B — Advisory checks on the structural rules
The reconciler reports missing sections, missing example consequences, and out-of-range summary lengths as advisory findings. Advisory findings print and are counted; they never fail a commit.
*Example consequence:* the same agent commits successfully and sees `explanation-shape: pull-request body has no TL;DR section (advisory)`. Most agents fix it; one ignores it and nothing stops them, so you still see the occasional bad body.

### Option C — Blocking checks on the structural rules
The same checks, but a violation fails the commit like any other invariant.
*Example consequence:* an agent cannot commit a queue item whose options have no example consequences — and also cannot commit one where the example consequence is the single word "none", because the check can see the line exists and not whether it says anything. Expect some correct-but-unusual messages to be refused, and expect agents to satisfy the shape rather than the intent.

## What I recommend

**Recommendation:** Option B — the structural rules are worth surfacing, and advisory findings put the rule in front of the agent that broke it without teaching anyone to write for the checker.
**Strongest case against this:** advisory findings in this repository are already ignorable by construction, so B may buy nothing over A while costing a checker to build and maintain. If you believe agents ignore warnings, A and C are the only real choices.
**Confidence:** medium — I know which rules have a structural shape, because I wrote them, but I have not measured how often agents actually violate them, so the size of the problem is unmeasured.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** I want option B.

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** folding
**Filed:** 2026-08-02, by claude, from task `2026-08-01-report-work-back-to-the-owner`
**Full context:** `docs/designs/explaining-work-to-the-owner.md`
**Resolution evidence:** `memory/decisions/2026-08-02-readability-enforcement-disposition.md`
**Answer by:** 2026-10-31
