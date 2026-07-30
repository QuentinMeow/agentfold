# Handover — locate Superpowers plugin

**Session:** 2026-07-28 22:34–22:43 PDT, codex
**Task:** none — exploratory
**Mode:** async
**Queue projection:** v1

## What happened

- Located the enabled Superpowers Codex plugin in the user-level plugin cache.
- Confirmed its manifest is version 5.1.3 and its bundle contains 14 workflow skills.
- Traced every screenshot entry: two AgentFold skills, one private job-search skill, and two optional curated plugins.
- Located `coding-interview` in the private overlay of `jobs-finder-combined`, explaining why it appears in global usage history but not this repository.
- Confirmed the official Codex manual exposes installed plugins through the Plugins directory's Installed row and loads bundled skills into new chats.

## How it works now

Codex enables the optional `superpowers@openai-curated` and `github@openai-curated` plugins in the user-level configuration. Superpowers contributes 14 development-workflow skills; GitHub contributes four routing, CI, review-feedback, and publishing skills plus connector tools. AgentFold contributes `adversarial-review` and `session-handover`, while the private `jobs-finder-combined` overlay contributes `coding-interview`.

## Decisions made for you

None.

## Needs your attention

- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- Looking under AgentFold's `skills/` or `~/.codex/skills` does not reveal Superpowers because plugin-provided skills live inside the plugin cache.
- Looking for `coding-interview` in the current repository is also misleading; it is a private, repository-scoped skill mounted under `jobs-finder-combined/private/skills/`.

## Next steps

None.

## Deep links

- Task folder: none · Worklog: none · Verification: none
- Sources: user-level Codex plugin configuration, installed plugin manifests, AgentFold skill files, and the private coding-interview skill
- Commits: none
