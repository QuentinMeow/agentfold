# Handover — clear branches and stop human answers gating merges

**Session:** 2026-08-01 into 2026-08-02, PDT local time, claude
**Task:** none — exploratory repository coordination
**Mode:** async
**Queue projection:** v1

## What happened

- What started as "clean up merged local branches" found 75 unpushed commits, 12 worktree
  scaffolding branches, 9 backup refs, 8 stashes, and 1,059 unreachable commits. Nineteen
  pull requests merged, taking `main` from `6cd2de9` to `4dcff4e`; there are now zero open
  pull requests, one local branch, one remote branch, and one worktree.
  Every retired branch's unique content survives under one of six archive tags — including
  one orphaned commit, `5c4e093`, that held two required session handovers reachable from
  nothing and is now `archive/2026-07-24-consolidate-unmerged-work`.
- An answer the owner committed on 2026-07-26 had never reached `main`. It lived only on an
  unpushed branch 77 commits behind, so the repository kept re-asking a question it already
  had the answer to. That answer is recovered.
- A real, production-reachable security hole is closed: a Git replacement ref could feed
  forged Git objects to the pre-commit gate. Adversarial review then found that the
  core-admission gate could be switched off entirely and the test selector made to run no
  tests at all. Both of those are closed too, with six exploit regressions and a
  source-level guard.
- Human-action files were redesigned after the owner rejected the format — a design panel of
  three, then a judge, then implementation. A final adversarial pass proved the live-item
  migration could rewrite the very question a human is answering while all seventeen frozen
  fields stayed byte-identical, so that migration was cut and `queue_mutation_problem` was
  left untouched.
- The headline change: human answers no longer gate Git edges. Three separate deadlocks were
  each one rule demanding what another rule forbids — a queue item needed a task backlink
  while the projection gate refused any candidate touching two task folders; a
  future-blocking merge-transition item could only be filed with that backlink, so it could
  never be introduced through any merged candidate at all; and an immutable handover was
  being judged by a grammar written after it. In every case the written contract was right
  and the code had drifted away from it.

## How it works now

The repository has one working branch and a clean remote, and its history is fully
reachable: nothing worth keeping depends on an unreferenced commit any more. A pending human
answer no longer blocks a merge, so branches carrying live queue items can land while their
questions stay open and answerable. The pre-commit gate now rejects forged objects, cannot be
switched off, and cannot be talked into running an empty test set.

## Decisions made for you

None were taken on the owner's behalf. Two were put to him during the session and he
answered both; both answers are folded on this branch — the merge gate stays advisory while
the repository is immature
([decision record](../../../memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md)),
and approval classification stays attested
([known issue](../../../memory/known-issues/2026-07-31-review-outcome-classification-is-attested.md)).

## Needs your attention

- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why this matters: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. — If you do nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why this matters: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. — If you do nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why this matters: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. — If you do nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [choose Option A or Option B, or state another choice](../../../message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md) — Why this matters: A principle is the most-quoted kind of file here, and this one currently promises an automatic repair loop that no hook, CI job, or script actually starts. — If you do nothing: Nothing stops. The principle keeps describing the loop in the present tense until either you answer this or the filed retry-automation task ships and makes the sentence true.
- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/non-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why this matters: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. — If you do nothing: The reviews stay live and answerable, their tasks complete without them, and the crossing stays visible in Git history.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-layered-development-workspace.md) — Why this matters: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. — If you do nothing: The merged design and its inspector stand, and its task completes without your judgment on record.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why this matters: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. — If you do nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/non-blocking-review-test-runner-git-environment-isolation.md) — Why this matters: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. — If you do nothing: The merged boundary stands as the repository-wide test boundary, and its task completes without your judgment on record.

## Dead ends

- `--delete-branch` on a stacked pull request closes the child pull request rather than
  retargeting it, and GitHub emits no `base_ref_changed` event. It killed two pull requests
  and cost about 41 minutes.
- GitHub pins a pull request's `baseRefOid` at creation and never refreshes it, so a
  long-lived pull request computes every gate against a stale base. Polling made no
  difference; closing and reopening the pull request was the only remedy that worked.
- Merging `main` *into* a non-`task/` branch makes the staged core-scope check read the
  imported core changes as unauthorised work. Merging with `main` as first parent avoided it.
- Turning on GitHub's native merge queue was rejected: it would have merged with zero
  verification, because `harness.yml` carries no `merge_group` trigger.
- Long descriptive pull-request bodies repeatedly tripped the action-projection check with
  "visible action-like question or directive exists outside the declared action section".
  Short factual bodies passed.
- The `git` on PATH is 2.23.0 and lacks `merge-tree --write-tree`; the copy at
  `/usr/bin/git` is 2.50.1.

## Next steps

None.

## Deep links

- Task folder: none · Worklog: none · Verification: this handover
- Commits: `280d106`, `36f97ca`, `5708802` on
  `harness/2026-08-02-fold-the-owners-gate-and-approval-answers`, plus this handover commit.
  The session's merged work spans `6cd2de9..4dcff4e` on `main`.
