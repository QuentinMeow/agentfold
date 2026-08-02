# Handover — stop human answers from gating Git edges

**Session:** 2026-08-01 10:30–16:10 PDT, claude
**Task:** 2026-08-01-stop-human-answers-from-gating-git-edges
**Mode:** async
**Queue projection:** v1

## What happened

- The repository could not merge itself. `reconcile --check` was clean on `main` while
  `reconcile --check --at-transition merge` reported four blocking findings, three of
  them questions nobody had answered — and two of those could never be answered in a way
  that helped, because their cleanup required a merge that had already happened.
- A `needs-human/` item may now withhold only two things: the start of a task still in
  `0_backlog`, and one act with no undo. Merging, moving a task through review, and
  recording it done are revertible, so none of them waits on an answer any more. The
  reconciler refuses the old shapes with a message that explains the rule.
- Every question to you now carries an `Answer by:` date. A lapsed date makes an agent
  re-surface the question and set a new one; it never answers it, and it never blocks a
  commit or a merge.
- Four live questions were migrated onto the one commit that turns the new rule on.
  Nothing you wrote changed: all ten committed response blocks hash identically before
  and after, including the one that already carries your answer. The two stranded reviews
  are still blank and are now answerable whenever you get to them.
- Two follow-up tasks and one known issue were filed for the parts this did not build.

## How it works now

A question is filed, the change merges, and the answer arrives whenever it arrives. A task
reaches `4_done` when the *agent* owes nothing — real `verification.md` output and no live
agent action — and any question you have not answered stays listed on it and outlives it.
The one gate you still hold is `transition:start` on a task nobody has begun, which is what
stops work from being piled on top of a judgment you have not given.

None of this is actually enforced yet. The repository's rule set is switched off with no
required check, so the merge button still works regardless of what any check says. That is
the first item below.

## Decisions made for you

- Nothing a human owes holds a Git edge —
  `memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md`. It amends three
  earlier records rather than replacing them; each keeps the clauses that still bind.
- The rule that generalises it, with the failure that taught it —
  `memory/lessons/message-queue/a-boundary-must-be-closable-at-any-later-time.md`.
- Three smaller calls, each recorded in the task's `design.md` and its commit: keep the
  three timing prefixes instead of renaming them, leave `needs-agent/` timing untouched,
  and refuse to let a lapsed deadline decide anything by itself.

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why this matters: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. — If you do nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why this matters: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. — If you do nothing: The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
- [Decide whether the repository should refuse to merge a pull request whose `reconcile-and-test` check has not passed, and say which of the options below you want.](../../../message-queue/needs-human/decisions/non-blocking-turn-on-the-merge-gate-this-repository-already-runs.md) — Why this matters: Every safety rule in this repository is currently a suggestion — the checks run, they can go red, and the merge button works anyway. — If you do nothing: The checks keep running and keep being ignorable, and a branch that goes red can still land on `main` exactly as one did on 2026-08-01.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md) — Why this matters: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. — If you do nothing: The merged design and its inspector stand, and its task completes without your judgment on record.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why this matters: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. — If you do nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md) — Why this matters: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. — If you do nothing: The merged boundary stands as the repository-wide test boundary, and its task completes without your judgment on record.

## Dead ends

- Renaming the three timing prefixes to carry the new meaning was considered and dropped:
  renaming one live item touches up to eight other files, including recorded command
  output that should not be edited at all. The reconciler's refusal message teaches the
  rule instead.
- A fourth timing class for "answer whenever" was dropped for the same reason — the
  weakest existing class already is that class, and has been since July.
- Correcting a dangling `Depends on:` link on a live review turned out to be illegal: it
  is part of the item's frozen identity. Recorded in `memory/known-issues/` rather than
  forced.
- Getting the scoped merge check to zero was not attempted. The one remaining finding is
  an agent's own obligation, and clearing it would mean either breaking eleven live agent
  items or finishing an unrelated in-flight task.

## Next steps

- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-screen-a-landing-set-before-merging-it.md)
- [When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.](../../../message-queue/needs-agent/requests/non-blocking-pick-up-stop-the-merge-ref-recompute-from-failing-a-stack.md)

## Deep links

- Task folder: `tasks/3_in-review/2026-08-01-stop-human-answers-from-gating-git-edges/` ·
  Worklog: `tasks/3_in-review/2026-08-01-stop-human-answers-from-gating-git-edges/worklog.md` ·
  Verification: `tasks/3_in-review/2026-08-01-stop-human-answers-from-gating-git-edges/verification.md`
- Commits: `0e63bbe..HEAD` on `task/2026-08-01-stop-human-answers-from-gating-git-edges`
