# Handover — admit a candidate's whole task scope

**Session:** 2026-08-01 14:10–15:40 PDT, Claude
**Task:** 2026-08-01-admit-a-candidates-whole-task-scope
**Mode:** async
**Queue projection:** v1

## What happened

- Confirmed that two gates required opposite things of the same commit, by reproducing both
  halves from real repository state before changing anything. The reconciler refuses a commit
  that files a queue item bound to another task without editing that task's record; the
  projection gate refused the candidate that contains the edit, with exit 2 rather than a
  finding. Both transcripts are in the task's verification record.
- Classified all six blocked pull requests. Five have a plural scope the lifecycle itself
  prescribes — a reciprocity backlink, a task checking off criteria it shipped for another
  task, a parent claimed with its child, follow-up tasks a task filed, and one whose entire
  product is edits to other tasks' records. One, pull request 46, is a branch problem.
- Made task scope a set. The gate now binds every task the trusted base/candidate range
  carries, requires a task-named branch to be among them, and requires the projection to
  cover the union of the scope's live queue actions.
- Repaired the merge boundary. A boundary now skips an unanswered action the range itself
  filed; previously no `transition:` action could be introduced through any merged candidate,
  because the reciprocal task link the reconciler requires put that task into scope.
- Replayed all six pull requests against the repaired gate: three pass, two report a finding
  about their own description, one is still refused for naming a task that was never filed.

## How it works now

`inferred_changed_task_ids` returns every task a candidate carries instead of raising on the
second one, and `projection_findings` takes a `task_scope` that may be one id or a set, with
`required_paths` the union over it. A branch named `task/<id>` still fails closed when the
candidate carries no evidence of `<id>` — that is what still refuses pull request 46.
`check_active_queue_boundaries` skips an action whose identity is absent at the range base
*and* which carries no committed human response; an answered action is the boundary's receipt
and is checked exactly as before. Both rules are stated in `automation/AGENTS.md`, which is
back at exactly its 60-line budget, and in `handbook/git-workflow.md`.

## Decisions made for you

- Scope became a union rather than the branch's declared task alone, because binding only the
  branch's task would let a live human ask hide behind a branch name — pull request 42 carries
  a child task the parent's branch does not name. The alternatives and their consequences are
  in the task's `design.md`, "Options considered".
- The merge boundary keeps `review_successor_problem`'s byte-for-byte timing inheritance. That
  rule is right: relaxing it would let a `changes-requested` answer be replaced by a successor
  that quietly moves its own boundary. The reading of the boundary was wrong, not the rule.

## Needs your attention

- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/future-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why-you-might-care: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. || If-you-do-nothing: The three reviews stay live and unanswered, their three tasks stay in review forever, and the queue keeps carrying three asks that no repository action can close.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why-you-might-care: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. || If-you-do-nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

The first version of the boundary repair skipped **every** action the range filed, on the
argument that filing is not crossing. It broke a pre-existing test —
`test_git_range_approval_satisfies_merge_only_for_queue_only_tail` — and that test was right:
an approved review filed inside the range is the boundary's receipt, and whether the approval
still covers the candidate is precisely what the boundary validates. Do not widen the skip
back to all actions. The narrowing to *unanswered* actions is now asserted by its own test.

Binding only the branch's declared task was also considered and rejected. It is smaller and
mirrors what the reconciler already does for `--branch task/<id>`, but it lets a live human
ask hide: a branch named for a parent task can carry a child task whose asks are never
projected, which is exactly the shape of pull request 42.

## Next steps

- [File the missing task record for the branch named task/2026-07-31-redo-stranded-review-disposition (or rename that branch), and rewrite the "What to review" section of pull requests 41 and 45 to project every live human queue action their scope now binds.](../../../message-queue/needs-agent/requests/non-blocking-repair-three-branches-the-repaired-scope-gate-still-refuses.md)

## Deep links

- Task folder: `tasks/3_in-review/2026-08-01-admit-a-candidates-whole-task-scope/` · Worklog: `tasks/3_in-review/2026-08-01-admit-a-candidates-whole-task-scope/worklog.md` · Verification: `tasks/3_in-review/2026-08-01-admit-a-candidates-whole-task-scope/verification.md`
- Commits: `3178734..HEAD` on the task/2026-08-01-admit-a-candidates-whole-task-scope branch,
  which is based directly on the merge of pull request 43 into `main`
