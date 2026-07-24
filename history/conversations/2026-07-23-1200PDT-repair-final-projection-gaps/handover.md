# Handover — repair final projection gaps

**Session:** 2026-07-23 12:00–12:44 PDT, codex subagent
**Task:** 2026-07-23-first-class-message-queue
**Mode:** async
**Queue projection:** v1

## What happened

- Made visible unchecked Markdown tasks actionable without enumerating their verbs,
  while checked history and code examples remain descriptive.
- Closed invisible Unicode command obfuscation only in the isolated visible-prose
  detection view; Markdown destinations and code bytes remain structural or literal.
- Preserved external assignment identity and actor direction through a generic
  envelope, with one distinct actor-matching queue link required per assignment.
- Mapped GitHub users and teams to human actions, bots to agent actions, and unknown
  account types or missing identities to a closed failure.
- Updated mixed-surface no-action guidance and passed all 87 projection/provider tests,
  Python compilation, workflow parsing, exact jq mapping, and the Git whitespace check.

## How it works now

An unchecked task-list marker is itself a pending-action signal; command recognition no
longer depends on knowing verbs such as “migrate.” Detection normalizes only prose left
after Markdown code and destinations are removed, so invisible format characters cannot
split command words without rewriting literal or structural content.

Provider adapters emit `{actor, identity}` assignments. The projection gate counts
distinct canonical links separately for `needs-human` and `needs-agent`; GitHub maps
`User` and team assignments to the former and `Bot` assignments to the latter, failing
unknown types closed. Mixed PR descriptions use exact `No queued action requested.`
when their selected task scope and assignment state are both empty.

## Decisions made for you

None.

## Needs your attention

- [Confirm the four claim ceilings below, or name a profile whose promise should change.](../../../message-queue/needs-human/reviews/future-blocking-review-assurance-profile-ceilings.md) — Why-you-might-care: Profile names must not advertise stronger protection than their actual enforcement boundary. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current proposal remains unchanged.
- [Confirm the separate failure state and its mode-dependent transition behavior, or describe the desired alternative.](../../../message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md) — Why-you-might-care: A crashed or incomplete scanner must not accidentally become evidence that content is safe. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the separate failure state remains a proposal.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

Adding “migrate” to the command verb list was rejected because every future unseen verb
would reopen the same bypass. Treating all external assignments as human actions was
also rejected because one unrelated human link could then satisfy an assigned bot. A
full reconciler run cannot inspect untracked handovers from its candidate snapshot;
direct strict-entry validation passed six of six, while full reconciler evidence
remains unavailable until the staged integration snapshot.

## Next steps

None.

## Deep links

- Task folder: [task](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/) · Worklog: [worklog](../../../tasks/1_in-progress/2026-07-23-first-class-message-queue/worklog.md) · Verification: pending
- Commits: none — unstaged repair
