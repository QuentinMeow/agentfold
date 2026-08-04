# Handover — multi-worktree safety merge session

**Session:** 2026-08-04 00:18–02:44 PDT, codex planner
**Task:** 2026-08-03-plan-multi-worktree-safety-remediation; 2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check; 2026-08-04-stop-review-verdicts-from-looking-like-human-asks
**Mode:** async
**Queue projection:** v1

## What happened

- Retargeted pull request #79 to `main`, verified no open child still depended on the
  planning branch, and merged planning pull request #73 with merge commit
  `d098e2bae13298e030446a892f8d06035df43f08`.
- Claimed the stale-base task on `main` in `68aed030f383e918c3758d41afd67e77322bd985`.
  Its repaired workflow commit `2925399ffa9ae5c2054e3a1aaaf2cf9fbc3ee32b`
  passed the full suite and a fresh 3–0 adversarial review.
- Formalizing that review exposed a separate gate contradiction: the required structural
  `approve` token was classified as a new human request. Filed GitHub issue #80, created
  and claimed its canonical task, and bound the provider source. Main is green at
  `1995cf4652f0acdd9e8a24cca993c4d6c6cfff7a`.
- Three candidate parser repairs were stopped after adversarial review found progressively
  narrower fail-open or false-boundary cases: `85a044e6` received 0 approve / 3 block,
  `12a1f32` received 2 approve / 1 valid block, and `3de329d8` received 0 approve / 3 block.
- The next design removes general Markdown section inference. It accepts only one closed,
  contiguous receipt block — heading, one full reviewed revision, then consecutive
  one-line core-fit verdicts — and leaves every later line under normal action detection.
  The workspace safety reviewer requires fresh owner authorization before that
  security-sensitive parser/template edit.
- Pull request #79 remains draft and unmerged. No task branch or worktree was deleted;
  cleanup is intentionally deferred until every corresponding head is proven merged into
  final `main`.

## Decisions made for you

- The session preserved both the core-review gate and task-action admission. Publication is
  paused, and no false review receipt or hidden human ask reaches main.
- Issue #80 became its own core task and branch rather than widening stale-base issue #78.
  Combining them later would join two independently testable trust boundaries and erase
  their separate issue histories.
- The proposed repair is a closed receipt grammar after a partial CommonMark parser failed
  on block quotes, list-contained headings, link references, and thematic breaks. Its undo
  cost is a small parser/template revert; no repository data or provider setting moves.

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Authorize the closed review-receipt parser and template change, or decline it.](../../../message-queue/needs-human/decisions/non-blocking-authorize-the-closed-review-receipt-parser.md) — Why this matters: Without this authorization, completed independent review verdicts cannot be recorded without either a false human-action failure or an unsafe parsing exception. — If you do nothing: The parser repair and the dependent stale-base and bootstrap merges remain unpublished; current `main` stays unchanged and green.
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

- `av init` failed before writing stack metadata because Aviator invoked an unsupported Git
  `chdir --path-format=absolute` form. Manual retargeting preserved the stack safely.
- The first stale-base repair bound the candidate after core scope and failed a moved-base
  protected-path race. The dual-range repair at `2925399f` replaced it and passed review.
- Basename-only, open-ended ATX, and partial CommonMark receipt parsers all admitted shapes
  outside their claimed formal boundary. Their exact commits and panel votes remain in the
  task verification record; none was pushed.

## Next steps

- [After the GitHub issue is filed, keep it synchronized with the canonical task and close it only when the task's implementation is published or deliberately withdrawn.](../../../message-queue/needs-agent/requests/non-blocking-track-github-review-verdict-action-classification.md)
- [Triage GitHub issue #80 against its canonical task and retain this source binding until trusted provider evidence proves the issue closed.](../../../message-queue/needs-agent/requests/non-blocking-triage-github-issue-80-review-verdict-action-classification.md)
- [Keep GitHub issue #78 synchronized with its canonical task and close it only when the task's implementation is published or deliberately withdrawn.](../../../message-queue/needs-agent/requests/non-blocking-track-github-issue-78-stale-base.md)
- [Keep GitHub issue #74 synchronized with its canonical task and close it only when the task's implementation is published or deliberately withdrawn.](../../../message-queue/needs-agent/requests/non-blocking-track-github-issue-74-worktree-bootstrap.md)

## Deep links

- Planning merge: [pull request #73](https://github.com/QuentinMeow/agentfold/pull/73)
- Bootstrap implementation: [pull request #79](https://github.com/QuentinMeow/agentfold/pull/79)
- Parser defect: [issue #80](https://github.com/QuentinMeow/agentfold/issues/80)
- Stale-base task: `2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check`
- Review-receipt task: `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`
