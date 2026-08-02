# Should a core rule stop promising an automatic repair loop that nothing actually runs?

**Action:** choose Option A or Option B, or state another choice
**Why this matters:** One of this repository's most-quoted rules promises an automatic repair loop, and no hook, scheduled job, or script anywhere actually starts it.
**If you do nothing:** Nothing stops; the rule keeps describing the loop in the present tense until you answer or the automation task that would make the sentence true finally ships.

## What you need to know

**Today:** the rule is written in the present tense — a checker spots a broken invariant, and a repair item is "auto-filed" for the next session to pick up. That filing only happens when the checker is run with an extra flag, and nothing runs it with that flag: the commit hook and both continuous-integration jobs run the plain check, and the repair folder has never held anything but its own README.

**What this would change:** the diagram and the two sentences beside it would say the checker *reports* a finding, and that turning a finding into a filed repair needs a flag nothing currently passes.

**What this does not decide:** whether the automatic filing is ever built. A separate task for wiring it up already exists and is untouched either way.

I corrected the same overstatement in two ordinary documents directly, without asking. I stopped at this one because rules of this kind are deliberately near-immutable here: changing one needs your approval and a permanent record of the change, which is why you are seeing a question rather than a finished edit. The rule is [the eventual-consistency principle](../../../handbook/principles/eventual-consistency.md).

## Your choices

The choices differ on whether the text is corrected now or left to become true when the missing automation lands.

### Option A — Make the wording honest now
Say what runs today: findings are reported, and filing one as a repair takes a flag nobody runs. The cost is an edit to a near-immutable rule plus the permanent record that goes with it, and the repository's flagship self-healing story starts reading as half-built.
*Example consequence:* an agent that skips a step reads the rule, sees that nothing will queue a repair on its behalf, and knows the failure surfaces only when someone next runs the checker — which is exactly what happens today.

### Option B — Leave the wording and fix it when the mechanism lands
Keep the text, and let the already-filed automation task make it true by wiring the flag into the commit hook. No edit and no record now; the cost is that until that task ships, anyone reading the rule believes a mechanism exists that does not.
*Example consequence:* someone adopting this harness next month reads the rule, expects a repair folder that fills itself, finds it permanently empty, and has to read the checker's source code to find out why.

## What I recommend

**Recommendation:** Option A — the rule's own argument is that detection plus a repair loop beats hoping agents remember, and that argument is weaker, not stronger, when the loop is described as running and is not.
**Strongest case against this:** the wording becomes true for free once the automation ships, so Option A spends an edit and a permanent record on a sentence a queued task is already scheduled to fix; if that task is picked up soon, this is churn.
**Confidence:** medium — I confirmed that the commit hook and both continuous-integration jobs run the plain check, that nothing passes the filing flag, and that the repair folder holds only a README; I did not check how soon the automation task is likely to be picked up.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-07-31, by claude, from task 2026-07-31-collapse-restated-contract-rules
**Full context:** [the eventual-consistency principle](handbook/principles/eventual-consistency.md)
**Resolution evidence:** `handbook/principles/eventual-consistency.md`
**Answer by:** 2026-10-29
