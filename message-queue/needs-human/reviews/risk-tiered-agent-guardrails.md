# Review the risk-tiered agent guardrails proposal

**Status:** folding
**Filed:** 2026-07-22, by codex, from task 2026-07-22-design-critical-agent-guardrails — `docs/designs/risk-tiered-agent-guardrails.md`
**Look-at:** `docs/designs/risk-tiered-agent-guardrails.md` and the new routing contracts in `docs/AGENTS.md` and `docs/designs/AGENTS.md`
**Why-you-might-care:** this proposes the future security boundary for PII, secrets, agent acknowledgements, authenticated exceptions, and provider-specific admission controls
**If-you-do-nothing:** the document remains a researched proposal and no new enforcement behavior is implemented

**Resolution:** reviewed, but we don't need sandbox for now, other things should provide template, but be careful we don't enforce it all the time. We should have a universal config to turn each hard guard on / soft on / off / manual trigger, especially the one that wasting a lot of tokens (i.e. Agent review)
