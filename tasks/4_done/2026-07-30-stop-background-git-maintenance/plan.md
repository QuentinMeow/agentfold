# Plan — Stop background Git maintenance racing temporary-directory teardown

- [x] 1. Establish the mechanism from Git's own source: which version detaches auto
      maintenance, what it writes inside `.git/objects`, and whether a fixture-sized
      repository trips the `gc.auto` threshold.
- [x] 2. Confirm empirically against a modern Git that `git commit` spawns
      `git maintenance run --auto --detach` and that `maintenance.lock` is the only
      non-fanout entry that appears inside `.git/objects`.
- [x] 3. Establish which configuration mechanism actually reaches both Git 2.23 and
      Git 2.5x, given `GIT_CONFIG_GLOBAL` currently points at `os.devnull`.
- [x] 4. Write the settings in `install_isolated_git_configuration` and repoint
      `GIT_CONFIG_GLOBAL` at that file.
- [x] 5. Add a test that reads the keys back through a child Git process, and update the
      two existing assertions the change invalidates.
- [x] 6. Run the two affected test files on both Git versions, plus the reconciler.
