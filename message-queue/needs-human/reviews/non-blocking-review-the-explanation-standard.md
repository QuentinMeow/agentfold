# Is this the standard you want every message an agent writes you to meet?

**Action:** Say whether this is the standard every human-facing message is held to, or name what to change.
**Why this matters:** Every report, pull request, and question you get from an agent from now on is written to this standard, so a wrong rule here compounds across every future message.
**If you do nothing:** The standard stands as written and agents follow it; nothing stops, and it can be changed later by editing one file.

## What you need to know

**Today:** each surface an agent writes for you — decision file, handover, pull-request body, chat reply — has partial rules in a different document, and none of them says how to explain something to a reader with no context. Message quality is whatever the writing agent happened to do.

**What this would change:** one skill states the craft once and routes to four short files, one per surface. Its core rule is that everything is written in three layers: one sentence saying whether you need to act, one paragraph saying what behaved how before and how it behaves now, then the depth, folded or linked.

**What this does not decide:** when an agent asks you anything at all. That is the collaboration mode, and it is unchanged — nothing here makes an agent ask more or less often.

Its other rules: say what goes in and comes out whenever a function or file is named; gloss an unusual word in parentheses at first use; give one worked example for anything counterintuitive and never two; write "~70%, medium confidence, because X" instead of "might"; and inline anything whose being different would change your answer, leaving only the evidence behind a link.

You are judging whether these are the right rules, not whether the prose is polished. The skill is [the explanation skill](../../../skills/explain-to-human/SKILL.md); its reasoning and rejected alternatives are linked from there.

## Your choices

The choices differ in whether the standard as written becomes the one agents are held to, or goes back for a named change first.

### Approve
The skill stands as the standard. Every later message, pull request, and handover is written to it, and later work builds on the routing table rather than reopening it.
*Example consequence:* the next session's chat reply opens with whether anything is blocked, lists what was decided without you and what each would cost to undo, and ends with your open items ranked — and if it does not, that is a defect you can point at a rule for.

### Request changes
The standard is close but one or more rules are wrong. Name the rule and what it should say; an agent repairs it and brings back the changed file.
*Example consequence:* if you think the three-layer rule buries detail you actually want first, saying so changes the shape of every future message rather than one of them.

### Reject
The whole approach is wrong — for example, you would rather have terse mechanical reports than explained ones.
*Example consequence:* the skill is removed and agents go back to per-surface rules; messages get shorter and you go back to asking what things are.

## What I recommend

**Recommendation:** Approve — the rules come from fields that solved this under real pressure, and every one of them is stated as an action rather than an adjective, so an agent can tell whether it followed it.
**Strongest case against this:** none of it is machine-checked, so an agent that ignores the skill produces exactly what you get today and nothing catches it. Whether written rules alone change behaviour is genuinely untested here.
**Confidence:** medium — I verified the rules against the repository's existing contracts and had an independent agent use the skill blind on a real change, but nothing proves the rules survive contact with an agent that is in a hurry.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your review:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-08-01, by claude, from task `2026-08-01-write-the-explanation-skill`
**Full context:** `docs/designs/explaining-work-to-the-owner.md`
**Resolution evidence:** `memory/decisions/2026-08-02-the-explanation-standard-disposition.md`
**Review target:** `skills/explain-to-human/SKILL.md`
**Review revision:** sha256:45058a9c0196dfb3f76bdaa3ba7d3b259258b2cf36511576a2c541f91239a80b
**Reviewed revision:** ______
**Review outcome:** pending
**Answer by:** 2026-10-30
