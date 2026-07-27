# Reviews — judge one exact artifact

Only files whose tracking status is `waiting` need human review. `awaiting-artifact`
means the artifact is not ready, and `folding` means an agent is already recording a
response.

Each actionable file explains prior and current behavior, the change under review, and
anything excluded or not yet implemented. It compares approval, requested changes, and
rejection, then shows evidence, assumptions, confidence, rationale, and reversal
conditions before putting the agent's recommendation last. You can answer with one of
those three outcomes or ask for clarification under `Your response`; the agent manages
revisions and outcome fields. `abandoned` is agent-managed lifecycle state, not a
displayed human choice.

The collapsed tracking block binds one exact target and revision so an answer cannot
silently apply to changed bytes. A local file or HTTPS artifact uses its SHA-256; a Git
commit or range uses its full object identifier. Git targets also expose one exact
artifact link through a provider-neutral HTTPS URL or an existing repository-relative
artifact whose destination contains the bound commit id or both range ids. `Resolution
evidence` is a different non-queue file that records crossing or cancellation.

Agents create a timing-prefixed file from `templates/queue/review.md` and follow
`handbook/human-action-guide.md`.
