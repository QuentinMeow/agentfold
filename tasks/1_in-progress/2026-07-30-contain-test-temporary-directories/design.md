# Design notes — Contain the test suite's temporary Git repositories to one scratch root

**Status:** decided

## Problem

`automation/run_tests.py` already builds one scratch root per run
(`tempfile.TemporaryDirectory(prefix="agentfold-tests-")` in `main()`) and points every
child test process's Git identity, `HOME`, and `XDG_CONFIG_HOME` inside it
(`install_isolated_git_configuration`). It never redirects the child processes' own notion
of "the temp directory." Every fixture that calls `tempfile.mkdtemp()` or
`tempfile.TemporaryDirectory()` with no `dir=` argument — the repeated git-repository
fixtures across `automation/tests/test_reconcile_queue.py`,
`test_check_action_projection.py`, `test_github_action_projection_workflow.py`,
`test_check_core_scope.py`, `test_run_tests.py`, and others — therefore resolves through
`tempfile.gettempdir()`, which reads the real ambient `TMPDIR`/`TEMP`/`TMP` (or the
platform default) from that child process's own environment.

On a normal completed run this is invisible: each fixture's own context manager (or, for
the once-per-process skeleton cache, an `atexit.register(shutil.rmtree, ...)` call) cleans
up before the process exits. On a killed run — measured to be the ordinary way a developer
stops a slow suite mid-development — nothing runs: `SIGKILL` (and an uncaught `SIGTERM`)
skip every `finally` block, context-manager `__exit__`, and `atexit` hook. The debris lands
directly in the real system temp directory, indistinguishable in name from any of the
thousands of unrelated files already there from other tools on the same machine.

## Options considered

### Option A — Redirect `TMPDIR`/`TMP`/`TEMP` into the existing scratch root (chosen)

Add one function, called once in `main()` right after the scratch root exists, that
creates `scratch_root / "tmp"` and points `TMPDIR`, `TMP`, and `TEMP` at it in the one
`child_environment` dict every worker subprocess already receives. Every fixture at every
call site — current and future, without needing to touch each one — resolves into this
run's own root. A completed run's outer `TemporaryDirectory` still removes it as a single
recursive unit, at the same one point in the code that already existed. A killed run
leaves exactly the outer `agentfold-tests-*` directory (already the case today) with the
scattered debris now nested inside it instead of beside it in the real system temp
directory — one named, discoverable, single-`rm -rf`-able thing instead of hundreds of
anonymous ones.

*Example consequence:* `python3 automation/run_tests.py`, killed 15s in, leaves one
`/var/folders/.../T/agentfold-tests-<random>/` directory; deleting it removes everything
the run had created up to that point.

### Option B — Wrap every call site with `addCleanup`/try-finally

Touch each of the ~9 test files' fixture helpers to register explicit cleanup. Rejected:
it does not solve the stated problem at all — `addCleanup` and `finally` are exactly the
machinery `SIGKILL` skips, so this only re-proves what already works (the completed-run
path already cleans up via context managers). It also multiplies the surface to maintain
across every current and future call site instead of one.

### Option C — A separate reaper process/manifest

Have the runner write a manifest of directories it creates and run (or schedule) a
separate cleanup pass for orphaned entries older than some age. Rejected as heavier than
the problem needs: it requires a background process or a cron-like mechanism this
repository's automation model does not otherwise have, and it does not change where the
debris lands while it is live — a `--jobs 8` run killed mid-flight still scatters
directories across the real temp directory until the reaper next runs.

## Chosen

Option A. It is the smallest change that fixes what a killed run actually does (consolidate
location) without pretending to fix what cannot be fixed for `SIGKILL` (cannot run cleanup
code at all). One call site in `main()`, symmetric with the existing
`install_isolated_git_configuration` call right above it.

**What this does and does not solve:** interruption is not made safe — nothing can make it
safe against `SIGKILL`. What changes is where the unavoidable debris lands: one named
directory under the real system temp root instead of a scattered, anonymous handful (or,
under the historical account, hundreds). `rm -rf` on any leftover `agentfold-tests-*`
directory is now sufficient and safe at any time (no such directory is ever reused across
runs — each is created fresh by `tempfile.TemporaryDirectory`'s random suffix).

## Core fit

**Agent substitution:** pass — any agent runtime that shells out to `python3 automation/run_tests.py` inherits the same redirected `TMPDIR`/`TMP`/`TEMP`; the mechanism lives in the runner's own `main()`, not in anything Claude-specific.
**Provider substitution:** not-applicable — no model or provider is involved in a test runner's own scratch-directory bookkeeping.
**Repository substitution:** pass — every repository that adopts `automation/run_tests.py` verbatim gets the same containment; the mechanism depends only on the Python standard library already required by the rest of the file, not on any AgentFold-specific path.
**User-global writes:** none
**Why AgentFold core:** `automation/run_tests.py` is the shared test runner every adopting repository uses; scratch-directory containment is a correctness property of the isolated environment it promises children (the same concern `install_isolated_git_configuration` already addresses immediately above it), not local machine configuration or a product feature.
**Thin adapter:** none
