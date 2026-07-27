# May the two validated coordination commits be pushed directly to main?

**Status:** waiting
**Filed:** 2026-07-27, by codex, from task `2026-07-27-configure-test-gates-and-time-budgets`
**Action:** Authorize the two validated coordination commits to be pushed directly to `main`, or require pull requests for them.
**Full context:** `handbook/git-workflow.md`
**Why-you-might-care:** Direct publication is the repository's prescribed path for live task and queue coordination, but it changes the shared default branch.
**If-you-do-nothing:** The task stays unclaimed and implementation does not start; both validated commits remain local.
**Resolution evidence:** `history/conversations/2026-07-27-0619PDT-configurable-test-gates-coordination/handover.md`
**Blocks at:** transition:start task:2026-07-27-configure-test-gates-and-time-budgets
**Until then:** Design resolution may finish locally, but no implementation or remote publication begins.

## What you need to know

The current `main` checkout held three staged parent-task records and six untracked records for
this child task. They were copied into clean worktrees and each coordination snapshot passed the
reconciler and the complete 11-file repository suite. The host safety layer rejected a direct
push because this conversation had not explicitly authorized updating `main`.

## Differences

Direct-to-`main` keeps the queue and task ledger current immediately, as required by the
repository contract. Using pull requests is safer at the hosting boundary but delays live
coordination and departs from that contract for these record-only commits.

## Options

### Option A — Authorize direct push
Push the parent-task filing commit, then the child-task filing and atomic claim commits to
`main`; implementation starts only after those pushes succeed.
*Example consequence:* Other agents immediately see the task as claimed before code work starts.

### Option B — Require pull requests
Publish the coordination commits on review branches and wait for them to merge before claiming
or implementing the task.
*Example consequence:* The shared default branch changes only after review, but the task remains
paused until those record-only pull requests land.

## Recommendation

Option A, because it matches the repository's explicit live-coordination workflow and both
candidate snapshots have passed the full local guard.

**Your answer:** Option A
