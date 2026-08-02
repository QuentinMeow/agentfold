# Does this write-up make it clear enough that adopting the harness switches none of its safety mechanisms on?

**Action:** Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.
**Why this matters:** Anyone who reads this and comes away thinking protection is on by default will believe they are covered when they are not.
**If you do nothing:** Nothing stops; mechanisms keep shipping as optional templates under the policy already decided, and the current wording stays.

## What you need to know

**Today:** the policy is already settled and recorded. The harness ships each safety mechanism as a discoverable, replaceable starting point, plus one place to configure them — and adopting the harness turns none of them on. Every repository picks, per mechanism, whether it is off, manual, advisory, or enforced. The design document now carries a longer explanation of that, which is what you are being asked about.

**What this would change:** only the wording. Approving keeps the explanation as it stands; asking for changes gets the confusing part rewritten.

**What this does not decide:** the policy itself. Nothing you say here can switch mechanisms on by default or change what ships — that would take a separate, explicit decision and its own permanent record.

The distinction the wording has to carry is that something being available is not the same as it being active, and that leaving a mechanism off or set to manual genuinely lowers how protected the repository is rather than being a neutral preference. A worked example: independent agent review ships in the starter set as *manual*, and runs only when somebody asks for it. If the document instead said it ran automatically on every proposed change, that sentence would contradict the recorded decision — and the fix would be to correct the sentence, not to start running it. The document is [the guardrail design](../../../docs/designs/risk-tiered-agent-guardrails.md), in its sections on how a human review is dispositioned and on the vocabulary it uses.

## Your choices

The choices differ only in whether the explanation is left alone or sent back for a named wording fix; refusing the underlying policy is not on offer here, because reversing it needs its own decision.

### Approve
The explanation stands as written and nobody revisits it. The cost is that if a sentence is subtly misleading, that misreading is now the documented one, and it is what an adopter will act on.
*Example consequence:* someone adopts the harness, reads this, correctly leaves everything off while they get set up, and knows their repository is currently unprotected rather than assuming otherwise.

### Request changes
Point at the sentence that reads wrong or the example that is missing. An agent rewrites that part and brings it back. The cost is a round trip, and the recorded policy governs unchanged meanwhile.
*Example consequence:* you say the four settings are never actually listed together in one place, that gets fixed, and the next reader can see all four without hunting.

## What I recommend

**Recommendation:** Approve — the explanation makes the two things that get confused, availability and activation, into separate statements, and it says out loud that off and manual are weaker rather than neutral.
**Strongest case against this:** the honest test is whether a first-time adopter is misled, and I am not one. Someone skimming for "is this safe by default?" may take the presence of a full mechanism list as an answer, whatever the surrounding sentences say.
**Confidence:** low — I am reading the file a previous session wrote rather than the design text itself; I confirmed the recorded decision exists, but I did not re-read the expanded explanation or test it on anyone unfamiliar.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your review:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Full context:** `memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md`; `docs/designs/risk-tiered-agent-guardrails.md`
**Resolution evidence:** `memory/decisions/2026-07-23-template-first-review-disposition.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f
**Reviewed revision:** ______
**Review outcome:** pending
**Answer by:** 2026-10-21
