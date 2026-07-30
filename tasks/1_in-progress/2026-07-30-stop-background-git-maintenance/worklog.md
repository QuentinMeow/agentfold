# Worklog — Stop background Git maintenance racing temporary-directory teardown

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — git-auto-maintenance-teardown-race (Claude Opus 5, 1M context)

- Started from the hypothesis that detached auto maintenance races the fixture teardown,
  with an explicit instruction to refute it if the evidence pointed elsewhere.
- The prompt's suggested refutation — that `git gc --auto` bails below `gc.auto` and so a
  tiny fixture never trips it — is **correct about gc and wrong as a refutation**.
  Git's builtin/gc.c `maintenance_run_tasks()` takes `<objects-dir>/maintenance.lock` *before*
  any `--auto` condition is evaluated and `daemonize()`s unconditionally, so the write
  inside `objects/` does not depend on the threshold. Confirmed identical in v2.47.0
  through v2.55.0.
- Found the system git (/usr/bin/git) is 2.50.1 (Apple Git-155) while the git on PATH (/usr/local/bin/git) on `PATH` is
  2.23.0 — so both sides of the version boundary are testable on this machine. That is
  worth remembering for any future Git-version question here.
- Dead end worth not repeating: tripping `too_many_loose_objects()` by dropping 38-hex
  decoy files into the objects/17/ fanout does trip the readdir check, but the following
  `gc` then fails on the corrupt objects, so it is useless for widening the window.
- Could not reproduce the `ENOTEMPTY` locally (7,200 commits, 12-way parallel teardown,
  APFS). Reported as not-reproduced rather than claimed; see `verification.md`.
- The one real trap in the fix: `GIT_CONFIG_GLOBAL` was set to `os.devnull`, and on Git
  2.32+ that replaces the global scope, so writing `$HOME/.gitconfig` alone would have
  been silently ignored on exactly the Git versions that have the bug.
