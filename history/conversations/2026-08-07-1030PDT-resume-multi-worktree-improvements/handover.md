# Handover — resume multi-worktree improvements

**Session:** 2026-08-07 09:15–10:45 PDT, claude opus 5 orchestrator with three independent review agents
**Task:** 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; 2026-08-03-make-linked-worktree-bootstrap-concurrency-safe
**Mode:** async
**Queue projection:** v1

## What happened

- Every worktree from the earlier sessions was gone. They had been created under the system
  temporary directory, which the operating system clears between sessions, while
  `handbook/git-workflow.md` prescribes a sibling of the repository. No commit was lost, but
  the stale-base branch was still unpushed and existed only in this clone. Seven dead
  worktree records were pruned and the live ones recreated at the prescribed path.
- Pull request 79 had become unmergeable. The only conflict was the generated queue digest,
  which was regenerated from its sources rather than hand-resolved. The merge was verified
  green and pushed, and the pull request is mergeable again.
- A three-lens independent panel examined the review-receipt parser at revision
  `ccbb9e4854faf42dc423638e6b6b39a284608f4b`. All three reviewers rejected it. Their
  verdicts and reproductions are recorded in the task's verification file.
- The decisive finding is a fail-open on the merge gate's own output: a verdict whose
  one-line finding leaves a narrow allowed character set is discarded together with every
  later verdict, so a panel of one approval and two rejections is reported as one approval
  and zero rejections. This session reproduced that independently before recording it.
- Nothing was published for the blocked task, and no parser or template byte was changed.

## How it works now

The review-receipt work stays in `1_in-progress` on its branch with no pull request; the
default branch is unchanged and green. The linked-worktree bootstrap branch has taken the
default branch in, passes the full suite and its nine focused tests, and its pull request
is mergeable. The stale-base branch is untouched at its reviewed revision and is
still the only branch that exists solely in this clone.

## Decisions made for you

- Recorded the panel and stopped, rather than starting a seventeenth repair round. The
  authorized shape is smaller than what shipped, so the choice went to the owner as a
  [queue decision](../../../message-queue/needs-human/decisions/non-blocking-repair-or-withdraw-the-review-receipt-parser.md).
  Undoing this costs nothing: no code changed and the branch is intact.
- Resolved the pull-request 79 conflict by regenerating the digest instead of merging its
  text, because that file is generated and its sources had both moved. Undoing it is one
  regeneration command.

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Choose which of three shapes the rule for externally changed instruction files takes: holding the adopting work, holding nothing, or holding the merge itself.](../../../message-queue/needs-human/decisions/non-blocking-choose-the-gate-for-externally-changed-instruction-files.md) — Why this matters: Anyone who can open a pull request here can edit the files that direct every agent, and the rule meant to catch that promises a hold this repository can no longer apply. — If you do nothing: Nothing stops. The rule keeps promising a hold no file can express, so an outside edit to an instruction file is reviewed only if the agent that happens to see it decides to ask.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why this matters: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. — If you do nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why this matters: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. — If you do nothing: The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
- [Choose whether the nine older waiting questions are left as written, replaced with plainer versions, or replaced only where their wording is now stale.](../../../message-queue/needs-human/decisions/non-blocking-re-ask-the-older-questions-in-plainer-words.md) — Why this matters: Nine of the questions in your queue were written in a format that buries the choice under bookkeeping, and four of them still ask about a moment that has already passed. — If you do nothing: They stay exactly as written and stay answerable; only questions filed from now on use the readable shape.
- [Choose whether the review-receipt work is repaired in place, withdrawn and rebuilt to the smaller shape you authorized, or left exactly as it is.](../../../message-queue/needs-human/decisions/non-blocking-repair-or-withdraw-the-review-receipt-parser.md) — Why this matters: The check that decides whether independent reviewers approved a change can count a panel that rejected it as a panel that approved it. — If you do nothing: Nothing stops. The current branch stays unpublished and unmerged, the default branch stays green and unchanged, and three finished repairs stay unreleased.
- [Choose whether an agent corrects the stale numbers in two principle files now, leaves them alone, or gets a standing permission to correct facts of this kind without asking.](../../../message-queue/needs-human/decisions/non-blocking-stop-a-principle-from-copying-the-line-budget.md) — Why this matters: The nine principle files are the most-quoted documents here, and one of them tells agents a size limit smaller than the real one, so an agent will cut a contract that was never too long. — If you do nothing: Nothing stops. The two files keep quoting numbers that are no longer true, and every agent that reads them inherits the wrong ones.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md) — Why this matters: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. — If you do nothing: The merged design and its inspector stand, and its task completes without your judgment on record.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why this matters: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. — If you do nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md) — Why this matters: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. — If you do nothing: The merged boundary stands as the repository-wide test boundary, and its task completes without your judgment on record.
- [Say whether this is the standard every human-facing message is held to, or name what to change.](../../../message-queue/needs-human/reviews/non-blocking-review-the-explanation-standard.md) — Why this matters: Every report, pull request, and question you get from an agent from now on is written to this standard, so a wrong rule here compounds across every future message. — If you do nothing: The standard stands as written and agents follow it; nothing stops, and it can be changed later by editing one file.
- [Say whether this pull-request shape works for you, or name the section to move, add, or drop.](../../../message-queue/needs-human/reviews/non-blocking-review-the-pull-request-shape.md) — Why this matters: This is the shape of every pull request you are asked to look at from now on, and it decides what you see before you have to click anything. — If you do nothing: The shape stands and every later pull request uses it; nothing stops, and changing it later means editing two files and one test.

## Dead ends

- Probing the receipt gate by editing a working tree proved nothing: `check_core_scope.py`
  reads committed content over its diff range, so uncommitted edits are invisible to it.
  Calling `core_fit_review_evidence` directly is the way to test receipt parsing.
- Suspecting the stranded-looking `folding` item in the queue was a missed cleanup was
  wrong. Future-timing items survive their answer until their boundary is crossed, and its
  durable record was written correctly two weeks ago.
- Suspecting the task's own verification file could no longer host a receipt was also
  wrong. Its nineteen historical revision fields are correctly ignored, and the parser
  extracts exactly one receipt from it.

## Next steps

- [Triage GitHub issue #80 against its canonical task and retain this source binding until trusted provider evidence proves the issue closed.](../../../message-queue/needs-agent/requests/non-blocking-triage-github-issue-80-review-verdict-action-classification.md)
- [Keep GitHub issue #74 synchronized with its canonical task and close it only when the task's implementation is published or deliberately withdrawn.](../../../message-queue/needs-agent/requests/non-blocking-track-github-issue-74-worktree-bootstrap.md)
- [Keep GitHub issue #78 synchronized with its canonical task and close it only when the task's implementation is published or deliberately withdrawn.](../../../message-queue/needs-agent/requests/non-blocking-track-github-issue-78-stale-base.md)

## Deep links

- Task folder: [review-receipt task](../../../tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/) · Worklog: [session record](../../../tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/worklog.md) · Verification: [sixteenth panel and reproductions](../../../tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md)
- Commits: `817209d` on the review-receipt branch; `3446053` on the bootstrap branch
- Pull request: https://github.com/QuentinMeow/agentfold/pull/79
