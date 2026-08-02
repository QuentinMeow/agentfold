# Pick up pinning the two untested merge-provenance cases

**Status:** open
**Filed:** 2026-08-02, by claude, from task `2026-07-24-complete-staged-merge-provenance-admission`
**Action:** Claim task 2026-08-02-pin-the-unproven-merge-provenance-cases, turn the two probe fixtures into committed regressions in the queue test file, and remove this pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-pin-the-unproven-merge-provenance-cases/task.md`
**Resolution evidence:** `automation/tests/test_reconcile_queue.py`
**Request kind:** task-pickup
**If unanswered:** The two behaviours keep working and stay untested. Nothing breaks today; the risk is a future refactor silently removing committed-range parity for a post-fork human response, or unrelated-history root admission, with the suite still green.

## What you need to know

The audit that closed task `2026-07-24-complete-staged-merge-provenance-admission` verified
every acceptance criterion, and found that two sub-cases of one criterion are correct in
behaviour but held there by nothing. It built both as throwaway probes, recorded their real
findings in that task's `verification.md`, and filed this rather than tick the gap away.

Both are small. The first is a second half for two existing tests, in the exact shape two
sibling tests in the same file already use. The second is one new fixture using
`--allow-unrelated-histories`, of which the file already contains one working example for a
different check.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its `Queue
actions` link have been removed in the claim commit.
