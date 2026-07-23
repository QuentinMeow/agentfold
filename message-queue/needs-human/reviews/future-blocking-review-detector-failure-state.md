# Should detector failures remain distinct from clean results and findings?

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.
**Look-at:** `docs/designs/risk-tiered-agent-guardrails.md`, “Treat the verifier as attack surface” and “Detector assurance”
**Why-you-might-care:** A crashed or incomplete scanner must not accidentally become evidence that content is safe.
**If-you-do-nothing:** Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.

## Context

The design distinguishes clean, finding, incomplete coverage, runtime error, and not
applicable. Mode then determines transition behavior; the detector result itself does
not change merely because a repository prefers less friction.

## Differences

- **Separate failure state:** preserves honest evidence; `hard` blocks while `soft`
  reports and continues.
- **Collapse failure into finding:** remains conservative but falsely says prohibited
  content was detected.
- **Collapse failure into clean:** maximizes availability but silently removes the
  security check during outages.

## Example

If a scan expected 20 files but processed zero, the run is incomplete. In `hard` the
commit waits for repair or authenticated break-glass; in `soft` the agent sees the
incomplete report and may continue, without claiming the content was clean.

**Your review:** ______
