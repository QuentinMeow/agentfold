# Stop pre-commit from re-auditing history imported from main

**Status:** open
**Filed:** 2026-08-31, by codex, from a user-requested verification of the pre-commit merge gate
**Action:** Repair the staged-merge reconciliation path so a task branch is not blocked by findings in unchanged history imported from main, while preserving findings for defects the branch authored.
**Full context:** [pre-commit entry point](automation/hooks/pre-commit)
**Resolution evidence:** `automation/tests/test_reconcile_queue.py`
**If unanswered:** Merging main into a stale task branch continues to fail at pre-commit even when the staged tree equals clean main; agents must avoid that merge and start fresh from main when they need current history.

## What you need to know

The reconciler (the script that checks repository invariants) gives different verdicts for the same tree depending on which branch presents it. The pre-commit hook invokes `reconcile.py --check` without a range. During a merge, `queue_revision_edges()` then asks `staged_side_commits()` for every commit reachable from `MERGE_HEAD` but not from `HEAD`, and audits those imported commits with the current activation context.

This is related to backlog task `2026-08-08-stop-a-withdrawn-exemption-from-dirtying-past-edges`, which covers historical edges that become dirty after an exemption changes. The repair agent should consolidate the work if one implementation and one regression-test matrix can satisfy both; this request specifically owns the staged pre-commit case and the identical-tree proof below.

### Reproduction on current main

The scratch clone started at the last first-parent commit before 2026-08-27 and staged a no-fast-forward merge of current `origin/main` without committing:

```text
$ git checkout --detach 3f9ee8920510f7a72c7a979828a3981adbecbd68
HEAD is now at 3f9ee89 Merge pull request #79 from QuentinMeow/task/2026-08-03-make-linked-worktree-bootstrap-concurrency-safe

$ git merge --no-ff --no-commit 0c9387ef8d5cd973fac6c80fd94e95da61db0c8e
Automatic merge went well; stopped before committing as requested
```

The first two object IDs are `HEAD` and `MERGE_HEAD`; the count is the imported side history; the last two IDs are the staged tree and incoming main tree:

```text
$ git rev-parse HEAD MERGE_HEAD && git rev-list --count MERGE_HEAD --not HEAD && git write-tree && git rev-parse MERGE_HEAD^{tree}
3f9ee8920510f7a72c7a979828a3981adbecbd68
0c9387ef8d5cd973fac6c80fd94e95da61db0c8e
125
257886ff1258f6c82e5d71b1767fc14250296435
257886ff1258f6c82e5d71b1767fc14250296435
```

The staged merge fails even though those tree IDs match:

```text
$ zsh -o pipefail -c 'python3 automation/reconcile/reconcile.py --check 2>&1 | tail -n 1'
reconcile: 2 blocking finding(s), 10 advisory (not blocking)
(exit 1)
```

The full run identified both blockers as `task-action-origin` findings in the verification record for task `2026-08-04-stop-review-verdicts-from-looking-like-human-asks`. The detected lines are completed adversarial-panel approvals about core fit and receipt authority, but the current parser reads them as unqueued human actions.

Current main at the identical tree passes when no merge context asks the reconciler to re-audit the imported history:

```text
$ zsh -o pipefail -c 'python3 automation/reconcile/reconcile.py --check 2>&1 | tail -n 1'
reconcile: 0 blocking finding(s), 7 advisory (not blocking)
(exit 0)
```

### Repair directions to evaluate

Neither direction is endorsed; the repair task owns the decision and the regression cases.

- In the reconciler, exclude commits already reachable from the upstream being merged so the staged audit covers what the receiving branch authored rather than what it received. The objection is that this trusts the upstream to have audited those commits, which is unsafe after an upstream force rewrite.
- In the hook, detect `MERGE_HEAD` and reconcile a committed merge boundary, matching the ordering already documented by `automation/integrate.py`. The objection is that every caller must then implement the boundary correctly instead of the checker owning it.

## Done when

- A regression test stages a merge whose tree equals a clean upstream tree and proves the reconciler gives both contexts the same blocking verdict.
- The repair continues to report a defect introduced by the receiving branch rather than imported unchanged from upstream.
- The repair records whether it consolidates or remains separate from task `2026-08-08-stop-a-withdrawn-exemption-from-dirtying-past-edges`.
- `python3 automation/reconcile/reconcile.py --check` ends with no blocking findings, and `python3 automation/run_tests.py` passes with the real outputs recorded before this request is resolved.
