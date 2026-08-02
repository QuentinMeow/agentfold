# Pick up the configurable test-gate and time-budget task

**Status:** open
**Filed:** 2026-08-02, by claude, from the abandoned `codex` claim on task `2026-07-27-configure-test-gates-and-time-budgets`
**Action:** When this backlog item is selected, re-derive its time budget from a suite time measured that day, then claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-27-configure-test-gates-and-time-budgets/task.md`
**Request kind:** task-pickup
**If unanswered:** The task stays unclaimed in backlog and nothing is blocked. The pre-commit hook keeps running whatever the staged-path selector picks, which is already fast for record-only commits; only the unbudgeted full-suite boundary stays unbudgeted.

## What you need to know

The task asks for one repository-local configuration file that sets a routine-gate budget,
a final-gate mode and trigger, critical scopes, and what happens when a budget is breached.
None of it exists: there is no `agentfold.toml` at any path, and no automation source
mentions a routine or final gate.

Its stated premise has partly decayed, so do not inherit its numbers. The task was written
on 2026-07-27 against a full suite measured at 214.62–221.17 seconds, and it picked 60
seconds as the routine-gate target against that. Parallelisation and selection work has
merged since; the suite measured 75.87 seconds wall clock on 2026-08-02. The task's
`## What the investigation found` section still describes the serial, process-heavy runner
that measurement replaced. Whoever claims this re-measures first and states which parts of
that section still hold, rather than implementing against the old numbers.

The 60-second target itself is the specific thing to re-derive. It was chosen as a large
cut from ~215 seconds; against ~76 seconds it may be the wrong shape of goal entirely, and
the honest options include a different number, a different metric, or recording that the
routine lane is already inside any budget worth configuring.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its reciprocal
`Queue actions` link have been removed in the claim commit.
