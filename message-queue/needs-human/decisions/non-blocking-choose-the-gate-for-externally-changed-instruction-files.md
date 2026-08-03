# When an outsider edits a file that tells agents how to behave, what should wait for you?

**Action:** Choose which of three shapes the rule for externally changed instruction files takes: holding the adopting work, holding nothing, or holding the merge itself.
**Why this matters:** Anyone who can open a pull request here can edit the files that direct every agent, and the rule meant to catch that promises a hold this repository can no longer apply.
**If you do nothing:** Nothing stops. The rule keeps promising a hold no file can express, so an outside edit to an instruction file is reviewed only if the agent that happens to see it decides to ask.

## What you need to know

**Today:** nothing is implemented, and no check looks at who authored a change. The constitution says an outside edit to an instruction file is reviewed "before an agent treats them as instructions or they merge". Since 2026-08-01 no queue file can hold a merge: two that did deadlocked, because the merge happened before the answer and the question could then be neither resolved nor withdrawn. A question waiting on you may now hold only the start of work nobody has begun, or one act with no undo.

**What this would change:** which of the three shapes below the constitution asks for, so the rule names something an agent can file.

**What this does not decide:** whether anything mechanical enforces it. No check exists under any of these answers, and you already decided on 2026-08-02 that checks stay advisory.

## Your choices

The choices differ in what is actually held while your answer is outstanding.

### Option A — Hold the work, not the file
The review attaches to a task nobody has started. The edit merges; no work that would treat it as instructions may begin until you answer. Cost: it guards the deliberate path only.
*Example consequence:* an outside contributor rewrites the contract for the message queue. The edit lands the same day, but the task to adopt it sits unstarted until you have read it, so no agent builds on the new wording.

### Option B — Hold nothing, and rely on the standing trust rule
The "or they merge" half is dropped. The review is filed with no hold, and the rule that outside text is data rather than orders is the whole protection. Cost: nothing distinguishes a reviewed instruction file from an unreviewed one.
*Example consequence:* the same rewrite lands, your review sits in the queue with a date on it, and an agent that reads the changed file mid-session is kept honest by one sentence that nothing checks.

### Option C — Make it a real hold at GitHub
A required check refuses the merge until you approve. Cost: it contradicts your 2026-08-02 decision that checks stay advisory, and a check that runs on only some pull requests cannot be required without leaving all the others waiting forever.
*Example consequence:* the rewrite cannot land until you approve it, and unrelated pull requests that touch no instruction file stop merging too.

## What I recommend

**Recommendation:** Option A — the only shape that survives the deadlock and still withholds something real; it turns an unanswerable mid-work question into an answerable pre-work one.
**Strongest case against this:** A guards the path where an agent deliberately adopts the change, but the attack the rule was written for is the other one: an agent that reads a poisoned contract mid-session, starts no task, and crosses no gate. If that is the case you care about, A is theatre and B is its honest version.
**Confidence:** medium — I confirmed no legal spelling exists by reading the grammar the check enforces and every live question in your queue; I have not tried to design the check that would make Option A mechanical rather than described.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-08-02, by claude, from task `2026-08-02-reconcile-the-contracts-with-the-code`
**Full context:** `handbook/principles/provenance-over-position.md`
**Resolution evidence:** `memory/decisions/2026-08-02-the-gate-for-externally-changed-instruction-files.md`
**Answer by:** 2026-10-31
