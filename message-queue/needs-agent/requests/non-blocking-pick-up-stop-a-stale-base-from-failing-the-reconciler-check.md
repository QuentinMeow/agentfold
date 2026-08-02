# Pick up stopping a moved base from failing the reconciler check

**Status:** open
**Filed:** 2026-08-02, by claude, reproduced on three separate pushes to pull request #65
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-stop-a-stale-base-from-failing-the-reconciler-check/task.md`
**Request kind:** task-pickup
**If unanswered:** `reconcile-and-test` keeps going red on pull requests for a reason unrelated to the change, which trains everyone to ignore it and blocks the owner's stated plan to require it once the repository is stable.

## What you need to know

The job exits 2 with `captured candidate is neither the --range head nor an exact base+head
synthetic merge` when the base branch moves between the event and the job resolving the
merge ref. The `push`-event run of the same job stays green, so it is specific to resolving
a pull request's merge ref against an advanced base.

This is the same stale-base race that `2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack`
repaired for `review-state-action-projection`, reached through a different job. That repair
interrogates the fetched merge commit's parents rather than comparing revisions; read it
before designing a second mechanism.

Establish first whether the repair belongs in the workflow, in `validate_range_candidate`,
or both. Exit 2 correctly means "this check could not run", so the defect may be an
over-narrow acceptance rule rather than wrong error handling.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
