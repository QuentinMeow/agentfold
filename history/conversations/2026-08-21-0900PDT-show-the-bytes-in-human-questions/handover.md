# Handover — show the bytes in human questions

**Session:** 2026-08-21 09:00–18:30 PDT, claude
**Task:** 2026-08-21-show-the-bytes-in-human-questions
**Mode:** async
**Queue projection:** v1

## What happened

- The owner rejected four live review items as unanswerable. Measured, they are 241–297
  words against an 800-word budget — empty, not crowded — while showing no text from the
  710-line design they ask for a verdict on.
- Found the mechanical cause: `check_explanation_shape()` skipped every item not written
  under the current template. That skip covered 10 of 70 items, and those ten were exactly
  the ten the owner rejected.
- Five research threads read roughly 45 primary sources. One reversed the obvious repair:
  adding reasoning prose is measured to raise a reader's acceptance regardless of whether
  the recommendation is correct. The fix shows verified bytes instead of arguing.
- Two designs were commissioned from opposing premises and judged adversarially; each
  contained a load-bearing factual error the other did not, and the judge rejected 10 of
  34 proposed mechanisms.
- Landed and published as #89, stacked on #88. Five checks pass, MERGEABLE.

## How it works now

A question that turns on a repository file must quote it, and the quoted words are
verified against the bytes under the heading anchor its attribution links. Paraphrasing,
deleting the anchor, misspelling it, quoting the wrong section of the right file, and
leaving an unclickable path above the answer line each report. The reader can also answer
that the page did not give them enough to decide, which settles nothing and obliges a
fresh question. Every finding is advisory and refuses no commit.

## Decisions made for you

- Anchors are resolved by the new check rather than by removing `"../"` from
  `LINK_SKIP_PREFIXES`. Undoing that means accepting 816 newly evaluated links, none
  carrying a fragment, nearly all in immutable history
  (`tasks/1_in-progress/2026-08-21-show-the-bytes-in-human-questions/design.md`).
- No reader-competence field was built, so that a failure of the byte-showing rule stays
  attributable to one cause rather than two (same file, "Chosen").
- A live unanswered review bound to the old `SKILL.md` was retracted and republished
  against the new bytes rather than silently rebound; the question and answer line are
  unchanged.

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [Choose which of three shapes the rule for externally changed instruction files takes: holding the adopting work, holding nothing, or holding the merge itself.](../../../message-queue/needs-human/decisions/non-blocking-choose-the-gate-for-externally-changed-instruction-files.md) — Why this matters: Anyone who can open a pull request here can edit the files that direct every agent, and the rule meant to catch that promises a hold this repository can no longer apply. — If you do nothing: Nothing stops. The rule keeps promising a hold no file can express, so an outside edit to an instruction file is reviewed only if the agent that happens to see it decides to ask.
- [Choose whether the ten older question files are rewritten to hide their bookkeeping, migrated one at a time with your sign-off, or left alone.](../../../message-queue/needs-human/decisions/non-blocking-choose-what-happens-to-the-ten-older-question-files.md) — Why this matters: Ten of the seventeen questions in your queue put a screen of paths and checksums above the ask, so on a phone the question starts below the fold. — If you do nothing: Nothing stops. Those ten keep the shape you saw, and every question written from today's template already hides its bookkeeping behind one line.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why this matters: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. — If you do nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Choose whether the five half-read sentences are left alone, repaired by teaching the reader to follow a wrapped line, or rewritten with your sign-off.](../../../message-queue/needs-human/decisions/non-blocking-dispose-five-half-read-values-in-two-frozen-questions.md) — Why this matters: Anything that later quotes one of those sentences to you — a summary, a notification — would show a sentence that stops mid-thought, and nobody would notice. — If you do nothing: Nothing stops. The two questions stay answerable as they are, and a warning about them prints on every run until you answer them.
- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why this matters: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. — If you do nothing: The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
- [Choose whether the nine older waiting questions are left as written, replaced with plainer versions, or replaced only where their wording is now stale.](../../../message-queue/needs-human/decisions/non-blocking-re-ask-the-older-questions-in-plainer-words.md) — Why this matters: Nine of the questions in your queue were written in a format that buries the choice under bookkeeping, and four of them still ask about a moment that has already passed. — If you do nothing: They stay exactly as written and stay answerable; only questions filed from now on use the readable shape.
- [Choose whether an agent corrects the stale numbers in two principle files now, leaves them alone, or gets a standing permission to correct facts of this kind without asking.](../../../message-queue/needs-human/decisions/non-blocking-stop-a-principle-from-copying-the-line-budget.md) — Why this matters: The nine principle files are the most-quoted documents here, and one of them tells agents a size limit smaller than the real one, so an agent will cut a contract that was never too long. — If you do nothing: Nothing stops. The two files keep quoting numbers that are no longer true, and every agent that reads them inherits the wrong ones.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md) — Why this matters: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. — If you do nothing: The merged design and its inspector stand, and its task completes without your judgment on record.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why this matters: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. — If you do nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md) — Why this matters: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. — If you do nothing: The merged boundary stands as the repository-wide test boundary, and its task completes without your judgment on record.
- [Say whether this is the standard every human-facing message is held to, or name what to change.](../../../message-queue/needs-human/reviews/non-blocking-review-the-explanation-standard.md) — Why this matters: Every report, pull request, and question you get from an agent from now on is written to this standard, so a wrong rule here compounds across every future message. — If you do nothing: The standard stands as written and agents follow it; nothing stops, and it can be changed later by editing one file.
- [Say whether this pull-request shape works for you, or name the section to move, add, or drop.](../../../message-queue/needs-human/reviews/non-blocking-review-the-pull-request-shape.md) — Why this matters: This is the shape of every pull request you are asked to look at from now on, and it decides what you see before you have to click anything. — If you do nothing: The shape stands and every later pull request uses it; nothing stops, and changing it later means editing two files and one test.

## Dead ends

- Scoring the weak-author test against the stock scenarios does not work: three of four
  name files this repository does not contain, so an author cannot quote them and the
  quote rule cannot be exercised. A grounded replacement failed differently — it
  duplicated a live queue item, which all three authors correctly detected and declined.
  The mechanism claim rests on five adversarial probes, which test it directly.
- Creating the task directly in `1_in-progress` is refused; tasks are born in
  `0_backlog` with a pickup request and claimed in a second commit.
- Rebinding a stale `Review revision` in place is refused. The only legal route is the
  `waiting` -> `awaiting-artifact` retraction, which requires `Review target: pending` and
  `Review revision: pending`, then a publication back to `waiting`.
- A bare verb opening a clause ("reproduce none of it") reads to
  `check_action_projection.py` as a directive aimed at the reader and fails the pull
  request. Past tense passes.

## Next steps

None.

## Deep links

- Task folder: [2026-08-21-show-the-bytes-in-human-questions](../../../tasks/1_in-progress/2026-08-21-show-the-bytes-in-human-questions) · Worklog: [worklog.md](../../../tasks/1_in-progress/2026-08-21-show-the-bytes-in-human-questions/worklog.md) · Verification: [verification.md](../../../tasks/1_in-progress/2026-08-21-show-the-bytes-in-human-questions/verification.md)
- Commits: `921d416..3b19259`
