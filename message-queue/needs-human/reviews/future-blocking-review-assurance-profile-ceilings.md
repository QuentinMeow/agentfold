# Do the four assurance-profile ceilings match the security claims you want?

**Status:** awaiting-artifact
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** Confirm the four claim ceilings below, or name a profile whose promise should change.
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review target:** pending
**Review revision:** pending
**Reviewed revision:** ______
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.
**Look-at:** `docs/designs/risk-tiered-agent-guardrails.md`, “Deployment assurance profiles”
**Why-you-might-care:** Profile names must not advertise stronger protection than their actual enforcement boundary.
**If-you-do-nothing:** Guardrail implementation waits at its start boundary; the current proposal remains unchanged.

## What you need to know

A guard **mode** says how one check runs (`hard`, `soft`, `off`, or `manual`). An
**assurance profile** says the strongest security promise the whole installed deployment
can honestly make after considering every active control and its authority.

## Differences

- **Feedback only:** a bypassable local scan catches ordinary mistakes.
- **Merge protected:** trusted hard CI can stop merge, but the data may already be on a
  remote PR branch.
- **Repository admission:** a server-side gate prevents rejected objects from becoming
  reachable refs, although the host processed the attempted push.
- **Controlled egress (future):** admission plus an external filesystem/network boundary
  and guarded credentials protects every declared outbound sink.

## Example

A repository with pre-commit plus required CI may say “prohibited findings cannot
merge.” It may not say “PII cannot reach GitHub,” because the branch reached GitHub
before CI. The stronger statement needs repository admission or controlled egress.

When answering here, copy `Review revision` into `Reviewed revision` so the answer
stays bound to the exact design bytes.

**Your review:** ______
