# Let a backlog task be claimed when another queue item names its pickup request

**Status:** open
**Filed:** 2026-07-30, by claude, from task 2026-07-30-report-check-failures-honestly
**Action:** Give the claim ritual a path that keeps both invariants — for example, teach the link check that a resolved pickup request is a lifecycle path like Resolution evidence, or forbid queue items from naming another item's pickup path — then claim task 2026-07-22-severity-tiers-for-reconciler-findings.
**Full context:** `tasks/AGENTS.md`
**Resolution evidence:** `automation/reconcile/reconcile.py`
**If unanswered:** Task 2026-07-22-severity-tiers-for-reconciler-findings stays unclaimed in backlog with its remaining scope; nothing else is blocked, because its severity split already shipped under 2026-07-30-report-check-failures-honestly.

## What you need to know

`tasks/AGENTS.md` requires a claim to delete the task's pickup request in the same
coordination commit. A live `needs-agent` request in this folder — the pre-commit mining
advisory — names that pickup request as a backticked repository path in its body. So the
claim commit produces a `link-check` finding for a path the claim ritual is required to
delete:

```
[link-check] message-queue/needs-agent/requests/future-blocking-add-the-pre-commit-mining-advisory.md: `message-queue/needs-agent/requests/non-blocking-pick-up-severity-tiers-for-reconciler-findings.md` does not exist
```

Repairing that reference is also rejected, because a request's body outside the
lifecycle fields is its action identity:

```
[queue-resolution] message-queue/needs-agent/requests/future-blocking-add-the-pre-commit-mining-advisory.md: live queue action was rewritten: action identity changed while the queue item remained live
```

Both were reproduced on branch task/2026-07-30-report-check-failures-honestly and are
recorded with full output in that task's `verification.md`. This is general: any backlog
task becomes unclaimable once another live queue item backticks its pickup path.

## Done when

A backlog task whose pickup request is named by another live queue item can be claimed
in one coordination commit with `automation/reconcile/reconcile.py --check` reporting
zero blocking findings, and a regression test covers that claim.
