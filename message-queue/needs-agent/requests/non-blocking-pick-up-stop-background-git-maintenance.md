# Pick up the background-maintenance teardown race

**Status:** open
**Filed:** 2026-07-30, by Claude Opus 5 (1M context), from the CI failure on run 30518101787
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-30-stop-background-git-maintenance/task.md`
**Request kind:** task-pickup
**Resolution evidence:** `tasks/0_backlog/2026-07-30-stop-background-git-maintenance/verification.md`
**If unanswered:** The repository test suite keeps failing intermittently on `ubuntu-latest` while passing every local run, because the race only exists on Git 2.30 and newer.

## What you need to know

A merge to main failed with `OSError: [Errno 39] Directory not empty: 'objects'` while
`tempfile.TemporaryDirectory` cleaned up a fixture repository in
`automation/tests/test_mine_cochange.py`. Since Git 2.30 every `git commit` runs
`git maintenance run --auto --detach`; the detached grandchild creates and later removes
a lock file inside `.git/objects`, so a process the test never waited for writes into
that directory after the foreground command already returned. The Git 2.23 available
locally predates the feature entirely, which is why no local run reproduces it.

The fix belongs in the isolated environment `automation/run_tests.py` hands every child,
so it covers every temporary repository any test builds rather than one fixture. The
version trap to respect: `GIT_CONFIG_COUNT` needs Git 2.31 and `GIT_CONFIG_GLOBAL` needs
2.32, and the runner already sets `GIT_CONFIG_GLOBAL` to `os.devnull`, which on Git 2.32+
replaces the global scope outright.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
