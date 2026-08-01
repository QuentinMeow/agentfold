# Finish the replacement-ref boundary the reconciler is halfway through building

**Claimed-by:** claude
**Filed:** 2026-07-31, by claude, from a branch-cleanup audit of the unmerged task/2026-07-26-resolve-queue-items-whose-evidence-already-merged branch
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`main` passes `--no-replace-objects` to 39 Git invocations in
`automation/reconcile/reconcile.py` so that a `refs/replace/*` entry cannot make the
reconciler read a forged object in place of a real one. The boundary is incomplete: the
`git cat-file --batch` reader that every cached object read now funnels through is still
launched bare, as is `git cat-file -t`, which validates a Git review target's type.

That gap is measurable today. On `main`:

```
["git", "cat-file", "--batch"],
["git", "cat-file", "-t", object_id],
```

On the unmerged 07-26 branch the same two sites read:

```
["git", "--no-replace-objects", "cat-file", "--batch"],
[*RAW_GIT, "cat-file", "-t", object_id],
```

The 07-26 branch hardens nine functions main leaves bare and carries the regression tests
for them, but its own headline change — a creation-baseline rule for queue resolution — was
rejected on the record in `docs/designs/queue-resolution-order-independence.md` with two
reproducible hard failures. This task ports only the boundary work, so that branch can be
retired without silently losing a security investment main has already half-made.

Nothing here is urgent: exploiting `refs/replace/*` needs local write access to the
repository, and the guardrail design already states that stopping a determined local agent
from laundering objects is a non-goal. This is defence in depth, and above all it is a
guard against the gap reopening.

## Acceptance criteria

- [x] WHEN the reconciler launches its `cat-file --batch` reader, THE SYSTEM SHALL pass `--no-replace-objects`.
- [x] The remaining bare object reads on `main` — `git_object_kind`, `handover_creation_state`, `handover_current_incarnation_text`, `staged_deleted_queue_paths`, `staged_mutated_queue_paths`, `staged_mutated_handover_paths`, `task_ids_changed_on_edge`, and `task_artifact_renames_on_edge` — all read through the hardened form.
- [x] The six `test_replace_ref_cannot_*` regressions from the 07-26 branch pass on `main`: forging a review object, forging ancestry, forging synthetic-candidate parents, hiding staged admission changes, hiding a new handover, and changing a handover or staged blob baseline.
- [x] A source-level guard fails the suite when any new bare `["git", ...]` invocation is added outside a small index/worktree-only allowlist, so the gap cannot silently reopen.
- [x] `verification.md` records the real before-and-after output of each regression on an unmodified tree first.
- [x] The creation-baseline rule, `ordinary_request_resolution_evidence_problem`, and the 24 evidence-lineage tests are NOT ported — they were rejected by measurement.

## Links

- Rejected sibling rule: `docs/designs/queue-resolution-order-independence.md`
- Source of the port: the unmerged task/2026-07-26-resolve-queue-items-whose-evidence-already-merged branch
