# Revise assurance wording and make controlled egress reference-only

**Status:** open
**Filed:** 2026-07-24, by codex, from the owner's review of task `2026-07-22-universal-guard-mode-configuration`
**Action:** Replace selectable assurance profiles with composable guard bindings and derived per-obligation reports, and make controlled egress reference-only pending a separate explicit human-approved proposal.
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Resolution evidence:** `docs/designs/risk-tiered-agent-guardrails.md`
**Supersedes:** `message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md`
**Follow-up review:** `message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md`
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.

## What you need to know

The owner approved independently configured guards with assurance derived from observed
coverage, detector health, and enforcement for each obligation and scope. The current
design instead presents deployment profiles that look selectable and treats controlled
egress as active future architecture.

## Done when

The design explains composable guard bindings, manual semantic evidence, deterministic
coverage limits, and mechanically derived reports; controlled egress appears only as an
unapproved reference, and the follow-up review is bound to the revised bytes.
