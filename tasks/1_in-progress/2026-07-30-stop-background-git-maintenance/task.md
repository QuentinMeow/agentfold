# Stop background Git maintenance racing temporary-directory teardown in tests

**Claimed-by:** Claude Opus 5 (1M context)
**Filed:** 2026-07-30, by Claude Opus 5 (1M context), from chat — CI failure on [run 30518101787](https://github.com/QuentinMeow/agentfold/actions/runs/30518101787)
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`automation/tests/test_mine_cochange.py` failed on `ubuntu-latest` with
`OSError: [Errno 39] Directory not empty: 'objects'` while `tempfile.TemporaryDirectory`
cleaned up a fixture repository, and never reproduces on the Git 2.23 some contributors
run locally. Since Git 2.30 every `git commit` runs `git maintenance run --auto --detach`;
the detached grandchild creates and later removes `<objects-dir>/maintenance.lock`, so a
process the test never waited for writes inside `.git/objects` after `subprocess.run` has
already returned. Turning that off in the runner's isolated Git configuration removes the
only concurrent writer, and removes one spawned process per commit while it is there.

## Acceptance criteria

- [x] A child Git process launched from the isolated test environment reports
      `gc.auto=0`, `gc.autoDetach=false`, `maintenance.auto=false` and
      `maintenance.autoDetach=false`.
- [x] The settings reach Git 2.23 (no `GIT_CONFIG_COUNT`, no `GIT_CONFIG_GLOBAL`) and
      Git 2.32+ (where `GIT_CONFIG_GLOBAL` replaces the global scope) alike.
- [x] No wrapper script and no extra process per Git call is reintroduced.
- [x] `git commit` under the isolated environment spawns no `git maintenance run --auto`.
- [x] `automation/tests/test_run_tests.py` and `automation/tests/test_mine_cochange.py`
      pass on both Git versions available here.

## Links

- `docs/designs/fast-local-test-feedback.md` — why no wrapper may return
- task 2026-07-29-remove-git-shell-wrapper — removed the interposed shell shim
