# Handover — rebuild the review receipt parser

**Session:** 2026-08-07 09:15 – 2026-08-08 01:30 PDT, claude opus 5 orchestrator with delegated implementer and five review panels
**Task:** 2026-08-04-stop-review-verdicts-from-looking-like-human-asks; 2026-08-03-make-linked-worktree-bootstrap-concurrency-safe
**Mode:** async
**Queue projection:** v1

## What happened

- Every worktree from the earlier sessions was gone: they had been created under the system
  temporary directory, which the operating system clears between sessions. No commit was
  lost, but the stale-base branch existed only in this clone until it was pushed. Seven dead
  records were pruned and the live ones recreated as siblings of the repository, which is
  what `handbook/git-workflow.md` already prescribed.
- Pull request 79 had become unmergeable. Its only conflict was the generated queue digest,
  regenerated rather than hand-resolved, verified green, and pushed; it is mergeable again.
- A panel found the review-receipt implementation contained a fail-open on the merge gate's
  own output: a rejecting panel was reported as an approving one. The owner chose to
  withdraw it, so `automation/` and `templates/` were restored to the default branch and the
  work rebuilt from that baseline.
- The rebuild is one 339-line module both gates import, at 1,515 added lines against the
  withdrawn 3,746. Five further panels found and closed two fail-opens, two regressions this
  session caused, and a class of test that claimed to pin a fix and did not.
- Three independent reviewers approved the final revision. The gate now reports
  `independent review verified` on this task's own receipt, which is the behaviour the task
  exists to provide, and pull request 82 is open.

## How it works now

A receipt is one exact `## Review verdicts` heading, one full commit id, then consecutive
`- core-fit / <reviewer>: <approve|block> — <finding>` lines, read by one parser both gates
share. The human-action gate blanks only the verdict token, so the reviewer name and the
finding stay under ordinary detection. Anything reaching for the verdict shape and missing
refuses the whole receipt with a file, a line and a reason. The finding is free prose.

## Decisions made for you

- None new. The owner's withdrawal decision is recorded in
  [the amending ADR](../../../memory/decisions/2026-08-07-withdraw-the-first-review-receipt-implementation.md),
  which narrows only the implementation-scope clause of the 2026-08-04 authorization and
  names the six mechanisms a rebuild may not reintroduce without its own decision.
- The merge-transition check reports two findings from intermediate commits that were green
  when made. Judged this as covered by the existing advisory-merge-gate decision rather than
  a new question, and filed the retroactivity defect as a backlog task. Undoing that costs
  one queue item.

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Choose which of three shapes the rule for externally changed instruction files takes: holding the adopting work, holding nothing, or holding the merge itself.](../../../message-queue/needs-human/decisions/non-blocking-choose-the-gate-for-externally-changed-instruction-files.md) — Why this matters: Anyone who can open a pull request here can edit the files that direct every agent, and the rule meant to catch that promises a hold this repository can no longer apply. — If you do nothing: Nothing stops. The rule keeps promising a hold no file can express, so an outside edit to an instruction file is reviewed only if the agent that happens to see it decides to ask.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why this matters: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. — If you do nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why this matters: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. — If you do nothing: The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
- [Choose whether the nine older waiting questions are left as written, replaced with plainer versions, or replaced only where their wording is now stale.](../../../message-queue/needs-human/decisions/non-blocking-re-ask-the-older-questions-in-plainer-words.md) — Why this matters: Nine of the questions in your queue were written in a format that buries the choice under bookkeeping, and four of them still ask about a moment that has already passed. — If you do nothing: They stay exactly as written and stay answerable; only questions filed from now on use the readable shape.
- [Choose whether an agent corrects the stale numbers in two principle files now, leaves them alone, or gets a standing permission to correct facts of this kind without asking.](../../../message-queue/needs-human/decisions/non-blocking-stop-a-principle-from-copying-the-line-budget.md) — Why this matters: The nine principle files are the most-quoted documents here, and one of them tells agents a size limit smaller than the real one, so an agent will cut a contract that was never too long. — If you do nothing: Nothing stops. The two files keep quoting numbers that are no longer true, and every agent that reads them inherits the wrong ones.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md) — Why this matters: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. — If you do nothing: The merged design and its inspector stand, and its task completes without your judgment on record.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why this matters: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. — If you do nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md) — Why this matters: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. — If you do nothing: The merged boundary stands as the repository-wide test boundary, and its task completes without your judgment on record.
- [Say whether this is the standard every human-facing message is held to, or name what to change.](../../../message-queue/needs-human/reviews/non-blocking-review-the-explanation-standard.md) — Why this matters: Every report, pull request, and question you get from an agent from now on is written to this standard, so a wrong rule here compounds across every future message. — If you do nothing: The standard stands as written and agents follow it; nothing stops, and it can be changed later by editing one file.
- [Say whether this pull-request shape works for you, or name the section to move, add, or drop.](../../../message-queue/needs-human/reviews/non-blocking-review-the-pull-request-shape.md) — Why this matters: This is the shape of every pull request you are asked to look at from now on, and it decides what you see before you have to click anything. — If you do nothing: The shape stands and every later pull request uses it; nothing stops, and changing it later means editing two files and one test.

## Dead ends

- Widening what the parser accepts is what grew the withdrawn implementation to 3,746 lines;
  each new shape needed another special case. Widening what it refuses cannot admit anything
  new, so it is safe by construction. The rule that held was broad refusal with narrow
  acceptance.
- Bounding the refusal scan for speed cost coverage and bought nothing measurable. A bound
  on a rejector is a coverage decision wearing an optimization's clothes.
- Closed enumerations in prose ("exactly five routes", "three shapes escape") were falsified
  by a reviewer every round for three rounds. State rules, never inventories.
- A test whose fixture differs from its decoy by one character can pass while pinning
  nothing. Two tests here claimed to pin fixes and did not; an executable mutation script
  found it, and a docstring never would.
- Probing a gate by editing a working tree proves nothing: the gates read committed content
  over their diff range.

## Next steps

- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-withdrawn-exemption-from-dirtying-past-edges.md)
- [Triage GitHub issue #80 against its canonical task and retain this source binding until trusted provider evidence proves the issue closed.](../../../message-queue/needs-agent/requests/non-blocking-triage-github-issue-80-review-verdict-action-classification.md)

## Deep links

- Task folder: [review-receipt task](../../../tasks/3_in-review/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/) · Worklog: [session record](../../../tasks/3_in-review/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/worklog.md) · Verification: [six panels, receipt and residue](../../../tasks/3_in-review/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md)
- Pull requests: https://github.com/QuentinMeow/agentfold/pull/82 · https://github.com/QuentinMeow/agentfold/pull/79
- Reviewed revision: `66c6e57b56c9995362fc6b01f7e6130d21866ecd`
