# Does the revised derived-assurance model match the approved direction?

**Status:** waiting
**Filed:** 2026-07-24, by codex, from the owner's review of task `2026-07-22-universal-guard-mode-configuration`
**Action:** Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Resolution evidence:** `memory/decisions/2026-07-24-revised-assurance-report-review-disposition.md`
**Why-you-might-care:** The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label.
**If-you-do-nothing:** Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:344a30c86bba805c4b78093b2916a0dffd1fcc98c3085dc85f5fbfbd09b5773f
**Reviewed revision:** ______
**Review outcome:** pending
**Supersedes:** `message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md`
**Depends on:** `message-queue/needs-agent/requests/future-blocking-revise-assurance-profile-scope-and-egress.md`
**Answer by:** 2026-10-22
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.

## What you need to know

The owner approved configuring individual guards while deriving assurance separately
for each obligation and scope. This follow-up will review the exact revised design; it
cannot be answered until the repair publishes an immutable content digest.

## Differences

- **Approve the revision:** the design clearly separates configurable guards from
  derived reports and keeps controlled egress outside approved work.
- **Request another wording change:** the conceptual decision remains, while an agent
  repairs the named ambiguity and republishes a new exact revision.
- **Reverse the decision:** requires a new explicit decision and durable record rather
  than silently restoring selectable profiles.

## Example

A credential rule may combine manual semantic inspection, hard merge checks, and hard
remote admission. The report lists each observed capability for that credential scope;
turning manual review off does not erase an independently verified admission gate, and
it does not pretend semantic review ran.

Do not answer while this item is `awaiting-artifact`. When it becomes `waiting`, copy
`Review revision` into `Reviewed revision` with the answer.

**Your review:** ______
