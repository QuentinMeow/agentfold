# Handover — wrap up the crashed session

**Session:** 2026-08-02 16:30–17:50 PDT, local time, claude
**Task:** none — recovery and publication of six task branches left in flight
**Mode:** async
**Queue projection:** v1

## What happened

- The owner's machine crashed overnight. Six task branches were in flight; nothing was
  lost. Two carried uncommitted work in their worktrees, one was complete but had no pull
  request, and three were already published and needed nothing.
- **Committed and published the two uncommitted branches**, each with the design and
  verification records it was missing. On
  `task/2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack` the uncommitted change
  turned out to close a real fail-open: `[` reports status 2, not 1, on an operand that
  overflows `intmax_t`, so a resolve bound above 2^63-1 skipped both the range guard and
  every loop iteration, and the step exited 0 publishing an empty revision. That is now
  recorded as run output in both directions — pre-repair exiting 0 with `revision=`, and
  repaired exiting 1 with `no candidate revision was bound`.
- On `task/2026-08-02-advise-on-explanation-shape` the uncommitted change closes an
  imitation hole an independent review probe walked through: a new agent queue item that
  copied one legacy field line from the single live legacy request switched the whole
  readability rule off for itself. The carve-out now needs the legacy field **and** a
  `Filed` date before the rule landed.
- **Opened pull request #70** for `task/2026-07-25-complete-stage-0-verification-transcripts`,
  which was complete and pushed with every acceptance criterion met when the machine died —
  only the pull request was missing.
- **The landing set was screened before any of it merged, and the screen earned its keep.**
  `automation/integrate.py`, the tool pull request 68 adds, pinned all seven legs, reported
  28 textually clean pairs, then replayed the whole set into a scratch worktree with the
  staged tests and the reconciler at every merge boundary. Legs 1 through 6 passed. Leg 7 —
  this handover — failed there while passing in isolation, because the sharper prose
  detector pull request 69 adds met a sentence in this file for the first time in the merge
  commit. That is precisely the failure class the screen exists for
  (`memory/lessons/automation/green-branches-can-merge-to-red.md`), caught before the trunk
  saw it. The sentence was reworded; no check was weakened.
- **Preserved eight stashes that were one `git gc` from gone.** They hold intermediate
  states of the shelved test-gate task that no archive tag contained. They are now
  `archive/2026-07-27-test-gate-stash-<0..7>-<slug>`, and every archive tag is pushed —
  before today only one of the six existing ones had been, so five existed on one laptop.

## How it works now

Six pull requests are open: #65 through #70. Three are fully green (#67, #69, #70). Three
show one red `reconcile-and-test` (#65, #66, #68) from a stale-base race that is not the
branches' fault — on the identical commit the `push` and `pull_request_target` events pass
and only the `pull_request` event fails, at the step that reads GitHub's lagging `base.sha`.
That race is already filed as its own backlog task. Every branch's own tests and reconciler
pass locally: 12/12 test files, `0 blocking finding(s)`.

## Decisions made for you

- The three branches showing red were **not** restacked onto current `main`. Restacking
  clears the stale-base failure but the previous session recorded that it then produces a
  different false positive, and it chose to stop chasing a green board. Undoing this is one
  rebase per branch; leaving it costs a red check that is explained in each branch's
  `verification.md`.
- The eight stashes were archived rather than turned into a pull request. The task they
  belong to was deliberately unstarted and re-filed, and its own record says to re-measure
  before implementing, so landing them would re-open a decision already taken. Undoing this
  means claiming the backlog task; the states are tagged and pushed either way.
- Nothing else. In particular no queue item was resolved, deleted, or reworded, and no
  human answer was interpreted.

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why this matters: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. — If you do nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why this matters: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. — If you do nothing: The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
- [Choose whether the nine older waiting questions are left as written, replaced with plainer versions, or replaced only where their wording is now stale.](../../../message-queue/needs-human/decisions/non-blocking-re-ask-the-older-questions-in-plainer-words.md) — Why this matters: Nine of the questions in your queue were written in a format that buries the choice under bookkeeping, and four of them still ask about a moment that has already passed. — If you do nothing: They stay exactly as written and stay answerable; only questions filed from now on use the readable shape.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md) — Why this matters: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. — If you do nothing: The merged design and its inspector stand, and its task completes without your judgment on record.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why this matters: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. — If you do nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md) — Why this matters: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. — If you do nothing: The merged boundary stands as the repository-wide test boundary, and its task completes without your judgment on record.
- [Say whether this is the standard every human-facing message is held to, or name what to change.](../../../message-queue/needs-human/reviews/non-blocking-review-the-explanation-standard.md) — Why this matters: Every report, pull request, and question you get from an agent from now on is written to this standard, so a wrong rule here compounds across every future message. — If you do nothing: The standard stands as written and agents follow it; nothing stops, and it can be changed later by editing one file.
- [Say whether this pull-request shape works for you, or name the section to move, add, or drop.](../../../message-queue/needs-human/reviews/non-blocking-review-the-pull-request-shape.md) — Why this matters: This is the shape of every pull request you are asked to look at from now on, and it decides what you see before you have to click anything. — If you do nothing: The shape stands and every later pull request uses it; nothing stops, and changing it later means editing two files and one test.

## Dead ends

- A handover that fails the merge gate cannot be repaired by a later commit on the same
  branch, and two attempts were spent learning it. Editing it in place is refused, because
  a committed handover is immutable. Deleting it and writing a corrected one at a fresh
  conversation path is refused too — not by the immutability rule, which explicitly allows
  the deletion, but because the merge-boundary check reads the whole `--range`, so the
  original bytes are still introduced somewhere in it and still count. Staging the two
  paths as one change is a third failure: Git reports a near-identical move as a rename.
  What works is rewriting the branch so the bad bytes were never committed, which is what
  this branch is — one commit, carrying only the corrected record.
- Restacking the three red branches onto current `main` was considered and rejected. It
  does clear the stale-base failure, but the previous session already ran that experiment
  and recorded what follows: the force push then reports
  `[queue-resolution] ... deleted unresolved queue item: divergent update discarded a live
  old-tip action`, because another agent's properly evidenced deletion between the two bases
  reads as this branch discarding a live action. Trading one explained red check for a
  different unexplained one is not progress.
- The pull-request body for #70 was rejected by the boundary gate on its first run:
  `commands that were actually run and the real output they printed` scans as a bare
  imperative, because `run` is a work verb sitting in a coordinate slot. This is the third
  sighting of that false positive. The sentence was reworded and the detector left alone —
  the standing repair is task
  `2026-08-02-stop-a-wrapped-line-from-reading-as-a-command`, not a waiver.
- Deleting `future-blocking-review-detector-failure-state.md` was attempted and the
  reconciler correctly refused it. The item sits at status `folding` with a decided ADR
  behind it, which reads like a fold that was never finished — it is not. An item filed as
  `future-blocking` stays live until the task it gates crosses the boundary named in its
  `Blocks at` field, and `2026-07-22-universal-guard-mode-configuration` is still in
  `0_backlog`, so the item is doing exactly its job. The deletion was reverted, and the
  correct reading is written here so the next session does not re-attempt it: an answered
  `folding` item is not evidence of a stranded fold.
- The first attempt at tagging the stashes mapped every tag to the wrong stash: `zsh`
  arrays are 1-indexed, so a `for i in 0..7` loop over a literal array shifts every name by
  one and silently drops the last. The eight bad tags were deleted before anything was
  pushed, and the tags were rebuilt from `git rev-parse stash@{N}` per stash with the SHA
  printed beside each name.

## Next steps

- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-stale-base-from-failing-the-reconciler-check.md)
- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-wrapped-line-from-reading-as-a-command.md)

## Deep links

- Task folders: `tasks/1_in-progress/2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack/` · `tasks/1_in-progress/2026-08-02-advise-on-explanation-shape/` · `tasks/1_in-progress/2026-07-25-complete-stage-0-verification-transcripts/`
- Pull requests: #65, #66, #67, #68, #69, #70
- Commits: `4db4080` (merge-ref bound repair), `00f3a89` (imitation hole), `c8fc9f1` (stage-0 publication record), and this branch
- Archived stash states: `archive/2026-07-27-test-gate-stash-0-…` through `-7-…`, all pushed to `origin`
