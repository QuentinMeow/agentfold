# Review needed: Does the recovery plan begin at the right point after sensitive data may have escaped?
<!-- human-action-presentation: v2 -->

> **Waiting for your response.**

## What I need from you

**Action:** Review whether the incident-recovery boundary and sequence are complete; then approve, request changes by naming any missing recovery obligation, or reject.

Review whether prevention, pre-authorized exceptions, and post-exposure recovery are
separated clearly enough to guide later implementation.

## Why this matters

This prevents deleting one Git file from being mistaken for complete recovery after credentials or private data may already exist in remote copies and logs.

## If you do not respond

If you do not respond, unrelated work may continue but guardrail implementation cannot start and the recovery sequence remains only a proposal.

## What changed

**Before this change:** The design could leave readers with the false impression that deleting a repository file completes recovery after sensitive data escapes.

**Current state:** The exact design contains a proposed recovery sequence, but this review is unanswered and the sequence is not implemented.

**Change under review:** Prevention decides whether data may cross a boundary, an exception authorizes a narrow crossing before it happens, and recovery starts only after data may already have escaped.

**Not included:** Credential rotation support, exposure inventory, coordinated deletion, history repair, regression fixtures, and operational recovery tooling remain future work.

**Additional context:** Credential recovery revokes or rotates the secret first, then
  cleans history and adds a regression fixture. Private-data recovery first contains
  access and inventories every exposure surface before coordinated deletion or history
  rewriting.

## Review outcomes

### Approve

**What it means:** Accept the proposed boundary and recovery ordering as the basis for later guardrail implementation.

**Consequence:** Implementation may use this incident sequence after the remaining start-boundary reviews are satisfied.

**Example:** When an API key reaches a remote branch, rotate it before inspecting and cleaning clones, forks, CI logs, artifacts, mirrors, and host caches.

### Request changes

**What it means:** Preserve the recovery direction while naming a missing obligation or incorrectly ordered step.

**Consequence:** The start boundary stays closed until the design is repaired and a new exact revision is reviewed.

**Example:** Require an explicit notification or audit-preservation step before coordinated deletion begins.

### Reject

**What it means:** Decline this recovery model and require a different incident boundary or sequence.

**Consequence:** The proposal is withdrawn and guardrail implementation cannot start without a replacement recovery design.

**Example:** Reject if all post-exposure response must be delegated to an external incident-response system rather than described by AgentFold.

## Agent recommendation

**Evidence checked:** I compared the exact design's sensitive-data state model, containment sequence, credential-invalidating step, and remote-copy caveats against the review question.

**Assumptions:** Remote copies, logs, caches, and credentials may remain effective after the repository file is removed.

**Confidence:** High, because the sequence makes the irreversible exposure explicit and prioritizes containment or invalidation before cosmetic repository cleanup.

**Rationale:** The proposal correctly treats prevention, authorization, containment, credential invalidation, and cleanup as different operations rather than letting later deletion rewrite what already happened.

**What could change this recommendation:** A missing legal, notification, evidence-preservation, or provider-specific containment obligation would justify requesting changes.

**Recommendation:** Approve.

## Your response

Write `approve`, `request changes`, or `reject`, followed by any reason or requested
changes. You may also write `I need clarification`. A plain-language answer is enough;
the agent manages revision tracking.

**Your review:** ______

## References

**Full context:** [Risk-tiered agent guardrails design](../../../docs/designs/risk-tiered-agent-guardrails.md)

<details>
<summary>Tracking details</summary>

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Resolution evidence:** `memory/decisions/2026-07-23-sensitive-data-recovery-review-disposition.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f
**Reviewed revision:** ______
**Review outcome:** pending
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.

</details>
