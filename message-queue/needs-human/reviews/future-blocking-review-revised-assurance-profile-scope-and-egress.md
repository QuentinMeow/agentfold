# Review needed: Does the revised assurance design match the direction already approved?
<!-- human-action-presentation: v2 -->

> **Waiting for your response.**

## What I need from you

**Action:** Review whether the revised design clearly separates configured guard settings from the assurance supported by evidence, explains the limits of manual evidence and coverage, and states that controlling where data may be sent is outside this review and design scope; then approve, request changes, or reject.

In plain language, check that settings are separate from evidence, manual review's
limits are explicit, and control over where data may be sent is clearly outside this
work; this review does not silently reopen the underlying decision.

## Why this matters

This keeps reported assurance tied to observed protection instead of allowing an agent to select or claim a reassuring label.

## If you do not respond

If you do not respond, unrelated work may continue but guardrail implementation cannot start and the revised explanation is not accepted.

## What changed

**Before this change:** The design described selectable assurance profiles, which could be mistaken for evidence-backed protection.

**Current state:** The owner has approved individual guard settings and evidence-derived assurance, the revised explanation is present on `main`, this wording review is unanswered, and implementation has not started.

**Change under review:** The revised design explains that guard settings are inputs, assurance is a report derived from observed evidence, manual review has explicit coverage limits, and controlled egress is outside this approved work.

**Not included:** The guard configuration, evidence collection, derived report, and enforcement at the start boundary all remain future work.

**Additional context:** For example, a credential rule may combine manual semantic
  inspection, a hard merge check, and hard remote admission. Turning off manual review
  does not erase an independently verified admission gate, and it does not pretend
  that semantic review ran.

## Review outcomes

### Approve

**What it means:** Accept that the exact revision clearly expresses the already approved derived-assurance model and its scope limits.

**Consequence:** The design review requirement is satisfied for this revision and implementation may start after the remaining boundary conditions are met.

**Example:** A report lists the protection actually observed for credential handling rather than presenting a selectable `high assurance` profile.

### Request changes

**What it means:** Keep the conceptual decision while naming wording, coverage, or scope boundaries that remain unclear.

**Consequence:** An agent revises the explanation and publishes a new exact revision before implementation starts.

**Example:** Ask the design to distinguish more clearly between an unobserved manual review and a failed automated admission check.

### Reject

**What it means:** Decline the revised design because it does not faithfully express the approved direction.

**Consequence:** Implementation remains stopped and reversing the underlying decision requires a separate explicit decision and durable record.

**Example:** Reject if the revision still lets a repository choose an assurance label independently of the guards and evidence actually observed.

## Agent recommendation

**Evidence checked:** I audited the exact target's mode table, derived-assurance section, coverage statements, and controlled-egress scope; none treats a configured mode as evidence or controlled egress as implemented.

**Assumptions:** The owner's recorded guard-binding and controlled-egress decisions remain authoritative; this review judges whether the revision explains them accurately.

**Confidence:** High, because the relevant sections of the exact target consistently preserve those distinctions.

**Rationale:** The revision separates configurable controls from evidence-derived claims and names controlled egress as outside the approved scope.

**What could change this recommendation:** Any passage that treats a configured mode as proof that a guard ran, or implies that controlled egress is implemented, would justify requesting changes.

**Recommendation:** Approve.

## Your response

Write `approve`, `request changes`, or `reject`, followed by any reason or requested
changes. You may also write `I need clarification`. A plain-language answer is enough;
the agent manages revision tracking.

**Your review:** ______

## References

**Full context:** [Revised risk-tiered agent guardrails design](../../../docs/designs/risk-tiered-agent-guardrails.md)

<details>
<summary>Tracking details</summary>

**Status:** waiting
**Filed:** 2026-07-24, by codex, from the owner's review of task `2026-07-22-universal-guard-mode-configuration`
**Resolution evidence:** `memory/decisions/2026-07-24-revised-assurance-report-review-disposition.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f
**Reviewed revision:** ______
**Review outcome:** pending
**Supersedes:** `message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md`
**Depends on:** `message-queue/needs-agent/requests/future-blocking-revise-assurance-profile-scope-and-egress.md`
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.

</details>
