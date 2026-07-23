# Is opt-in activation the intended meaning of template-first guardrails?

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** Confirm opt-in activation, or say which guardrails AgentFold should enable automatically.
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:e2314db67388c8aaf7980b6b66c945605db0822c2f52502c0a38c401d5458392
**Reviewed revision:** ______
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.
**Look-at:** `docs/designs/risk-tiered-agent-guardrails.md`, “Recommended architecture”
**Why-you-might-care:** The choice sets how much security friction an adopted repository receives before explicitly choosing it.
**If-you-do-nothing:** Guardrail implementation waits at its start boundary; the current opt-in interpretation stands only as a proposal.

## What you need to know

“Template-first” currently means AgentFold ships discoverable, replaceable mechanisms
and one configuration surface, but adopting AgentFold silently activates none of them.
Each repository explicitly chooses a mode for each guard.

## Differences

- **Opt-in templates:** preserve future-agent freedom and avoid surprise token cost or
  false positives, but adopters receive no new assurance until they configure guards.
- **Starter guards on by default:** provide stronger initial protection, but impose a
  workflow and operating cost before the adopter evaluates the trade-off.

## Example

Under opt-in adoption, independent-agent review is present in the starter template as
`manual` and runs only when requested. Under starter-on adoption, it might run on every
PR, spending tokens and adding latency even for a typo.

When answering here, copy `Review revision` into `Reviewed revision` so the answer
stays bound to the exact design bytes.

**Your review:** ______
