# Is the boundary between acknowledgement and exception authority correct?

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review target:** `docs/designs/risk-tiered-agent-guardrails.md`
**Review revision:** sha256:e2314db67388c8aaf7980b6b66c945605db0822c2f52502c0a38c401d5458392
**Reviewed revision:** ______
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.
**Look-at:** `docs/designs/risk-tiered-agent-guardrails.md`, “Bind evidence to exact bytes and policy” and “Content-bound acknowledgement”
**Why-you-might-care:** Treating an agent-authored receipt as approval would let the producing agent waive its own security gate.
**If-you-do-nothing:** Guardrail implementation waits at its start boundary; the current authority split remains a proposal.

## What you need to know

A self-authored acknowledgement is an anti-forgetting receipt bound to the content the
agent considered. An authenticated exception is permission from a distinct authority,
bound to repository, ref, sink, content, reason, and expiry.

## Differences

- **Acknowledgement:** useful evidence of deliberation, but untrusted because the
  producing agent can write it.
- **Authenticated exception:** independently verifiable authority that can permit one
  narrowly scoped critical finding.

## Example

An agent may record why a public business email is allowed. It may not dismiss an API
key by writing `approved`; that needs a protected provider approval or signature whose
credential the producing agent cannot access.

When answering here, copy `Review revision` into `Reviewed revision` so the answer
stays bound to the exact design bytes.

**Your review:** ______
