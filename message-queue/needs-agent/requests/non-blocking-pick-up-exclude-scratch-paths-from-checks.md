# Pick up the exclude-scratch-paths-from-checks task

**Status:** open
**Filed:** 2026-07-30, by claude, from two agents independently bricking their checkout
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-exclude-scratch-paths-from-checks/task.md`
**Request kind:** task-pickup
**If unanswered:** The reconciler keeps reporting findings for git-ignored scratch content under `tmp/`, and a stray scratch file left there can still block every commit via the pre-commit hook.

## What you need to know

`reconcile.py --check` walks the live working tree (not just the Git index) so
untracked-but-present content is caught before it is staged. That walk does not
consult `.gitignore`, so a scratch file under the contract's own designated `tmp/`
scratch directory trips real findings (`agents-budget` observed in practice), and one
finding blocks every commit through the pre-commit hook. The task adds a single
Git-backed exclusion primitive that every filesystem-walking check shares, without
weakening any check for content that is actually tracked.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
