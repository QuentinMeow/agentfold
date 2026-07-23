# Explain the guardrail review terms and repair the review interface

**Status:** in-repair
**Filed:** 2026-07-23, by the owner in chat
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`

Explain, in short plain language with contrasting examples, what “assurance profile,”
“template-first adoption,” self-authored acknowledgement, authenticated exception,
detector failure, and PII/credential recovery each mean. Link each explanation to the
exact source section.

Trace why the five questions appeared only in PR #4 rather than as actionable queue
items. Update the reusable review-writing guidance so every human action explains the
difference being judged, gives a concrete example, and points to complete context.

Done when the explanation is durable, the review questions are reissued through the
message queue where further human judgment is still needed, and orphan PR-only asks are
forbidden by the relevant contracts and skills.
