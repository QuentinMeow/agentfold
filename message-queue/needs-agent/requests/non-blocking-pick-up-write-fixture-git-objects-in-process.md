# Pick up building fixture Git history without spawning add and commit

**Status:** open
**Filed:** 2026-07-30, by claude, from `docs/designs/fast-local-test-feedback.md`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-write-fixture-git-objects-in-process/task.md`
**Request kind:** task-pickup
**Resolution evidence:** `tasks/0_backlog/2026-07-30-write-fixture-git-objects-in-process/task.md`

**If unanswered:** The suite keeps spending two process spawns per fixture commit, and the measured 13.5x per commit stays unclaimed.

## What you need to know

The suite's cost is process creation, not computation: a full run measures 198.57s wall
with 102.63s system against 81.70s user, and a bare `git --version` costs 5.59ms here.
About 74s of a full run is process startup alone.

The loose object format is small and documented: a header of type, space, size and a NUL
byte, then the content; the object identifier is the SHA-1 of that, stored zlib-compressed
under a two-character prefix directory. A measured probe wrote a blob, tree and commit
this way and real Git resolved the resulting history correctly.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
