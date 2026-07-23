# Handover — risk-tiered agent guardrails

**Session:** 2026-07-22 09:49–10:11 PDT, codex
**Task:** 2026-07-22-design-critical-agent-guardrails
**Mode:** async

## What happened

- Added the `docs/` service and `docs/designs/` endpoint, with root, README, skill, and
  roadmap routing updated to keep proposals separate from principles and ADRs.
- Wrote a research-backed design that explores guardrails breadth-first, defines
  consequence tiers, compares enforcement times, and deep-dives PII and credentials.
- Recommended layered policy, evidence, and enforcement: local feedback, explicit but
  untrusted self-receipts, authenticated critical exceptions, sink-specific egress
  controls, deployment assurance profiles, detector canaries, and history response.
- Revised the design after three adversarial reviewers found forgeable receipts,
  authority/sink replay, outage deadlocks, unsafe filename diagnostics, and contextual
  carry-forward gaps; all three approved the revision.

## How it works now

The repository now has a durable home for proposed technical designs. The guardrail
document is a proposal only: it changes no enforcement behavior and explicitly prevents
future agents from treating the recommendation as an accepted ADR.

## Decisions made for you

- Recommended, but did not accept, the risk-tiered layered approach; alternatives and
  rejected sole solutions are in `docs/designs/risk-tiered-agent-guardrails.md`.

## Needs your attention

- [Risk-tiered guardrails proposal](message-queue/needs-human/reviews/risk-tiered-agent-guardrails.md): review the proposed PII/security boundary and the new docs routing contracts. If you do nothing, the design remains proposed and no guardrail implementation begins.
- [Earlier design-review wording](message-queue/needs-human/reviews/design-review-direct-fixes.md): your working tree already contains `**Resolution:** ack`; I preserved that unrelated, uncommitted edit and did not fold or delete the queue item. No new wording decision is needed from this session.
- [Provenance principle wording](message-queue/needs-human/reviews/provenance-principle-wording.md): decide whether the five instruction-bearing paths and mandatory human review in autonomous mode are the right trust boundary. If you do nothing, the principle stands as written and mechanical enforcement remains backlog work.

## Dead ends

- A self-authored, content-bound acknowledgement initially looked like proof that review
  occurred. The panel demonstrated it is forgeable; the final design treats it only as
  anti-forgetting friction and requires authenticated external authority for critical
  exceptions.

## Next steps

Have a maintainer review or accept the proposal. If accepted, implementation should
start with data classification, sink inventory, and honest deployment assurance profiles
before selecting a PII scanner.

## Deep links

- Task folder: `tasks/4_done/2026-07-22-design-critical-agent-guardrails/` · Worklog: `tasks/4_done/2026-07-22-design-critical-agent-guardrails/worklog.md` · Verification: `tasks/4_done/2026-07-22-design-critical-agent-guardrails/verification.md`
- Commits: `2e10097`, `1da2af3`, `e37ca4a`
