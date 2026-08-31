# Handover — land the queue machine-record fold

**Session:** 2026-08-18 03:20–04:40 PDT, claude
**Task:** 2026-08-18-fold-the-queue-machine-record
**Mode:** async
**Queue projection:** v1

## What happened

- **The branch can land now.** Its first commit created its task directly in
  `1_in-progress`, which the landing gate refuses. It is now two commits — a `0_backlog`
  filing carrying the pickup request every unclaimed task owes, and a claim that resolves
  it — and the rest of the branch was replayed on top through the real commit gate.
  `--check --range fc8c0af...HEAD` is 0 blocking. Nothing was pushed.
- **The word budget goes back to 800, reversing a call made on this branch.** A held-out
  authoring run scored the same written questions at 0.750 under an 800-word ceiling and
  0.375 under 700; well-written questions naturally run about 725 words. The earlier
  measurement — that authors expand into a raised ceiling — was real and is kept beside it.
- **The real defect was that nobody could see the count.** `reconcile.py --word-count`
  now prints "N of 800" for any file, committed or not, so the one hard limit of the
  question format is checkable before you are refused rather than only afterwards.
- **Three things filed, two of them yours.** What to do about the ten older question
  files, and what to do about five sentences the checks read only half of. Plus one job
  for the next agent: decided decision records have no tamper check at all.
- **Two decision records written**, including one that retires two false statements
  underneath a decision from July without reversing the decision itself.

## How it works now

A question filed from today's templates puts its bookkeeping below the line you answer on,
inside one line you can tap open; four checks refuse the ways that shape can silently lose
a field. Not one of the fifteen questions already waiting for you is folded, and none can
be — folding one would change what the repository thinks the question is, and the rule
against rewriting a live question refuses that. So the fold has been tested against
fixtures and never once used in anger: the first real use is the next question anyone
files. The two questions this session filed carry it, but an agent wrote them.

## Decisions made for you

- The fold and the checks that hold it —
  `memory/decisions/2026-08-18-the-machine-record-is-folded-and-checked-by-position.md`.
  Undoing it is reverting three template files; no live item was touched.
- Bold-key metadata stays, but two reasons given for it in July are false —
  `memory/decisions/2026-08-18-bold-key-metadata-stays-on-corrected-grounds.md`. The July
  record stays decided and gained only a back-link. Undoing it costs a third record.
- The word budget is 800, not 700 — recorded on the constant in
  `automation/reconcile/reconcile.py` with both measurements. Undoing it is one number and
  a template line, and it would start refusing well-written questions again.
- The branch's history was rewritten to make it landable. The pre-rewrite commits are kept
  locally on `backup/pre-ceremony-a2ab98d`; undoing the rewrite is `git reset --hard` to
  that branch, and it puts the ship blocker back.

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

- **A one-line change to how file identity is computed** (ignoring blank lines) was
  investigated as a cheaper way to let the ten older questions be reformatted. It works and
  it buys those ten files nothing, because their problem is where their lines sit. Not
  recommended, and the reason is written into the question itself.
- **Reverting the word budget to 700 on the training-set length ratchet.** That number was
  real and measured the wrong thing. Do not revert it again on length evidence alone.
- **Making the missing-source-link warning apply to every question.** Two of the questions
  already waiting for you have no clickable source link, and adding one would change what
  the repository thinks the question is — so the warning fires only on a question that is
  not yet committed, where fixing it is still legal.

## Next steps

- [Add a check that refuses an edit to a decided record under `memory/decisions/` other than the lineage fields and `Review-by` bump `memory/AGENTS.md` allows, computed over raw bytes rather than a subtractive parse view.](../../../message-queue/needs-agent/requests/non-blocking-freeze-decided-records-against-invisible-appends.md)

## Deep links

- Task folder: [tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record](../../../tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record) · Worklog: [worklog.md](../../../tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record/worklog.md) · Verification: [verification.md](../../../tasks/1_in-progress/2026-08-18-fold-the-queue-machine-record/verification.md)
- Commits: `fc8c0af..HEAD` on `task/2026-08-18-fold-the-queue-machine-record` (10 commits, nothing pushed)
