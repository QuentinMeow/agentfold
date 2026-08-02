# Verification — Record the missing Stage 0 verification transcripts as real command output

**Verified:** 2026-08-02 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

The four transcripts this task exists to produce are not here. They are in the file this
task repairs: the dated section appended to the `verification.md` of task
2026-07-25-mine-markdown-cochange-couplings. This file records that the append clobbered
nothing and that the repository is green with it staged.

## the pre-existing 906 lines are byte-identical

```
$ wc -l tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md
    1070 tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md
$ head -906 tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md | md5 -q
9ed7ea55eee2d8ff9f797ceb47374dc0
$ git show HEAD:tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md | md5 -q
9ed7ea55eee2d8ff9f797ceb47374dc0
$ git show HEAD:tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md | wc -l
     906
$ git diff --numstat HEAD -- tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md
164	0	tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md
```

The committed file is 906 lines and hashes to `9ed7ea55eee2d8ff9f797ceb47374dc0`; the first
906 lines of the working copy hash to the same value. `--numstat` reports 164 insertions
and zero deletions, so no line of the gating-experiment session's record was rewritten.

## reconciler, with the result staged

```
$ git status --short
M  tasks/1_in-progress/2026-07-25-complete-stage-0-verification-transcripts/plan.md
M  tasks/1_in-progress/2026-07-25-complete-stage-0-verification-transcripts/task.md
M  tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md
$ python3 automation/reconcile/reconcile.py --check; echo "exit=$?"
reconcile: 0 blocking finding(s)
exit=0
```

That run was made before this file existed, so this file is not in the tree it saw. The
pre-commit hook re-runs the same check over the commit that carries it, and its output is
recorded below.

The first attempt at this run was not clean, and the failure is recorded rather than
silently repaired:

```
$ python3 automation/reconcile/reconcile.py --check
[task-action-origin] tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md: task artifact introduced an unqueued human action: Every run created one untracked fixture file, ran the command, and deleted the fixture. Creation, run, and deletion were a single shell line, so no fixture could outlive a failed run; nothing was ever committed, and each block ends with the `git status --short` that proves the tree came back clean. [...]
    fix: create one needs-human queue item, list it in task.md Queue actions, and replace the ask with its exact action link
reconcile: 1 blocking finding(s)
```

The sentence held no ask. `run` sat as one item of a comma-separated noun list, and a
bare command verb in that position is read as an imperative. This is a sibling of the
false positive already filed as
`message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-wrapped-line-from-reading-as-a-command.md`,
which reports the same word-position confusion arriving from a line wrap rather than from
a comma; that filing is about the pull-request body gate and this instance is
`task-action-origin` over a task artifact, so it is a second symptom rather than the same
one.

The detector was not weakened. The sentence was reworded to say the same thing without a
bare command verb in list position, and the probe below shows the trigger one clause at a
time — swapping `run` for `execution` in an otherwise identical sentence clears it, and
`check` triggers it exactly as `run` does:

```
$ python3 - <<'PY'
import sys
sys.path.insert(0, "automation")
import check_action_projection as c
for s in [
 "Creation, run, and deletion were a single shell line.",
 "Creation, execution, and deletion were a single shell line.",
 "Creation, run, and deletion happened together.",
 "Alpha, run, and beta were a single shell line.",
 "Creation, check, and deletion were a single shell line.",
]:
    print(c.action_like_task_record_prose(s), "|", s)
PY
True | Creation, run, and deletion were a single shell line.
False | Creation, execution, and deletion were a single shell line.
True | Creation, run, and deletion happened together.
True | Alpha, run, and beta were a single shell line.
True | Creation, check, and deletion were a single shell line.
```

## unit tests

This task changes no code, so the suite is unchanged evidence rather than new evidence; it
is recorded because the plan promised it. Head and tail of the run, with the shard progress
dots and the runner's own nested self-tests elided:

```
$ python3 automation/run_tests.py; echo "exit=$?"
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
  serial tail: automation/tests/test_run_tests.py -> not concurrency-safe, its tests re-run this whole runner, so a shard of it would nest a second worker pool inside the first
[...]
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
test elapsed: 77.98s
exit=0
```

## the hook that admitted the commit carrying this file

The staged run above was made before this file existed. Commit `d49b307` carries it, and
its pre-commit hook ran the same reconciler over the whole staged tree with this file in
it. The message came from a file in a scratch directory outside the repository, which is
why the command names a variable; everything after it is the hook's own output, trimmed in
the middle where it lists the twelve test files no record path selects.

```
$ git commit -F "$SP/msg-work.txt"
pre-commit: core scope
core-scope: no core changes (independent review manual; not invoked)
pre-commit: reconciler
reconcile: 0 blocking finding(s)
pre-commit: staged-path repository tests
test lane: staged
test reason: every staged path is a record path no test reads
staged paths: 5
  tasks/1_in-progress/2026-07-25-complete-stage-0-verification-transcripts/plan.md -> record path, no test reads it
  tasks/1_in-progress/2026-07-25-complete-stage-0-verification-transcripts/task.md -> record path, no test reads it
  tasks/1_in-progress/2026-07-25-complete-stage-0-verification-transcripts/verification.md -> record path, no test reads it
  tasks/1_in-progress/2026-07-25-complete-stage-0-verification-transcripts/worklog.md -> record path, no test reads it
  tasks/4_done/2026-07-25-mine-markdown-cochange-couplings/verification.md -> record path, no test reads it
[...]
no discovered test file can be affected by the staged change
tests: 0/0 files passed
test elapsed: 0.18s
pre-commit: OK
[task/2026-07-25-complete-stage-0-verification-transcripts d49b307] docs: record the four missing Stage 0 verification transcripts
 5 files changed, 341 insertions(+), 13 deletions(-)
 create mode 100644 tasks/1_in-progress/2026-07-25-complete-stage-0-verification-transcripts/verification.md
```

The staged lane selects no test file because every staged path is a record path; the full
suite in the section above is the test evidence, and it was run separately. The commit that
adds this section runs the hook once more and nothing records that run — the recursion has
to stop somewhere and it stops here. No `--no-verify` was used at any point.
