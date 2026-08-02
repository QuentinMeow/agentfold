# Pick up stopping a human answer from holding a Git edge

**Status:** open
**Filed:** 2026-08-01, by claude, from a judged design over the queue's boundary grammar
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-01-stop-human-answers-from-gating-git-edges/task.md`
**Request kind:** task-pickup
**If unanswered:** The queue keeps admitting `transition:merge` on `needs-human/` items, the two crossed merge reviews keep failing the merge-boundary replay, and the decision filed to dispose of them keeps binding the transition it asks about.

## What you need to know

`reconcile --check` is clean on `main` while `reconcile --check --at-transition merge`
reports four boundary findings. Two of them are human reviews whose reviewed Git ranges are
already ancestors of `main`, so no future commit can supply the receipt their cleanup needs.

The repair restricts which boundary values a `needs-human/` item may bind rather than
renaming the three timing prefixes, so no live item outside the migrated set changes.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
