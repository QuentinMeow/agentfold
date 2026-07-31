# Handover — queue resolution design exploration

**Session:** 2026-07-30 13:47–17:25 PDT, Claude
**Task:** none — design exploration ahead of a task
**Mode:** async
**Queue projection:** v1

## What happened

- Retired two superseded local branches earlier in the session; that work is recorded in its
  own handover at `history/conversations/2026-07-30-1347PDT-retire-superseded-branches/`.
- Explored how a queue item can be resolved when its work landed in an earlier commit. Nine
  independent agents ran: three mapping and researching, four designing materially different
  approaches, three attacking the results.
- Established that the current gate is already empty. Appending a probe line to the declared
  evidence file clears the finding completely, reproduced twice on disposable clones.
- Designed four approaches in full and attacked three of them. All three attacked designs were
  returned as do-not-ship, and all three failed for the same reasons.
- Wrote the proposal at `docs/designs/queue-resolution-order-independence.md` recommending the
  smallest change rather than any of the four, and kept every deep document in `artifacts/`
  beside this file.

## How it works now

Nothing in the checker changed. The proposal is a proposal, and the live stuck item at
`message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`
is still unresolvable. The unmerged branch carrying the finished lineage-baseline
implementation is unchanged and should not merge as it stands; verification found it makes all
14 live ordinary requests deletable with no work, adds an unrepairable finding on immutable
history, and turns a shallow clone into a silent exit-2 that blocks every commit. Its caching
work is a real 2.7x win on the hot path and is worth keeping separately.

## Decisions made for you

None. The proposal deliberately leaves one open choice — widen the window and move strictness
to filing time, or delete the resolution-evidence gate entirely — and its "Recommendation"
section states the case for each.

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

Three elaborate redesigns were built and then abandoned on evidence: a level-triggered
predicate grammar, an append-only resolution log with compaction, and commit-pinned receipts.
Each was returned do-not-ship by an independent reviewer, and each failed the same way — it
kept a gate satisfiable without doing the work, added a new field to items governed by a
whole-text identity check and so manufactured a fresh way to brick the repository, and paid
for the residue with an escape hatch its own author called load-bearing. The convergence
across three separate reviewers is the reason the proposal recommends none of them. Do not
restart from any of the four without reading the adversarial verdicts in `artifacts/` first.

Two measurement traps also cost time. Comparing the lineage-baseline branch against main at
full history compares a 246-commit history to a 317-commit one and reports a speedup that
reverses once de-confounded. And the widely repeated figure of 92 to 312 seconds measures the
queue check's test file rather than the check, which costs about a fifth of a second.

## Next steps

None.

## Deep links

- Task folder: none · Worklog: none · Verification: `docs/designs/queue-resolution-order-independence.md`
- Commits: this handover and the proposal beside it
