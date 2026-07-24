# Does the design explain the decided template-first policy clearly?

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.
**Full context:** `memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md`; `docs/designs/risk-tiered-agent-guardrails.md`
**Resolution evidence:** `memory/decisions/2026-07-23-template-first-review-disposition.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:e2314db67388c8aaf7980b6b66c945605db0822c2f52502c0a38c401d5458392
**Reviewed revision:** ______
**Review outcome:** pending
**If unanswered:** The 2026-07-22 ADR remains authoritative and the current expanded explanation stays; implementation may proceed.
**Look-at:** `docs/designs/risk-tiered-agent-guardrails.md`, “Human review disposition” and “Review vocabulary and concrete differences”
**Why-you-might-care:** This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it.
**If-you-do-nothing:** AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## What you need to know

“Template-first” is already a decided policy, recorded in the linked ADR. AgentFold
ships discoverable, replaceable mechanisms and one configuration surface, but adopting
AgentFold silently activates none of them. Each repository explicitly chooses a mode
for each guard. This review asks only whether the design now explains that distinction
clearly enough.

## Differences

- **Approve the explanation:** keep the existing wording because it makes clear that
  availability is not activation and that disabled/manual controls lower assurance.
- **Request a wording change:** identify the confusing sentence or missing example; the
  ADR still governs while the documentation is revised.
- **Reverse the policy:** this review cannot do that. A reversal requires an explicit
  new decision and a superseding ADR, rather than a comment that conflicts with history.

## Example

Independent-agent review is present in the starter template as `manual` and runs only
when requested. If the design instead said it automatically runs on every PR, that
sentence would conflict with the ADR; request a wording fix here rather than silently
changing implementation policy.

When answering here, copy `Review revision` into `Reviewed revision` so the answer
stays bound to the exact design bytes.

**Your review:** ______
