# Pick up reporting a task whose work already merged

**Status:** open
**Filed:** 2026-08-02, by claude, from a status audit of every open task folder
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-notice-a-task-whose-work-already-merged/task.md`
**Request kind:** task-pickup
**If unanswered:** Nothing checks whether a task's folder still matches reality, so the next run of merges silently corrupts the record agents read to decide what to pick up.

## What you need to know

On 2026-08-02 an audit found 22 of the 24 folders in `tasks/1_in-progress/` and
`tasks/3_in-review/` holding work already merged into `main`, every task branch merged and
deleted, while `python3 automation/reconcile/reconcile.py --check` reported
`0 blocking finding(s)`. The referee has no check that compares a task's folder against
whether its work landed, so the invariant `tasks/AGENTS.md` states — the folder **is** the
status — drifted in bulk without a single finding.

The task specifies the check and names the three questions its design has to settle:
which severity tier, what evidence counts as "merged" once a branch is deleted, and how to
keep the extra Git reads off the pre-commit path.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
