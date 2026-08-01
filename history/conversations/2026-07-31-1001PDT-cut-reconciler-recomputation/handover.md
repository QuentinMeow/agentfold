# Handover — cut-reconciler-recomputation

**Session:** 2026-07-31 08:20–11:10 PDT, local time, claude
**Task:** 2026-07-31-cut-reconciler-recomputation
**Mode:** async
**Queue projection:** v1

## What happened

- The reconciler now answers repeated questions from caches instead of recomputing them:
  the pure Markdown text views and the task-record action-prose verdict are memoised on
  their exact input text, one exact index question is a dictionary lookup instead of a scan
  of the whole index, the governed edge walk asks Git for a revision's parents once instead
  of once per consuming check, an immutable handover's creation bytes come from the existing
  `cat-file --batch` reader instead of a `git show`, and the live queue path sets are derived
  once per candidate instead of twice per handover.
- `automation/reconcile/reconcile.py --check`, the command a human waits on at every commit,
  now takes half as long: 10.51s to 5.25s median on an interleaved baseline/current run.
  Larger scopes: 1.91x on a 22-commit range, 2.03x on a 72-commit range, 1.75x on the whole
  363-commit history.
- Nothing the reconciler decides changed. A differential harness ran the pre-change and
  post-change reconciler against one clean working tree and diffed exit code, findings, and
  stderr for `--check`, both ranges, and `--range root:<head>`; all four are byte-identical,
  including the 55 blocking findings the full-history range reports.
- The profiling audit that motivated this task was taken before the object-read caching layer
  landed. All four of its named hot spots still reproduce at the stack tip, but the largest
  single cost was not among them, and fixing that one dissolved most of the largest named one.
- The full test suite passes (11/11 files), and every commit went through the installed
  pre-commit hook.

## How it works now

Two kinds of cache were added, and they are scoped differently on purpose. The text views in
`automation/markdown_semantics.py` and `automation/check_action_projection.py` are pure
functions of their input string, so they use a bounded `lru_cache` that is valid for the whole
process regardless of which Git revision is bound. The live queue path sets depend on the
bound candidate, so they live beside the other candidate-scoped caches and
`git_revision_candidate` saves, clears, and restores them exactly like `_TASK_SNAPSHOT_CACHE` —
a rebound historical tree can never read the answer another tree produced.

## Decisions made for you

- Not caching `check_task_structure`'s findings per admitted revision, even though it was the
  single biggest named hot spot: it reads arbitrary repository paths through a review item's
  declared target and consults the bound revision itself, so no fingerprint is both sound and
  narrow enough to ever hit. See `Options considered` in the task's `design.md`.
- Not materialising the `queue_revision_edges` generator: its real cost was a Git process per
  commit per consumer, which the cached parent helper removes while the generator stays lazy
  and keeps streaming findings ahead of a mid-walk failure. Same file.

## Needs your attention

- [Choose option A, B, or C for all three stranded merge reviews, or state another disposition.](../../../message-queue/needs-human/decisions/future-blocking-dispose-merge-reviews-whose-boundary-already-passed.md) — Why-you-might-care: Three core changes are live on main today without the review each of them declared mandatory before merge, and no commit can now satisfy that gate. || If-you-do-nothing: The three reviews stay live and unanswered, their three tasks stay in review forever, and the queue keeps carrying three asks that no repository action can close.
- [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md) — Why-you-might-care: This changes every human and durable cross-session agent action surface in AgentFold. || If-you-do-nothing: The task may be reviewed and revised, but it does not merge.
- [Confirm that self-authored acknowledgements may record judgment but may never authorize a confirmed critical finding.](../../../message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md) — Why-you-might-care: Treating an agent-authored receipt as approval would let the producing agent waive its own security gate. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current authority split remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, review the layered workspace design and read-only inspector, then approve the exact Git range, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md) — Why-you-might-care: This design shapes how public, private, restricted, raw, and temporary workspace content may eventually compose without pretending Git convenience mechanisms are confidentiality boundaries. || If-you-do-nothing: This PR remains unmerged, and the deferred coordination tasks are not published.
- [Confirm the revised design makes guard configuration, derived assurance, manual evidence, coverage limits, and controlled-egress non-scope clear.](../../../message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md) — Why-you-might-care: The implementation must configure real guards and report only observed protection, rather than letting an agent select or claim an assurance label. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the approved conceptual direction remains recorded but the revised design is not accepted.
- [Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.](../../../message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md) — Why-you-might-care: Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs. || If-you-do-nothing: Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.
- [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md) — Why-you-might-care: Every hook-launched repository test depends on this boundary not redirecting Git operations into the invoking checkout. || If-you-do-nothing: This PR and its dependent stack layers remain unmerged.
- [Review whether the expanded explanation makes the existing template-first decision understandable; request wording changes if it does not.](../../../message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md) — Why-you-might-care: This review is about whether the documentation now explains a prior decision, not whether an implementation task may reverse it. || If-you-do-nothing: AgentFold continues to ship mechanisms as opt-in templates under the decided four-mode policy.

## Dead ends

- The first differential harness swapped the reconciler's source files in the working tree and
  ran both versions in place. That works for `--check` but `--range` fails closed with
  "candidate has unstaged changes beyond its captured commit", so range parity could never be
  proved that way. The working harness materialises the baseline into the git-ignored `tmp/`
  mirror instead, whose directory depth makes `REPO` and `AUTOMATION` resolve to the real
  repository, leaving the tree untouched. Any future A/B work on this gate needs that shape.
- Batching the per-handover `git log -1 --diff-filter=A` into one directory-wide query was
  considered and rejected: Git computes history simplification against the pathspec, so a
  directory-limited walk can reach commits a file-limited walk prunes, and the reported
  creation commit can change. It is the largest remaining `--check` cost and is still open.

## Next steps

None.

## Deep links

- Task folder: [2026-07-31-cut-reconciler-recomputation](../../../tasks/1_in-progress/2026-07-31-cut-reconciler-recomputation/task.md) · Worklog: [worklog.md](../../../tasks/1_in-progress/2026-07-31-cut-reconciler-recomputation/worklog.md) · Verification: [verification.md](../../../tasks/1_in-progress/2026-07-31-cut-reconciler-recomputation/verification.md)
- Commits: `6ad707d..HEAD` on branch task/2026-07-31-cut-reconciler-recomputation
