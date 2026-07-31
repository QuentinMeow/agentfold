# Handover — collapse restated contract rules

**Session:** 2026-07-31 09:30–11:10 PDT, claude
**Task:** 2026-07-31-collapse-restated-contract-rules (parent) and 2026-07-25-single-source-queue-prefix-rule (child)
**Mode:** async
**Queue projection:** v1

One screen max, plain language, for a teammate who was away. Depth goes in the task
folder; this file links to it.

## What happened

- Broke a literal precedence loop. Root `AGENTS.md` said the closest `AGENTS.md` wins;
  `handbook/AGENTS.md` said root wins over anything in `handbook/`. For any file under
  `handbook/` those two rules cited each other forever. The inverted clause is deleted and
  both files now point at `handbook/principles/folder-as-a-service.md`, which terminates.
- Collapsed the queue delivery-prefix rule from thirteen live contracts to one. The five
  queue templates had already drifted: line 4 said "a named date, event, or transition"
  while the `Blocks at` line in the same file said UTC. Four further sites were surveyed
  and deliberately kept — they carry meaning the owner does not.
- Stopped six contracts describing mechanisms that do not run: auto-filed retries,
  configurable guard modes, a third branch lane, a deleted design sketch, and an
  unqualified link check. Each is now conditional or gone; none was replaced by a new
  mechanism.
- Repaired two broken ADR chains additively. `templates/memory/adr.md` gained
  `**Amends:**`/`**Amended-by:**`, `memory/AGENTS.md` says when to use them, and
  `generated_index()` marks an amended ADR. No decided ADR's prose was touched.

## How it works now

Precedence is stated once and the chain terminates in a principle. The three prefix
definitions exist only in `message-queue/AGENTS.md`; the thirteen files that used to copy
them each link there at the exact point the copy sat. `memory/index.md` now prints
`**[amended]**` on the two ADRs whose clauses were overturned, so a booting agent no longer
reads "commit the generated artifact" or "assurance profiles" as live. The reconciler
reports zero blocking findings and the full test suite passes.

## Decisions made for you

- Adding `Superseded-by:` / `Amends:` to a decided ADR is **not** a rewrite. Reasoning in
  `tasks/1_in-progress/2026-07-31-collapse-restated-contract-rules/design.md`, "Chosen":
  `templates/memory/adr.md` already declares those lineage fields the only permitted edits,
  because they record what happened *to* a decision rather than changing it.
- An amended ADR keeps `Status: decided`. Marking it `superseded` would retire six clauses
  that still bind.
- Both tasks share one branch, because the same edits close both. Noted in each worklog.

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

- Deleting root's precedence sentence instead of the handbook's. It would leave `tasks/`,
  `memory/`, `automation/`, and `services/` with no precedence rule at all — the loop only
  ever affected `handbook/`.
- Reclassifying the successor of `2026-07-23-queue-resolution-preserves-review-intent.md`
  from `Supersedes:` to `Amends:`. Substantively correct — its own prose keeps most of the
  old decision in force — but it would edit a recorded claim, which the lineage carve-out
  does not permit. The over-claim is documented in `design.md` instead of silently fixed.
- Editing `handbook/principles/eventual-consistency.md` directly. Principles are
  near-immutable; that one is queued as a decision.

## Next steps

None.

## Deep links

- Task folder: `tasks/1_in-progress/2026-07-31-collapse-restated-contract-rules/` · Worklog: `tasks/1_in-progress/2026-07-31-collapse-restated-contract-rules/worklog.md` · Verification: `tasks/1_in-progress/2026-07-31-collapse-restated-contract-rules/verification.md`
- Child task: `tasks/1_in-progress/2026-07-25-single-source-queue-prefix-rule/`
- Commits: `ed3a9ee..HEAD` on branch task/2026-07-31-collapse-restated-contract-rules
