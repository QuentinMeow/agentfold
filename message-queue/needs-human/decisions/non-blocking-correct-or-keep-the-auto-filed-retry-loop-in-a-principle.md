# Should the eventual-consistency principle stop saying retries are filed automatically?

**Status:** waiting
**Filed:** 2026-07-31, by claude, from task 2026-07-31-collapse-restated-contract-rules
**Action:** choose Option A or Option B, or state another choice
**Full context:** [the eventual-consistency principle](handbook/principles/eventual-consistency.md)
**Why-you-might-care:** A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts.
**If-you-do-nothing:** Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
**Resolution evidence:** `handbook/principles/eventual-consistency.md`

**Answer by:** 2026-10-29
**If unanswered:** The principle text stays exactly as it is; agents keep reading "retry item auto-filed" as a live mechanism, and the repair keeps waiting on the retry-automation task instead.

## What you need to know

`handbook/principles/eventual-consistency.md` describes the repo's self-healing loop:
an agent forgets a step, the reconciler detects it, and — in the diagram on line 12 and
the prose on lines 16-19 — "retry item auto-filed", with the reconciler later garbage
collecting its own item. That filing only happens when `reconcile.py` is run with
`--file-retries`. Nothing runs it: the pre-commit hook and both CI jobs call `--check`
only, the installer never mentions the reconciler, and there is no Makefile. The
`retries/` directory contains only a `README.md`; no retry item has ever been filed.

I fixed the same overstatement in `README.md` and `history/AGENTS.md` directly, because
those are ordinary docs. I did not touch this one: `handbook/AGENTS.md` makes
`principles/` files near-immutable, so changing one needs your approval and a superseding
ADR. That is why this is a question rather than a diff.

## Differences

The choice is between describing the loop as it runs today and describing it as designed.
Option A makes the principle true right now at the cost of making the repo's flagship
self-healing story read as half-built. Option B keeps the story intact and moves the
repair into the already-filed automation task, accepting that until that task ships, an
agent reading the principle will believe a mechanism exists that does not.

## Options

### Option A — Make the tense honest now
Change the diagram and prose to say the reconciler *reports* a finding, and that filing
it as a retry item requires `--file-retries`, which nothing currently runs. Costs a
superseding ADR and a principle edit.
*Example consequence:* An agent that skips a handover reads the principle, sees that
nothing will queue a repair for it, and knows the next session will only see the failure
if someone runs `--check` — which is exactly what happens today.

### Option B — Leave the principle and fix it when the mechanism lands
Keep the text, and let task 2026-07-22-retry-filing-automation-and-waivers
make it true by wiring `--file-retries` into the hook. No principle edit, no ADR.
*Example consequence:* Someone adopting AgentFold next month reads the principle,
expects a `retries/` folder that fills itself, finds it permanently empty, and has to
read the reconciler source to discover why.

## Recommendation

Option A. The principle's own argument is that detection plus a repair loop beats hoping
agents remember — an argument that is weaker, not stronger, when the loop is described as
running and is not.

**Your answer:** ______
