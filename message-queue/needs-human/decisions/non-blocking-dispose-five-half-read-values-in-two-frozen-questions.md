# Two of your open questions contain five sentences the checks read only half of — what should happen to them?

**Action:** Choose whether the five half-read sentences are left alone, repaired by teaching the reader to follow a wrapped line, or rewritten with your sign-off.
**Why this matters:** Anything that later quotes one of those sentences to you — a summary, a notification — would show a sentence that stops mid-thought, and nobody would notice.
**If you do nothing:** Nothing stops. The two questions stay answerable as they are, and a warning about them prints on every run until you answer them.

## What you need to know

**Today:** every labelled value here is read one physical line at a time. Two of your open questions wrap five example sentences onto a second line, so a reader sees the whole sentence and every check sees only its first half. Nothing looks wrong on screen.

**What this would change:** either how values are read everywhere, or those five lines in two files — not the questions, and not your ability to answer them.

**What this does not decide:** the separate question about the ten older files and their bookkeeping. This one is about five sentences being half-read, not about layout.

Both files are frozen: the rule against rewriting a live question refuses an edit to either. Here is one of the five, exactly as it stands.

```
WHAT YOU SEE (the rendered paragraph, complete)
  An agent that skips a handover reads the principle, sees that
  nothing will queue a repair for it, and knows the next session will only see
  the failure if someone runs --check — which is exactly what happens today.

WHAT EVERY CHECK READS
  "An agent that skips a handover reads the principle, sees that"
```

This branch already makes the loss visible: each of the five prints as a non-blocking warning naming its file and line, rather than passing in silence. That is the smallest honest thing to do about a file nothing may repair. The rule that every value is one physical line, however long, is written where new questions are copied from: [the schema every template obeys](../../../templates/README.md).

## Your choices

The choices differ in whether the record changes, the reader changes, or neither does.

### Option A — Leave the five alone
The two files stay as written, the warning keeps printing, and both disappear when you answer them. Costs: five warnings on every run while those questions stay open, and the next long hand-written value repeats the bug.
*Example consequence:* you answer both questions in October, the files are deleted, and the warnings vanish with them — having cost nothing but noise.

### Option B — Teach the reader to follow a wrapped line
Values that continue onto a second line are read whole, everywhere. Costs: this changes what several hundred existing lines parse to, in tasks and designs as well as questions, and checks quietly passing on a half-value start seeing the rest.
*Example consequence:* the class is closed for good — and some check starts reporting a file that has looked clean for a month, for a reason nobody will connect to this.

### Option C — Rewrite just those five lines, with your sign-off
You are shown the five lines and approve unwrapping them; an agent edits two frozen files on that authority alone. Costs: a hole in the rule that stops an agent altering a question you were shown, for five sentences you can already read.
*Example consequence:* the two files parse cleanly next week, and the exception you granted is quoted the next time an agent wants to tidy something you were shown.

## What I recommend

**Recommendation:** Option A — the sentences are complete for you, no live check reads the missing halves, and both files disappear when you answer them, so the cheapest repair is the one already shipped: say so out loud and leave them.
**Strongest case against this:** A fixes nothing and only manages the symptom; the same bug will be written again by the next author with a long sentence, and B is the only choice that closes the class rather than waiting out two instances of it.
**Confidence:** high — I located all five, ran the repository's own reader over them, and confirmed both files are refused a rewrite today; I did not measure what Option B would change across the several hundred other wrapped lines, the number that makes it expensive.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** ______

## For the record

<details>
<summary>For the record — bookkeeping the reconciler reads. Nothing here needs you.</summary>

**Status:** waiting  
**Filed:** 2026-08-18, by claude, from task `2026-08-18-fold-the-queue-machine-record`  
**Full context:** `templates/README.md`  
**Resolution evidence:** `memory/decisions/2026-08-18-wrapped-value-truncation-disposition.md`  
**Answer by:** 2026-11-16

</details>
