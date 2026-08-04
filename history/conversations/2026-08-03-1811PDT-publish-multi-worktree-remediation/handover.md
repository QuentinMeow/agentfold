# Handover — publish multi-worktree remediation

**Session:** 2026-08-03 18:11 PDT, codex
**Task:** 2026-08-03-plan-multi-worktree-safety-remediation; 2026-08-03-make-linked-worktree-bootstrap-concurrency-safe
**Mode:** async
**Queue projection:** v1

## What happened

- Published draft planning pull request #73 with the audit, canonical parent task, plan,
  design, two newly filed implementation tasks, and the dependency order.
- Filed GitHub issues #74–#78 and bound each exact issue version to a task-owned queue
  action and a stable projection ledger, keeping repository files canonical.
- Implemented issue #74 in a real linked worktree and published stacked draft pull request
  #79. Eight focused tests cover six concurrent fresh worktrees, twelve concurrent reruns,
  shared and worktree Git config, lock failure paths, and adapter races.
- Sol xhigh adversarial review initially blocked three concrete bugs; all three were fixed,
  the exact implementation commit was approved, and an independent Terra pass reran the
  focused suite, reconciler, and diff check successfully.

## How it works now

On pull request #79, bootstrap converges the common repository's hook setting without
rewriting correct state, verifies and repairs a masking worktree override locally, and then
creates adapters in the current checkout. It preserves real paths and stale links rather
than risking a clobber. The behavior is not on `main`; #79 is stacked on planning PR #73.

## Decisions made for you

- Chose serial vertical implementation slices because shared reconciler/workflow changes can
  combine into a red trunk even when sibling branches pass independently. Reordering later
  slices is cheap; parallelizing them reintroduces the audited integration risk.
- Kept GitHub issues as projections rather than sources of truth. This adds queue records but
  preserves the repository's existing task/action authority; undoing it requires closing the
  issues with trusted provider evidence and resolving their bindings.
- Kept server-side required merge enforcement deferred because enabling it would contradict
  the accepted advisory-gate decision. No provider policy or default branch was changed.

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

- The GitHub connector could read but not write this repository; authenticated `gh` was used
  for issue and pull-request creation after its write returned 403.
- GPT-5.6 Luna was unavailable; Terra handled the mechanical worker/test roles instead.
- The first implementation passed its own tests but adversarial review still found three
  untested races. Publication waited for fixes, regression tests, and revision-bound approval.

## Next steps

- [Keep GitHub issue #74 synchronized with its canonical task and close it only when the task's implementation is published or deliberately withdrawn.](../../../message-queue/needs-agent/requests/non-blocking-track-github-issue-74-worktree-bootstrap.md)
- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-restack-from-being-blamed-for-another-branchs-deletion.md)
- [Claim the explicit-lease task and remove this pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-bind-task-branch-pushes-to-observed-tips.md)

## Deep links

- Parent task: `tasks/1_in-progress/2026-08-03-plan-multi-worktree-safety-remediation/` · [Child verification](https://github.com/QuentinMeow/agentfold/blob/7f3bb6fd44b5ab7a78cbba5a8d6ac22fc7a3f49d/tasks/3_in-review/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe/verification.md)
- Pull requests: https://github.com/QuentinMeow/agentfold/pull/73 · https://github.com/QuentinMeow/agentfold/pull/79
- Issues: https://github.com/QuentinMeow/agentfold/issues/74 through https://github.com/QuentinMeow/agentfold/issues/78
- Reviewed implementation: `c0c7b19bb1256fb22a0dc85fc5aa5b0da6941b75`
