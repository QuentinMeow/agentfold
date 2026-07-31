# Handover — let-a-human-answer-in-one-edit

**Session:** 2026-07-31 06:40–09:10 PDT, local time, claude (worktree agent-a96648202c9c88cbe)
**Task:** 2026-07-31-let-a-human-answer-in-one-edit
**Mode:** async
**Queue projection:** v1

## What happened

- The one thing this repository exists to do — you answering a queued item — could not
  be committed. Answering a review the way root `AGENTS.md` describes was rejected by
  two checks, and by a third if the sentence named a file. All three were reproduced
  against the real repository first; the before-and-after output is in the task's
  `verification.md`.
- You can now answer any item by replacing the blank with one sentence and committing.
  Nothing else on the page is yours. A file path you mention in that sentence is read as
  prose, so naming a file that does not exist yet no longer breaks your commit.
- A review's `Reviewed revision` and `Review outcome` are now written by the agent when
  it claims the item, not by you. They are still required before anything resolves or
  merges — the change is who writes them and when.
- No queue template could be copied and filled in without failing. All five failed; 13
  findings in total. All five now pass, one at a time and together, and a test copies and
  fills every one of them on every run.
- Seven schema fields that the code requires but no template shows are now listed in
  `templates/README.md`, with the file that carries each.

## How it works now

You answer while the item says `waiting`. The agent then makes one commit that moves it
to `folding`; for a review, that same commit copies the revision you were shown into
`Reviewed revision` and records the outcome. That commit may change nothing else. It is
refused if your response was not already committed before it, if it tries to point the
approval at different bytes, or if it tries to reword what you wrote — so an agent cannot
invent an answer and approve it in one move. Every queue template is now valid as soon as
its `<placeholders>` are filled, and ships as `non-blocking-` because live timing may
only ever escalate.

## Decisions made for you

- The conservative fix shipped: who supplies the two review fields moved, rather than the
  fields being deleted or you being taught to write them. Reasoning in the task's
  `design.md`.
- Queue templates default to the `non-blocking-` delivery class, because that is the only
  starting point live timing may always escalate away from. Same file.
- The aggressive alternative — requiring a specific word in your own text before an agent
  may record `approved` — was written up rather than shipped, and is queued below as a
  choice for you.

## Needs your attention

- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/future-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why-you-might-care: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. || If-you-do-nothing: The three reviews stay live and unanswered, their three tasks stay in review forever, and the queue keeps carrying three asks that no repository action can close.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Choose Option A or Option B, or state another rule for how an approval is derived from human text.](../../../message-queue/needs-human/decisions/non-blocking-require-a-human-token-before-an-agent-records-approved.md) — Why-you-might-care: Every boundary that requires `approved` currently rests on one agent's reading of one English sentence, and no check can tell a truthful reading from a false one. || If-you-do-nothing: Option A stays. Approvals remain agent-attested readings of immutable human text, and the known-issue file keeps saying so.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- Making the templates carry all three timing blocks as real field lines does not work:
  the schema rejects a field belonging to another delivery class, so a filled copy would
  fail with "contradicts the ... filename". Shipping one default class and documenting
  the escalation once is what actually survives a copy.
- Asserting in a test that each schema marker is still present on its owning contract
  file made `test_reconcile_queue.py` read five record paths, which the narrow test lane
  deliberately deletes from its projection. The reconciler's own schema-activation checks
  already enforce presence, so the test asserts only what `templates/README.md` says.

## Next steps

None.

## Deep links

- Task folder: [2026-07-31-let-a-human-answer-in-one-edit](../../../tasks/1_in-progress/2026-07-31-let-a-human-answer-in-one-edit) · Worklog: [worklog.md](../../../tasks/1_in-progress/2026-07-31-let-a-human-answer-in-one-edit/worklog.md) · Verification: [verification.md](../../../tasks/1_in-progress/2026-07-31-let-a-human-answer-in-one-edit/verification.md)
- Commits: 2397aec..HEAD on task/2026-07-31-let-a-human-answer-in-one-edit
