# Handover — common human-agent Git cycles

**Session:** 2026-08-31 15:05–17:19 PDT, codex
**Task:** 2026-08-03-plan-multi-worktree-safety-remediation
**Mode:** async
**Queue projection:** v1

## What happened

- Recovered the missing integration worktree and remote task branch from preserved Git
  objects, merged current `main`, and opened draft pull request #94.
- Published a source-linked comparison of Vibe, Beads/Gas Town, Claude/Codex messaging, and
  mature visibility/runtime alternatives; none earned immediate canonical-core authority.
- Defined ten human/agent development cycles, separate durable/live/integration identities,
  positive writer fencing, and a replay-resistant candidate-evidence protocol.
- Bound the final design candidate to a clean-clone run: reconciler 0 blockers, repository
  tests 16/16, and five fresh-context design reviewers accepted it.

## How it works now

The pull request contains design and research, not the deferred behavior implementation.
Repository records remain authoritative for durable intent and evidence; runtime adapters may
own expiring observations and writer fences; external products remain replaceable projections.
The first planned implementation task cannot start until the task-claim publication decision
is folded.

## Decisions made for you

- Kept AgentFold's core limited to vendor-neutral governance, evidence, recovery, and
  admission; product runtimes and dashboards remain adapters — [design](../../../tasks/1_in-progress/2026-08-03-plan-multi-worktree-safety-remediation/design.md#external-product-disposition).
- Treated self-evolving agents as isolated candidate generators, never evaluator or approval
  owners — [design](../../../tasks/1_in-progress/2026-08-03-plan-multi-worktree-safety-remediation/design.md#verification-ladder).

## Needs your attention

- [Choose whether to authorize sending the published recovery code and diffs to Claude for one read-only review, or accept the five native reviews without that additional check.](../../../message-queue/needs-human/decisions/blocking-authorize-the-external-recovery-review.md) — Why this matters: Sending repository code to another service adds a recipient, and that disclosure cannot be undone by deleting a local file. — If you do nothing: No code is sent to Claude; the two prepared PRs remain available with their native reviews and passing checks.
- [Choose whether atomic task claims keep a narrow direct-main exception or must use a new pull-request transaction.](../../../message-queue/needs-human/decisions/future-blocking-choose-whether-task-claims-must-use-pull-requests.md) — Why this matters: Parallel agents need one immediate winner, while you asked for every piece of progress to remain reviewable as a pull request. — If you do nothing: Parent design and research continue, but the first planned implementation task cannot start; the current task remains safely claimed under the old rule.
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

- Do not promote Vibe to core: its commercial remote task plane shut down and no successor
  governance was verified.
- Do not promote Beads or Gas Town from repository reputation alone: the required failure,
  upgrade, restore, rebuild, and dual-write trials have not run.
- A Git archive reinitialized as a one-commit repository is not the cold-clone check here;
  it discards historical commits that live review records intentionally reference.
- The cross-provider Claude refuter was not retried after the publication boundary rejected
  it; no candidate bytes were sent.

## Next steps

- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-restack-from-being-blamed-for-another-branchs-deletion.md)

## Deep links

- Task folder: [multi-worktree remediation](../../../tasks/1_in-progress/2026-08-03-plan-multi-worktree-safety-remediation/) · Worklog: [session log](../../../tasks/1_in-progress/2026-08-03-plan-multi-worktree-safety-remediation/worklog.md) · Verification: [real checks](../../../tasks/1_in-progress/2026-08-03-plan-multi-worktree-safety-remediation/verification.md)
- Commits: `8e24d09`, `823f9f6`, `9e78d85`; the handover and final receipts are in the closing records commit.
