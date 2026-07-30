# Design notes — Stop background Git maintenance racing temporary-directory teardown

**Status:** decided

## Problem

A test fixture builds a real repository inside `tempfile.TemporaryDirectory()`. On
`ubuntu-latest` the cleanup failed with `ENOTEMPTY` on `objects`; on the Git 2.23
available locally it never fails. The cause has to be something that writes inside
`.git/objects` *after* the last foreground Git command returned, and that does not exist
on Git 2.23.

Git ≥ 2.30 `git commit` calls `run_auto_maintenance()`, which spawns
`git maintenance run --auto --detach`. `maintenance_run_tasks()` takes a lock at
`<objects-dir>/maintenance` — i.e. it creates `.git/objects/maintenance.lock` — *before*
evaluating any `--auto` condition, then `daemonize()`s and only releases the lock in the
detached grandchild. So the write inside `objects/` is unconditional: being far below the
`gc.auto` threshold stops gc from doing work, but does not stop the lock or the detach.

The constraint that shapes the fix: the setting must reach Git 2.23 *and* Git 2.4x/2.5x,
must apply to every temp repository any test creates, and must not reintroduce a wrapper
script (a `/bin/sh` shim named `git` was removed precisely because it doubled the process
count of every Git call).

## Options considered

### Option A — `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_n` environment pairs
Purely environmental and inherited by every child. But `GIT_CONFIG_COUNT` landed in Git
2.31, so on Git 2.23 it is silently ignored — the local suite would prove nothing.

### Option B — a config file in the runner's scratch `HOME`
The runner already sets `HOME` and `XDG_CONFIG_HOME` to empty scratch directories.
Writing `.gitconfig` there is read by every Git version as global config. The trap: the
runner also set `GIT_CONFIG_GLOBAL=os.devnull`, and on Git 2.32+ that *replaces* the
global scope, so `$HOME/.gitconfig` would be ignored on exactly the newer Git that has
the bug. Pointing `GIT_CONFIG_GLOBAL` at the written file instead fixes that and keeps
one file as the single global source on every version.

### Option C — a retrying / error-tolerant `rmtree` helper in each fixture
Treats the symptom. `TemporaryDirectory(ignore_cleanup_errors=…)` needs Python 3.10 and
the interpreters here are 3.7.6 and 3.9.6, so it would mean a hand-written helper
duplicated across the six test files that build repositories — and it would leave the
stray background process, and its per-commit spawn cost, in place.

## Chosen

Option B. It removes the concurrent writer rather than tolerating it, reaches both Git
vintages through one file, adds no process (it *removes* one spawn per commit), and is
inherited by every temp repository through the existing child environment. Verified
empirically: six commits spawn six `git maintenance run --auto` children before the
change and zero after.

Option C stays worth doing if a teardown race is ever observed again once no background
Git process exists — it is the right shape for a cause this is not.

## Core fit

**Agent substitution:** pass — the runner is invoked as a plain script; no agent runtime reads or writes this configuration, so any agent that runs the suite gets the same isolated environment.
**Provider substitution:** not-applicable — no model provider is involved; this is Git's own behavior in a test subprocess.
**Repository substitution:** pass — every adopted repository whose tests build fixture repositories inherits the same race from Git's defaults, so the fix belongs with the shared runner rather than in one repository's tests.
**User-global writes:** none
**Why AgentFold core:** `automation/run_tests.py` is the shared test runner every adopting repository uses, and this is a correctness property of the isolated environment it promises children, not local setup: the file it writes lives inside the runner's own per-run scratch directory and is deleted with it.
**Thin adapter:** none
