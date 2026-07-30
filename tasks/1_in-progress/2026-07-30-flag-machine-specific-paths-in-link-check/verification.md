# Verification — machine-specific paths in the link check

Commands actually run, with their real output.

## The survey taken before changing behaviour

```
$ python3 - <<'PY'   # BACKTICK_RE over live markdown, skipping the check's own exempt dirs
distinct backticked absolute paths in live markdown: 3
  /bin/sh  <- 3 file(s): tasks/4_done/2026-07-29-remove-git-shell-wrapper/worklog.md
  /usr/bin  <- 1 file(s): docs/designs/fast-local-test-feedback.md
  /usr/bin/time  <- 1 file(s): docs/designs/fast-local-test-feedback.md
```

All three exist on macOS and on the Linux runner, so all five occurrences pass today by
luck rather than by construction. Each is unquoted in this change.

## The check finds them

Run against the repository before the records were unquoted:

```
$ python3 automation/reconcile/reconcile.py --check
[link-check] docs/designs/fast-local-test-feedback.md: `/usr/bin` is an absolute path, so it names a machine and not this repository
    fix: unquote it — backticks assert a repository path, and this one resolves differently on each machine
[link-check] docs/designs/fast-local-test-feedback.md: `/usr/bin/time` is an absolute path, so it names a machine and not this repository
[link-check] message-queue/needs-human/decisions/non-blocking-choose-the-test-speed-levers-to-land.md: `/bin/sh` is an absolute path, so it names a machine and not this repository
[link-check] roadmap/current-state.md: `/bin/sh` is an absolute path, so it names a machine and not this repository
[link-check] tasks/4_done/2026-07-29-remove-git-shell-wrapper/worklog.md: `/bin/sh` is an absolute path, so it names a machine and not this repository
reconcile: 5 finding(s)
```

After unquoting all five:

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## The guard fails without the change

The new block was removed from the check and the test run again, then restored:

```
$ python3 -m unittest ...test_backticked_absolute_path_is_machine_specific_not_a_link
Ran 1 test in 0.008s

FAILED (failures=2)
```

Two failures because the test covers two absolute paths as subtests. Restored:

```
$ python3 -m unittest ...test_backticked_absolute_path_is_machine_specific_not_a_link
Ran 1 test in 0.005s

OK
```

## Relative links still resolve

```
$ python3 -m unittest ...test_relative_path_that_exists_is_still_a_valid_link
Ran 2 tests in 0.007s

OK
```

The test asserting an absolute path is a finding uses two paths that exist on neither
every developer machine nor every runner, so its verdict does not depend on the
filesystem of whoever runs it. That is the property the change exists to establish.
