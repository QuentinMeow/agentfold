# Verification — Stop background Git maintenance racing temporary-directory teardown

**Verified:** 2026-07-30 by Claude Opus 5 (1M context)

Two Git versions are available on this machine, which is what makes the portability
claim checkable: `/usr/local/bin/git` is 2.23.0 (predates `git maintenance` entirely)
and `/usr/bin/git` is 2.50.1 (has the detached auto-maintenance that CI hits).

## The mechanism: `git commit` spawns detached maintenance

```
$ GIT_TRACE=1 /usr/bin/git commit -qm "c2" 2>&1 | grep -E "maintenance|gc --auto"
10:35:23.225471 run-command.c:673       trace: run_command: git maintenance run --auto --quiet --detach
10:35:23.225505 run-command.c:765       trace: start_command: /Applications/Xcode.app/Contents/Developer/usr/libexec/git-core/git maintenance run --auto --quiet --detach
10:35:23.234756 git.c:476               trace: built-in: git maintenance run --auto --quiet --detach
```

## What that detached child writes inside `.git/objects`

A polling thread watched `.git/objects` across 120 ordinary commits and recorded every
entry that is neither a two-hex fanout directory nor `info`/`pack`:

```
$ /usr/bin/python3 watch_objects.py
commits: 120
non-fanout entries observed inside .git/objects: {'maintenance.lock': 327}
maintenance.lock still present the instant `git commit` returned: 0/120
```

`maintenance.lock` is the only thing that ever appears. On this machine the detached
child always finished before the caller could look — which is why this reproduces on a
loaded CI runner and not here.

## The trap: writing `$HOME/.gitconfig` alone is invisible on the Git that has the bug

`gc.auto = 0` written to the scratch `HOME`, read back three ways:

```
$ # A: the environment as it was — GIT_CONFIG_GLOBAL=/dev/null, git 2.50.1
$ HOME=$PWD/../home XDG_CONFIG_HOME=$PWD/../xdg GIT_CONFIG_GLOBAL=/dev/null \
    GIT_CONFIG_NOSYSTEM=1 /usr/bin/git config --get gc.auto
  git 2.50.1 gc.auto -> exit=1 (empty means NOT seen)

$ # B: GIT_CONFIG_GLOBAL pointed at the written file, git 2.50.1
$ HOME=$PWD/../home XDG_CONFIG_HOME=$PWD/../xdg GIT_CONFIG_GLOBAL=$PWD/../home/.gitconfig \
    GIT_CONFIG_NOSYSTEM=1 /usr/bin/git config --get gc.auto
0
  git 2.50.1 gc.auto -> exit=0

$ # C: same, on git 2.23.0, which ignores GIT_CONFIG_GLOBAL and reads $HOME/.gitconfig
$ HOME=$PWD/../home XDG_CONFIG_HOME=$PWD/../xdg GIT_CONFIG_GLOBAL=$PWD/../home/.gitconfig \
    GIT_CONFIG_NOSYSTEM=1 /usr/local/bin/git config --get gc.auto
0
  git 2.23.0 gc.auto -> exit=0
```

One file named by both `HOME` and `GIT_CONFIG_GLOBAL` is what covers both versions.

## The fix removes the spawn

Six commits in a fixture repository, counting `run_command: git maintenance run --auto`
in `GIT_TRACE` output, with and without `install_isolated_git_configuration`:

```
$ /usr/bin/python3 verify_fix.py
control (plain isolated HOME)                maintenance spawns over 6 commits: 6
with install_isolated_git_configuration      maintenance spawns over 6 commits: 0

git version: git version 2.50.1 (Apple Git-155)
RESULT: 6 -> 0
```

## Affected test files, Git 2.50.1

```
$ export PATH=/usr/bin:$PATH && git --version
git version 2.50.1 (Apple Git-155)
$ /usr/bin/python3 automation/tests/test_run_tests.py
Ran 48 tests in 3.542s
OK (skipped=1)
$ /usr/bin/python3 automation/tests/test_mine_cochange.py
Ran 28 tests in 11.559s
OK
```

## Affected test files, Git 2.23.0

```
$ git --version
git version 2.23.0
$ /usr/bin/python3 automation/tests/test_run_tests.py
Ran 48 tests in 1.935s
OK (skipped=1)
$ /usr/bin/python3 automation/tests/test_mine_cochange.py
Ran 28 tests in 6.506s
OK
```

## Reconciler

```
$ /usr/bin/python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## Not reproduced locally

The failure itself did not reproduce here, and that is reported rather than papered over.
7,200 commits across 900 fixture repositories, torn down by 12 concurrent workers the
instant `git commit` returned, on APFS with Git 2.50.1:

```
$ /usr/bin/python3 race.py 900
iterations=900 workers=12 maintenance_disabled=False elapsed=125.2s
objects/maintenance.lock present at teardown: 0/900
rmtree failures: 0
```

The detached child wins the race by microseconds on this filesystem every time. The
mechanism is therefore established from Git's source plus the observations above, not
from a local reproduction of the `ENOTEMPTY` itself.
