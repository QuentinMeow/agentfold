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

### Added after adversarial review — the boundary is not the reconciler's alone

The title claims the boundary is finished, so it has to cover every gate a repository
state can point at a chosen revision, not only the reconciler.

- [x] WHEN `check_core_scope.py` resolves, compares, or walks a reviewed revision, THE SYSTEM SHALL read through `--no-replace-objects`, so a blob cannot pass its "is this a commit" test and a stale core-fit review cannot report clean.
- [x] WHEN `run_tests.py --staged` reads the staged diff against HEAD, THE SYSTEM SHALL read through `--no-replace-objects`, so a replacement entry cannot choose which tests the pre-commit hook runs.
- [x] `check_action_projection.py` hardens in its `git_output` helper rather than at each caller, so a new caller cannot forget the flag.
- [x] The merge and push adapters in `.github/workflows/harness.yml` read `cat-file -e` and `merge-base` through the flag, matching the hardened blocks already in that file; `git fetch` is the one subcommand that may stay bare, and a test holds that line.
- [x] The source-level guard scans all four gates, starts at the spawn call sites rather than at list literals, and catches an argument list written as a tuple, as a name bound to `"git"`, as a shell string, as a concatenation, through `os.popen`, or through `list(...)`.
- [x] The guard's starred rule applies in argument position only, so an ordinary `[*CONSTANT, "x"]` elsewhere in a scanned file is not a security failure, and every finding carries its source text.
- [x] The test docstring states what the guard cannot see instead of claiming total coverage, and `design.md` states what is and is not covered.
- [x] Each new exploit is reproduced against the unfixed file first, with the real output in `verification.md`, and a regression covers each one.

## Links

- Rejected sibling rule: `docs/designs/queue-resolution-order-independence.md`
- Source of the port: the unmerged task/2026-07-26-resolve-queue-items-whose-evidence-already-merged branch
