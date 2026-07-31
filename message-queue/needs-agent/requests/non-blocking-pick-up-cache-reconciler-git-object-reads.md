# Pick up the reconciler Git object read caching task

**Status:** open
**Filed:** 2026-07-30, by claude, from chat
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-cache-reconciler-git-object-reads/task.md`
**Request kind:** task-pickup
**If unanswered:** The task remains unclaimed in backlog; the reconciler keeps spawning one `ls-tree` per path and no current work is blocked.

## What you need to know

One `reconcile.py --check` run over this repository spawns 102
`git --no-replace-objects ls-tree -z <revision> -- <path>` processes, all of them
re-reading the same handful of commit and tree objects. The unmerged branch
task/2026-07-26-resolve-queue-items-whose-evidence-already-merged already batched those
reads; its resolution-evidence rule is being discarded, but its caching is worth keeping
on its own.

## Done when

The task has a claimant, has moved to `1_in-progress`, and this request and its
`Queue actions` link have been removed in the claim commit.
