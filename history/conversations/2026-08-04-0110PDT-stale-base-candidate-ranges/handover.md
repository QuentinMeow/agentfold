# Handover — stale-base candidate ranges

**Session:** 2026-08-04 01:00–01:15 PDT, sol-high implementer
**Task:** 2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check
**Mode:** async
**Queue projection:** v1

## What happened

- The first adversarial panel blocked candidate `1da29e9` by a 2–1 vote because core scope
  could read its protected-path registry from stale event head `H` instead of candidate `M`.
- Candidate binding now occurs once, immediately after checkout and before either policy
  gate. Core scope receives `B2...M`; reconciliation receives `B2...H`.
- Literal workflow fixtures prove both named outputs reach their intended consumers and
  retain the fail-closed parent checks, direct-head path, and retry-free behavior.
- The repaired workflow module passes 25 tests, the full suite passes all 15 test files,
  and the staged core-scope and reconciler checks pass.

## How it works now

A direct event-head checkout gives both consumers `event_base...event_head`. For a synthetic
candidate `M(B2,H)`, core scope gets candidate-headed `B2...M`, so candidate-side policy
comes from the merged tree; the reconciler gets parent-shaped `B2...H`, so it binds `M` as
the exact two-parent merge. Both ranges come from one immutable checkout.

## Decisions made for you

- Kept the canonical Python gates unchanged and added no retry. The provider adapter now
  supplies each gate the range shape its existing contract needs; reverting remains a
  workflow-and-tests change with no data migration or provider-setting cost.
- Kept the displaced-tip observation outside this repair because task
  `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion` and GitHub
  issue #75 already own it.

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

- The first candidate bound the checked-out merge only inside the reconciler step. That was
  too late for core scope and let an advanced-base registry change escape its candidate read.
- A mutable-ref retry remains the wrong model because checkout already supplied the immutable
  tree that both consumers must judge.

## Next steps

- [Keep GitHub issue #78 synchronized with its canonical task and close it only when the task's implementation is published or deliberately withdrawn.](../../../message-queue/needs-agent/requests/non-blocking-track-github-issue-78-stale-base.md)

## Deep links

- Task folder: [task records](../../../tasks/1_in-progress/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/) · Worklog: [session history](../../../tasks/1_in-progress/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/worklog.md) · Verification: [recorded evidence](../../../tasks/1_in-progress/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/verification.md)
- Commits: `1da29e9` is the blocked first candidate; the repair remains uncommitted for the parent session
