# Verification — make the reconciler report its own failures honestly

**Verified:** 2026-07-30 by claude (worktree agent-a08cc597c4b8c87c6, branch task/2026-07-30-report-check-failures-honestly)

Only commands actually run and their real output. Every "before" transcript was captured
on the unmodified tree at commit 6cd2de9 before any fix was written; every "after"
transcript was captured on the fixed tree. Output is trimmed only where marked.

## Baseline

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
EXIT=0
```

## Defect 1 — an unreadable file exits 1 with zero findings

### Before — untracked invalid-UTF-8 Markdown

```
$ printf '# Scratch \xff\xfe notes\n' > docs/scratch-invalid.md
$ python3 automation/reconcile/reconcile.py --check
Traceback (most recent call last):
  File "automation/reconcile/reconcile.py", line 7704, in <module>
    sys.exit(main())
  File "automation/reconcile/reconcile.py", line 7695, in main
    return reconcile(argv)
  File "automation/reconcile/reconcile.py", line 7679, in reconcile
    findings = [f for check in CHECKS.values() for f in check()]
  File "automation/reconcile/reconcile.py", line 7679, in <listcomp>
    findings = [f for check in CHECKS.values() for f in check()]
  File "automation/reconcile/reconcile.py", line 7134, in check_links
    text = semantic_text(repo_text(md))
  File "automation/reconcile/reconcile.py", line 969, in repo_text
    return path.read_text(encoding="utf-8")
  File ".../pathlib.py", line 1217, in read_text
    return f.read()
  File ".../codecs.py", line 322, in decode
    (result, consumed) = self._buffer_decode(data, self.errors, final)
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 10: invalid start byte
EXIT=1
```

The staged variant crashes at the other decode, line 961:

```
$ git add docs/scratch-invalid.md
$ python3 automation/reconcile/reconcile.py --check
... (same trace)
  File "automation/reconcile/reconcile.py", line 961, in repo_text
    return artifact.decode("utf-8")
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 10: invalid start byte
```

### Before — one crash discards every finding already found

```
$ rm -f docs/scratch-invalid.md
$ python3 automation/reconcile/reconcile.py --check
[link-check] docs/scratch-broken-link.md: `docs/does-not-exist-anywhere.md` does not exist
    fix: fix the path, create the target, or unquote if not a path
reconcile: 1 finding(s)

$ printf '# Scratch \xff\xfe notes\n' > docs/scratch-invalid.md
$ python3 automation/reconcile/reconcile.py --check
... UnicodeDecodeError traceback; the link-check finding is never printed
```

### After

```
$ python3 automation/reconcile/reconcile.py --check   # untracked unreadable file
reconcile: Git snapshot error: `docs/scratch-invalid.md` is not valid UTF-8: 'utf-8' codec can't decode byte 0xff in position 10: invalid start byte
[link-check] docs/scratch-broken-link.md: `docs/does-not-exist-anywhere.md` does not exist
    fix: fix the path, create the target, or unquote if not a path
EXIT=2

$ git add docs/scratch-invalid.md && python3 automation/reconcile/reconcile.py --check
reconcile: Git snapshot error: `docs/scratch-invalid.md` is not valid UTF-8: 'utf-8' codec can't decode byte 0xff in position 10: invalid start byte
EXIT=2
```

The error line goes to stderr and the findings to stdout, so they interleave in a
combined capture. Exit 2, one line naming the file, no traceback, and the finding found
before the crash still reported.

## Defect 2 — TypeError on a valid-looking impossible date

### Before

```
$ mkdir -p tasks/4_done/2026-02-30-impossible-date
$ printf '# Impossible date probe\n' > tasks/4_done/2026-02-30-impossible-date/task.md
$ git add tasks/4_done/2026-02-30-impossible-date
$ python3 -c "...; print(list(m.check_roadmap_fresh()))"
Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "automation/reconcile/reconcile.py", line 7250, in check_roadmap_fresh
    default=None,
TypeError: '>' not supported between instances of 'NoneType' and 'datetime.date'
```

### After

Same staged tree, same call: no exception, and the comparison still runs against the
valid ids (`Last-updated: 2026-07-30` equals the newest valid done id, so no finding).

```
$ python3 tmp/probe_check.py check_roadmap_fresh
done
```

Covered by `test_impossible_done_task_date_never_crashes_roadmap_freshness`, which
asserts an impossible id alongside `2026-07-22-real` still reports
`Last-updated 2026-07-01 predates the newest done task (2026-07-22)`.

## Defect 3 — a staged violation disappears when its worktree copy is deleted

### Before

```
$ git add AGENTS.md            # staged with **Collaboration mode:** `bogus-mode`
=== A: staged violation, worktree copy present ===
[mode-valid] AGENTS.md: collaboration mode 'bogus-mode' is not autonomous|async|pair
reconcile: 1 finding(s)
$ mv AGENTS.md tmp/AGENTS.md.moved
=== B: same staged violation, worktree copy deleted ===
reconcile: 0 finding(s)
$ git show :AGENTS.md | grep -n "Collaboration mode"
15:**Collaboration mode:** `bogus-mode` — see `handbook/collaboration-modes.md` for what each
```

### Before — the three sibling sites named in the brief. All three reproduced.

```
=== A1: stale-queue with message-queue/ present in the worktree ===
[stale-queue] message-queue/needs-agent/requests/blocking-audit-probe-stale.md: filed 2026-05-01, older than 30 days
=== A2: same index, message-queue/ deleted from the worktree ===
done

=== B1: roadmap-fresh with roadmap/current-state.md present ===
[roadmap-fresh] roadmap/current-state.md: Last-updated 2026-07-01 predates the newest done task (2026-07-30)
=== B2: same index, roadmap/current-state.md deleted from the worktree ===
done
=== B3: same index, tasks/4_done/ deleted from the worktree ===
done

=== C1: memory-index with memory/ present in the worktree ===
[memory-index] memory/index.md: index does not match the memory files
=== C2: same index, memory/ deleted from the worktree ===
done
```

### After — every site reports the staged violation with the worktree copy gone

```
=== BUG3 AFTER: staged bogus mode, worktree copy deleted ===
[mode-valid] AGENTS.md: collaboration mode 'bogus-mode' is not autonomous|async|pair

=== SITE A AFTER: stale-queue, message-queue/ deleted from worktree ===
[stale-queue] message-queue/needs-agent/requests/blocking-audit-probe-stale.md: filed 2026-05-01, older than 30 days

=== SITE B1 AFTER: roadmap-fresh, current-state.md deleted from worktree ===
[roadmap-fresh] roadmap/current-state.md: Last-updated 2026-07-01 predates the newest done task (2026-07-30)

=== SITE B2 AFTER: roadmap-fresh, tasks/4_done/ deleted from worktree ===
[roadmap-fresh] roadmap/current-state.md: Last-updated 2026-07-01 predates the newest done task (2026-07-30)

=== SITE C AFTER: memory-index, memory/ deleted from worktree ===
[memory-index] memory/index.md: index does not match the memory files
```

## Defect 4 — advisory findings brick the repository on calendar dates

### Before — no repository change at all, only the clock moves

```
$ python3 tmp/probe_clock.py 2026-07-31 2026-08-13 2026-08-14 2026-08-15 2026-08-25 2027-01-22 2027-01-23
TODAY=2026-07-31  exit=0  0 finding(s)  {}
TODAY=2026-08-13  exit=0  0 finding(s)  {}
TODAY=2026-08-14  exit=0  0 finding(s)  {}
TODAY=2026-08-15  exit=1  3 finding(s)  {'stale-task': 3}
TODAY=2026-08-25  exit=1  4 finding(s)  {'stale-queue': 1, 'stale-task': 3}
TODAY=2027-01-22  exit=1  13 finding(s)  {'stale-queue': 1, 'stale-task': 3, 'memory-expiry': 9}
TODAY=2027-01-23  exit=1  23 finding(s)  {'stale-queue': 1, 'stale-task': 3, 'memory-expiry': 19}
```

The audit predicted 2026-08-09 for `stale-task`; this checkout first fails on
2026-08-15 because `days_old` reads filesystem mtime, which resets per clone. Ten memory
entries share one due date, so 2027-01-23 adds ten findings at once:

```
$ grep -rh "Review-by:" memory/ | sort | uniq -c | sort -rn | head -3
  10 **Review-by:** 2027-01-22
   4 **Review-by:** 2027-01-18
   2 **Review-by:** 2027-02-15
```

The hook runs `--check` unscoped under `set -e`, before the tests:

```
$ cat automation/hooks/pre-commit
...
echo "pre-commit: reconciler"
python3 "$ROOT/automation/reconcile/reconcile.py" --check
echo "pre-commit: staged-path repository tests"
```

### After

```
$ python3 tmp/probe_clock.py 2026-07-31 2026-08-15 2026-08-25 2027-01-22 2027-01-23
TODAY=2026-07-31  reconcile: 0 blocking finding(s)  EXIT=0
TODAY=2026-08-15  reconcile: 0 blocking finding(s), 4 advisory (not blocking)  EXIT=0
TODAY=2026-08-25  reconcile: 0 blocking finding(s), 5 advisory (not blocking)  EXIT=0
TODAY=2027-01-22  reconcile: 0 blocking finding(s), 14 advisory (not blocking)  EXIT=0
TODAY=2027-01-23  reconcile: 0 blocking finding(s), 24 advisory (not blocking)  EXIT=0
```

Advisory findings stay visible; only the exit code changed:

```
[stale-queue] message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md: filed 2026-07-25, older than 30 days  (advisory)
    fix: resolve or re-surface it; record a duplicate/moot disposition before deletion
[stale-task] tasks/1_in-progress/2026-07-25-fix-handover-projection-code-span-copy: untouched for over 14 days  (advisory)
    fix: continue it, or move back to 0_backlog and unclaim
...
reconcile: 0 blocking finding(s), 23 advisory (not blocking)
EXIT = 0
```

Counts differ by one between the before and after tables because this task's own
in-progress folder and queue item exist in the after tree.

## Claiming task 2026-07-22-severity-tiers-for-reconciler-findings is blocked

Both halves were reproduced by performing the claim exactly as `tasks/AGENTS.md`
requires, then restoring.

```
=== STEP 1: claim the backlog task exactly as tasks/AGENTS.md requires ===
[link-check] message-queue/needs-agent/requests/future-blocking-add-the-pre-commit-mining-advisory.md: `message-queue/needs-agent/requests/non-blocking-pick-up-severity-tiers-for-reconciler-findings.md` does not exist
    fix: fix the path, create the target, or unquote if not a path
reconcile: 1 blocking finding(s)
EXIT=1

=== STEP 2: repair that dead link in the item that names it ===
[queue-resolution] message-queue/needs-agent/requests/future-blocking-add-the-pre-commit-mining-advisory.md: live queue action was rewritten: action identity changed while the queue item remained live
    fix: preserve the action and response identity; file a distinct successor action when the requested work changes
reconcile: 1 blocking finding(s)
EXIT=1
```

Filed as `message-queue/needs-agent/requests/non-blocking-unblock-claiming-a-linked-pickup-task.md`.

## Regression tests

Eleven new tests, one or more per defect:

```
$ python3 -m unittest \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_unreadable_markdown_reports_the_file_and_exits_two \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_a_crashing_check_keeps_the_findings_already_reported \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_impossible_done_task_date_never_crashes_roadmap_freshness \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_mode_violation_survives_a_deleted_worktree_copy \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_roadmap_staleness_survives_a_deleted_worktree_copy \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_queue_age_survives_a_deleted_message_queue_folder \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_staged_memory_index_drift_survives_a_deleted_memory_folder \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_every_advisory_check_id_is_registered_and_tiered \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_stale_task_is_reported_by_its_own_registered_check \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_advisory_findings_report_without_failing_the_local_gate \
    automation.tests.test_reconcile_queue.ReconcileQueueTests.test_an_expired_memory_entry_does_not_block_the_commit_gate
...........
----------------------------------------------------------------------
Ran 11 tests in 0.378s

OK
```

Whole reconciler test file, no existing test changed:

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 313 tests in 84.865s
OK
```

## Full suite and clean tree

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 26.88s
```

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
EXIT=0

$ python3 automation/check_core_scope.py --staged
core-scope: pass (3 core path(s), task 2026-07-30-report-check-failures-honestly; independent review manual; not invoked)
EXIT=0
```

No commit used `--no-verify`; the pre-commit hook ran on every commit on this branch.

## Review verdicts (when a review was explicitly run)

No independent review was invoked; `--require-review` was not selected.
