# Handover — correct the ship-gate blockers

**Session:** 2026-08-18 04:45–05:30 PDT, claude
**Task:** 2026-08-18-fold-the-queue-machine-record
**Mode:** async
**Queue projection:** v1

## What happened

- **A false claim in the previous handover is corrected here, because that file cannot
  be edited.** It says the branch is "(10 commits, nothing pushed)". It was 12 commits
  when that line was written. `handover-queue-projection` freezes a committed handover,
  and its own repair instruction is to record the correction in a new one, which is this.
  Count it rather than trust any number: `git rev-list --count fc8c0af..HEAD`.
- **The word budget's justification no longer cites evidence nobody can reach.** The
  comment above `HUMAN_ATTENTION_WORD_BUDGET` rested 800 on `pass^2` figures and a
  McNemar p-value produced by a harness that is not in this repository. It now carries
  the reasoning and names the task record that holds the figures.
- **`roadmap/current-state.md` described the pre-branch tree.** It said fifteen live
  human items, none folded. Measured at HEAD: 17 live, 10 with bookkeeping above the
  answer line and 7 below, and the 2 this task filed are folded.
- **One ship blocker is not fixed and needs your decision** — see below.

## How it works now

Nothing about the fold, the checks, or the templates changed in this session; only
records and one code comment did. The state that mattered was that
`non-blocking-choose-what-happens-to-the-ten-older-question-files.md` opened with "Ten of
the fifteen questions waiting for you". That was true before this branch filed two more
items and was false by then — at HEAD there are 17 live items, 15 of them waiting, 7
carrying their bookkeeping under the answer line and 10 above. The same file called its
excerpt "the worst file"; measured, that excerpt ranked fourth of ten.

Neither could be edited in place. A live queue item's title and context are its action
identity, and `queue-resolution` refuses any edit that changes them; amending the filing
commit fails too, because at hook time HEAD still holds the old item and the check sees a
live rewrite. The repair was to rebuild the commit that files it from its parent, so the
item is born correct and no prior version exists to rewrite — legal only because this
branch is unpushed. The handovers that project it were rebuilt the same way, for the same
reason: a committed handover is immutable, so its projection had to be born correct too.

## Decisions made for you

- **The uncitable statistics were removed rather than imported.** The alternative was to
  land the eval harness in the repository. Undoing this is one comment.
- **The stale item was rewritten at its birth commit, not left as filed.** Rewriting it means rewriting the
  commit that created it, which is legal only because the branch is unpushed. That is a
  history rewrite of your branch, so it is yours to authorize, not mine to take.

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

- **Editing the live queue item in place.** Committed through the real hook; refused with
  `queue-resolution: live queue action was rewritten: action identity changed while the
  queue item remained live`. The prior gate report called this edit legal. It is not.
- **Editing the previous handover in place.** Refused with `handover-queue-projection`,
  twice over. Corrections go forward into a new handover; that is this file.
- **Deleting and re-filing the item.** `queue_deletion_problem` requires the item to be
  `folding` with a concrete human response before it may be deleted, and an agent may
  never author one.
- **Appending the correction to the item as a `Re-asked:` line.** Legal, but `Re-asked`
  is a machine field, so it sits inside the "nothing here needs you" fold — the one place
  a correction the owner must see should never go.

## Next steps

- [Add a check that refuses an edit to a decided record under `memory/decisions/` other than the lineage fields and `Review-by` bump `memory/AGENTS.md` allows, computed over raw bytes rather than a subtractive parse view.](../../../message-queue/needs-agent/requests/non-blocking-freeze-decided-records-against-invisible-appends.md)

## Deep links

- Task folder: [tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record](../../../tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record) · Worklog: [worklog.md](../../../tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record/worklog.md) · Verification: [verification.md](../../../tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record/verification.md)
- Commits: `fc8c0af..HEAD` on `task/2026-08-18-fold-the-queue-machine-record`, nothing pushed; count them with `git rev-list --count fc8c0af..HEAD`
