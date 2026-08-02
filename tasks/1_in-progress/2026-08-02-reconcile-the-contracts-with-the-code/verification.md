# Verification — Correct the contract text that no longer matches the code or itself

**Verified:** 2026-08-02 by claude

Only commands actually run and their real output. Every line below is re-runnable from a
clean checkout of `task/2026-08-02-reconcile-the-contracts-with-the-code`.

## The acceptance criterion: an item written from the corrected timing table is accepted

Two live-shaped `needs-human/decisions/` items were written using only what the corrected
`templates/README.md` table offers in its `needs-human/` column — one per legal spelling —
staged, and checked. They were deleted again after the run, because filing a real
`blocking-` item would claim to stop an operation nobody is performing.

`blocking-approve-deleting-the-archived-codex-guard-tag.md` carried the table's
`blocking-` cell:

```
**Blocks now:** operation:delete-archive-tag-prevent-false-github-reauth
```

`future-blocking-choose-how-none-should-read.md` carried the `future-blocking-` cell, with
the reciprocal link added to `tasks/0_backlog/2026-08-01-stop-reading-none-as-an-unanswered-field/task.md`
that `check_queue_task_reciprocity` requires:

```
**Blocks at:** transition:start task:2026-08-01-stop-reading-none-as-an-unanswered-field
```

Both accepted:

```
$ git add -A && python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
exit=0
```

## The same two items, rewritten as the *old* table described them, are refused

Only the timing token was changed — to `transition:merge`, which the pre-repair
`templates/README.md` offered in both `needs-human/` cells.

```
$ git add -A && python3 automation/reconcile/reconcile.py --check
[queue-schema] message-queue/needs-human/decisions/blocking-approve-deleting-the-archived-codex-guard-tag.md: human action may not bind transition:merge; merging, reviewing, and completing are revertible Git edges
    fix: drop the boundary and file it non-blocking-* with its unattended outcome, or bind transition:start on a 0_backlog task
[queue-schema] message-queue/needs-human/decisions/future-blocking-choose-how-none-should-read.md: human action may not bind transition:merge; merging, reviewing, and completing are revertible Git edges
    fix: drop the boundary and file it non-blocking-* with its unattended outcome, or bind transition:start on a 0_backlog task
reconcile: 2 blocking finding(s)
exit=1
```

That is the finding an agent obeying the old table would have hit. After removing both demo
items and reverting the borrowed reciprocal link:

```
$ git rm -f message-queue/needs-human/decisions/blocking-approve-deleting-the-archived-codex-guard-tag.md message-queue/needs-human/decisions/future-blocking-choose-how-none-should-read.md
$ git checkout HEAD -- tasks/0_backlog/2026-08-01-stop-reading-none-as-an-unanswered-field/task.md
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Reconciler, on the branch as published

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Line budgets after the edits

Three of the edited files carry a reconciler budget. `tasks/AGENTS.md` needed two
transitions and a corrected subject added to a file already at 59 of its 60 lines; one
neighbouring bullet was merged to pay for it.

```
$ wc -l AGENTS.md README.md tasks/AGENTS.md
     136 AGENTS.md          (budget 140)
     124 README.md          (budget 140)
      60 tasks/AGENTS.md    (budget 60)
```

The `agents-budget` check is part of the `--check` run above, which is green.

## Full test suite

```
$ python3 automation/run_tests.py
test lane: full
test reason: full suite requested
selected test files:
  automation/tests/test_check_action_projection.py
  automation/tests/test_check_core_scope.py
  automation/tests/test_collect_github_review_actions.py
  automation/tests/test_github_action_projection_workflow.py
  automation/tests/test_inspect_workspace_boundaries.py
  automation/tests/test_mine_cochange.py
  automation/tests/test_pull_request_schema.py
  automation/tests/test_reconcile_queue.py
  automation/tests/test_resolve_github_external_sources.py
  automation/tests/test_run_tests.py
  services/quote-api/tests/test_quote_api.py
  services/quote-cli/tests/test_quote_cli.py
test workers: 8
test shards: 50
...
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_pull_request_schema.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 12/12 files passed
test elapsed: 110.69s
exit=0
```

## Re-verification of each finding before it was repaired

Every claim the task quoted was re-read on this branch's base rather than trusted from the
audit revision `1871d5f`. What was checked, and against what:

```
$ git tag -l 'archive/*'
archive/2026-07-22-prevent-false-github-reauth
archive/2026-07-23-first-class-message-queue
archive/2026-07-24-consolidate-unmerged-work
archive/2026-07-26-resolve-queue-items-whose-evidence-already-merged
archive/2026-07-27-configure-test-gates-and-time-budgets
archive/2026-07-31-redo-stranded-review-disposition
```

Six tags; the fact enumerated one (finding 9). Reading each tag message with
`git tag -l --format='%(contents)'` shows only the first is a Core-admission refusal.

```
$ grep -rn "reconcile.py" automation/hooks/ .github/workflows/
automation/hooks/pre-commit:13:python3 "$ROOT/automation/reconcile/reconcile.py" --check
.github/workflows/harness.yml:53:          python3 automation/reconcile/reconcile.py --check \
.github/workflows/harness.yml:83:          python3 automation/reconcile/reconcile.py --check \
```

No caller passes `--file-retries`, which is the only mode that files or collects retry
items (finding 12).

```
$ grep -rn "non-blocking-turn-on-the-merge-gate-this-repository-already-runs" . --exclude-dir=.git
tasks/0_backlog/2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack/task.md:25
tasks/0_backlog/2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack/task.md:42
tasks/3_in-review/2026-08-01-stop-human-answers-from-gating-git-edges/verification.md:352
roadmap/current-state.md:194
history/conversations/2026-08-01-1030PDT-stop-human-answers-from-gating-git-edges/handover.md:57
history/conversations/2026-08-01-2100PDT-judge-a-handover-by-its-creation-grammar/handover.md:57
```

The file itself is absent from `message-queue/needs-human/decisions/`, so all six are dead
citations. The two in `roadmap/current-state.md` and the backlog task are repaired (findings
5 and 10); the `verification.md` and `handover.md` hits are immutable records of runs that
really happened and are left alone.

Findings 7 and 8 were checked against the source rather than the docs:
`TASK_ALLOWED_STATUS_TRANSITIONS` at `automation/reconcile/reconcile.py:70` admits
`1_in-progress → 0_backlog` and `3_in-review → 1_in-progress`, and the `open` → `in-repair`
requirement is reached only from `check_queue_task_reciprocity` at line 6074, under
`timing == "blocking"` and a `Blocks now: task:<id>` naming that task. No live `blocking-`
agent item exists, so no task in `1_in-progress` owes such a claim today and the tree is
green — which is what makes the unconditional sentence provably false.

Finding 14, before removal:

```
$ find skills/github-auth-guard -type f
skills/github-auth-guard/scripts/__pycache__/check.cpython-37.pyc
skills/github-auth-guard/scripts/__pycache__/codex_hook.cpython-37.pyc
skills/github-auth-guard/tests/__pycache__/test_check.cpython-37.pyc
skills/github-auth-guard/tests/__pycache__/test_codex_hook.cpython-37.pyc
skills/github-auth-guard/tests/__pycache__/test_install_codex.cpython-37.pyc
$ git ls-tree -r --name-only archive/2026-07-22-prevent-false-github-reauth -- skills/github-auth-guard
skills/github-auth-guard/SKILL.md
skills/github-auth-guard/scripts/check.py
skills/github-auth-guard/scripts/codex_hook.py
skills/github-auth-guard/scripts/install_codex.py
skills/github-auth-guard/tests/test_check.py
skills/github-auth-guard/tests/test_codex_hook.py
skills/github-auth-guard/tests/test_install_codex.py
```

Not empty, but empty of content: five gitignored Python 3.7 bytecode files and no source.
All seven sources survive on the tag. Removing the directory left three dangling adapter
symlinks under the gitignored `.claude`, `.cursor`, and `.agents` skill directories, which
were removed with it; `find … -type l ! -exec test -e {} \; -print | wc -l` then reported 0.

No finding turned out to be already fixed, and none was refuted.

## Review verdicts

None run. `automation/check_core_scope.py --require-review` was not selected; the core-scope
gate ran in the pre-commit hook on every commit and reported
`core-scope: pass (5 core path(s), task 2026-08-02-reconcile-the-contracts-with-the-code;
independent review manual; not invoked)`.
