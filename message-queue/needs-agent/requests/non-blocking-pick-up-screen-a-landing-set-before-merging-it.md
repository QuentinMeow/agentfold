# Pick up screening a landing set before merging it

**Status:** open
**Filed:** 2026-08-01, by claude, from task `2026-08-01-stop-human-answers-from-gating-git-edges`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-screen-a-landing-set-before-merging-it/task.md`
**Request kind:** task-pickup
**If unanswered:** `handbook/git-workflow.md` keeps telling agents to screen a landing set while nothing screens it, and cross-leg collisions keep being found by the trunk going red.

## What you need to know

Two findings are already recorded in the task and should not be rediscovered: the
reconciler cannot be run against a staged merge, so `build` must commit each merge first;
and `git merge-tree --write-tree` needs Git 2.38, so `plan` must feature-detect it or the
conflict screen silently reports every pair as conflicting.

The `land` subcommand is deliberately not part of this: it would be `gh` calls end to end,
which fails the Core-admission guardrail, and its content is now prose in
`handbook/git-workflow.md`.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
