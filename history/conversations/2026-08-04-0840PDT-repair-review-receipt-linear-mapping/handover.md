# Handover — linear receipt mapping

**Session:** 2026-08-04 08:40–08:59 PDT, codex sol-high implementer
**Task:** 2026-08-04-stop-review-verdicts-from-looking-like-human-asks
**Mode:** async
**Queue projection:** v1

## What happened

- Nothing is broken; implementation commit `189fd7e` is green and local, with one task
  admission boundary still preceding publication.
- Verdict-token mapping now builds line starts once and advances one monotone cursor over
  ordered matches. It no longer rescans the growing semantic prefix per verdict.
- A duplicate revision still invalidates the receipt before its first valid verdict. Once
  a verdict exists, an immediate revision field terminates the receipt, preserves that
  evidence, and leaves later verdict-shaped text actionable.
- A deterministic 16,000-verdict regression rejects any return to `count` or `rfind`
  prefix scans. Actual one-run observations improved from 1.090s to 0.657s at 4,000
  verdicts and from 2.975s to 1.357s at 8,000.
- Focused, owning, full, staged, exact-range core-scope, exact-range reconciler, diff, and
  finite-model checks passed.

## How it works now

The receipt parser already returns verdict matches in line order. Neutralization computes
each semantic line's start offset once, then advances through those offsets as match token
positions increase. The cost is O(n + k) for document length n and k verdicts. The first
valid verdict also marks the end of the revision prologue: a later revision is ordinary
terminating history, not a reason to erase earlier evidence.

## Decisions made for you

- No new authority was assumed. The repair follows the already authorized closed receipt
  boundary and makes its writer-facing wording explicit in the canonical verification
  template. The rationale and compatibility cases are in the
  [task design](../../../tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/design.md).

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

- A nested guard-string helper made the repository's static test discovery intentionally
  fall back to whole-file execution, so the first full lane stopped in the sharding
  meta-tests. A configured mock provides the same deterministic `count`/`rfind` trap while
  remaining statically discoverable.
- The ephemeral classification view normalizes CRLF to LF by established design. The
  regression therefore checks logical line count, not preservation of source line-ending
  bytes; changing repository source was never in this repair's scope.

## Next steps

- [After the GitHub issue is filed, keep it synchronized with the canonical task and close it only when the task's implementation is published or deliberately withdrawn.](../../../message-queue/needs-agent/requests/non-blocking-track-github-review-verdict-action-classification.md)
- [Triage GitHub issue #80 against its canonical task and retain this source binding until trusted provider evidence proves the issue closed.](../../../message-queue/needs-agent/requests/non-blocking-triage-github-issue-80-review-verdict-action-classification.md)

## Deep links

- Task folder: [implementation task](../../../tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/) · Worklog: [session record](../../../tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/worklog.md) · Verification: [panel and real outputs](../../../tasks/1_in-progress/2026-08-04-stop-review-verdicts-from-looking-like-human-asks/verification.md)
- Commits: `9e9dfa2..189fd7e`
