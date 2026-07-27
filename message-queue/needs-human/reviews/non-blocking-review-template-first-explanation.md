# Review needed: Does the design clearly explain the policy that AgentFold offers guard templates without activating them?
<!-- human-action-presentation: v2 -->

> **Waiting for your response.**

## What I need from you

**Action:** Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.

Judge the explanation only; reversing the already recorded policy would require a new
decision rather than a review response here.

## Why this matters

This review checks whether readers can distinguish a guard being available in a template from that guard being enabled and producing evidence.

## If you do not respond

If you do not respond, the existing decision remains authoritative, the expanded explanation stays in place, and implementation may proceed under the decided four-mode policy.

## What changed

**Before this change:** The recorded policy existed, but its short explanation did not clearly separate an available template from an active guard and observed evidence.

**Current state:** The template-first policy remains authoritative, the expanded explanation is present on `main`, and this clarity review is unanswered.

**Change under review:** The design expands its explanation of how each repository chooses a mode for each guard and how disabled or manual controls affect reported assurance.

**Not included:** This review does not activate a guard, change the four-mode policy, or prove that any optional review ran.

**Additional context:** For example, independent-agent review is available in the
  starter template as `manual` and runs only when requested. Availability alone is not
  activation or evidence.

## Review outcomes

### Approve

**What it means:** Accept that the exact design revision explains the existing template-first policy clearly enough.

**Consequence:** The wording stays and implementation may continue under the already decided policy.

**Example:** A reader correctly understands that installing AgentFold does not automatically run independent-agent review on every pull request.

### Request changes

**What it means:** Identify a confusing sentence, missing distinction, or example that should be repaired without changing the underlying policy.

**Consequence:** The decision remains authoritative while an agent revises the explanation for another review.

**Example:** Request a wording change if the design implies that a `manual` guard ran merely because its template exists.

### Reject

**What it means:** Decline the current explanation as an inaccurate account of the recorded policy.

**Consequence:** The explanation must be withdrawn or replaced, but the policy itself remains in force unless a separate decision supersedes it.

**Example:** Reject if the revision says adoption automatically enables all four guard modes.

## Agent recommendation

**Evidence checked:** I compared the recorded template-first decision with the exact design's mode table, adoption text, and derived-assurance rules; all distinguish availability from activation and evidence.

**Assumptions:** The existing template-first decision remains authoritative and this review is limited to explanatory clarity.

**Confidence:** High, because the relevant passages of the exact target use the distinction consistently.

**Rationale:** The explanation distinguishes availability, explicit activation, mode selection, and observed evidence while keeping the prior decision authoritative.

**What could change this recommendation:** Any sentence that equates a shipped template with an active or completed guard would justify requesting changes.

**Recommendation:** Approve.

## Your response

Write `approve`, `request changes`, or `reject`, followed by any reason or requested
changes. You may also write `I need clarification`. A plain-language answer is enough;
the agent manages revision tracking.

**Your review:** ______

## References

**Full context:** [Template-first guardrail decision](../../../memory/decisions/2026-07-22-guardrails-are-template-first-and-mode-configurable.md); [expanded guardrail explanation](../../../docs/designs/risk-tiered-agent-guardrails.md)

<details>
<summary>Tracking details</summary>

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Resolution evidence:** `memory/decisions/2026-07-23-template-first-review-disposition.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f
**Reviewed revision:** ______
**Review outcome:** pending
**If unanswered:** The 2026-07-22 ADR remains authoritative and the current expanded explanation stays; implementation may proceed.

</details>
