# Experiment E — remove the shell Git wrapper from `automation/run_tests.py`

**Branch:** exp/e-git-wrapper (from `main` @ `bf6f726`)
**Commit:** `e900216` — `automation: isolate child Git config by environment, not a shell wrapper`
**Committed with `git commit --no-verify`** (stated as permitted): the pre-commit hook runs
`check_core_scope.py --staged`, which fails on any non-`task/<task-id>` branch, and the full
staged-lane test suite, which is the thing being measured.

**Verdict: the wrapper can be removed safely.** Every isolation property it provided is
preserved by child-environment variables, with one narrow residual difference documented
below (system-level Git config for *grandchild* processes of tests that deliberately strip
`GIT_*` from their own environments). Per-Git-call cost halves.

---

## 1. Diff summary

`git show --numstat --format="" e900216`:

```
16	32	automation/run_tests.py
133	15	automation/tests/test_run_tests.py
```

`automation/run_tests.py` (+16 / −32):

- `install_isolated_git_wrapper()` → **`install_isolated_git_configuration()`**. It no
  longer writes a `#!/bin/sh` `git` script into `<scratch>/git-wrapper/` and no longer
  prepends that directory to the child `PATH`. It now sets, directly in
  `child_environment`:
  - `HOME` → `<scratch>/git-home` (freshly created, empty)
  - `XDG_CONFIG_HOME` → `<scratch>/git-xdg-config` (freshly created, empty)
  - `GIT_CONFIG_GLOBAL` → `os.devnull` (kept; belt-and-braces, effective on Git ≥ 2.32)
  - `GIT_CONFIG_NOSYSTEM` → `"1"` (unchanged from before)
- The fail-closed `shutil.which("git", path=child_environment["PATH"])` + `is_file()` +
  `os.access(..., X_OK)` guard is **kept**, so the runner still refuses to start when Git
  is not resolvable from the child `PATH`. `PATH` itself is now left byte-identical to the
  caller's.
- Constant `REAL_GIT_ENVIRONMENT = "AGENTFOLD_TEST_REAL_GIT"` **deleted**, and the
  `import shlex` with it. Its only purpose was to stop a *nested* runner from wrapping the
  outer runner's wrapper; with no shim on `PATH` there is nothing to re-wrap, and
  `shutil.which("git")` always resolves the real binary. Nothing else in the repository
  referenced either name (verified: `grep -rn "REAL_GIT_ENVIRONMENT\|install_isolated_git_wrapper\|shlex" --include='*.py' automation/ services/ skills/ .github/` → no matches after the change).
- Module docstring now states the isolation contract: "Each child receives a sanitized Git
  environment, an empty `HOME` and XDG config root so no caller Git configuration is
  readable, …".

`automation/tests/test_run_tests.py` (+`import shutil`, 34 → 35 test methods): one test
replaced, one assertion pair replaced, one new test added. Details in §7.

No other tracked file changed. This `RESULT.md` is untracked; the measurement harnesses
(`tmp/bench_git_call.py`, `tmp/ab_isolation.py`, `tmp/probe_isolation.py`, `tmp/run_one.py`,
`tmp/before_suite.sh`, `tmp/after_suite.sh`, `tmp/ab_pairs.sh`) live in the git-ignored
scratch directory.

---

## 2. Per-Git-call cost (`tmp/bench_git_call.py`, N = 60, interleaved)

The two arms are byte-faithful reconstructions of the pre-change and post-change child
environments; the arms are **interleaved** call-by-call so they share the same machine load.

```
real git: /usr/local/git/bin/git
shell-wrapper git            n=60 median=25.39ms min=22.72ms mean=26.05ms max=32.16ms
env-isolated git             n=60 median=12.53ms min=10.82ms mean=12.89ms max=18.85ms
tax: 12.87ms/call (2.03x)  min-tax: 11.90ms/call
```

That first run was taken with the machine at 1-min load ≈ 5.7. Re-run after the change, with
the *real* `install_isolated_git_configuration` from the committed code driving the second
arm (the script imports `automation/run_tests.py` and calls it), on a quieter machine
(load 3.66 → 2.02):

```
real git: /usr/local/git/bin/git
shell-wrapper git            n=60 median=10.23ms min=9.28ms mean=10.43ms max=12.88ms
env-isolated git             n=60 median=5.10ms min=4.51ms mean=5.16ms max=6.33ms
tax: 5.13ms/call (2.01x)  min-tax: 4.77ms/call
```

| | median | min | tax | ratio |
|---|---|---|---|---|
| loaded (load ≈ 5.7), replicated arms | 25.39 / 12.53 ms | 22.72 / 10.82 ms | 12.87 ms | **2.03×** |
| quiet (load ≈ 2–3.7), real installer | 10.23 / 5.10 ms | 9.28 / 4.51 ms | 5.13 ms | **2.01×** |

The **ratio is invariant at ≈ 2.0×** across a 2.5× swing in machine load, while the absolute
per-call tax scales with load (12.87 ms → 5.13 ms). That is exactly the signature of "one
extra `fork`+`exec` per call": the cost of creating a process, not of doing work.

Cross-check against §4: the full suite lost 180.98 s, which over the investigation's
13,261 Git calls is **13.65 ms/call** — within 6 % of the 12.87 ms/call measured directly
under comparable load. The two independent measurements agree.

This also reproduces the investigation's profiler figure (11.8 ms/call, 2.05×) rather than
its higher under-load figure, which is what one expects from an interleaved measurement.

---

## 3. The long pole — `automation/tests/test_reconcile_queue.py`

### 3a. Control: the file run standalone, outside the runner (no isolation at all)

```
=== standalone test_reconcile_queue (control) run 1 ===
reconcile: 0 finding(s)
reconcile: 0 finding(s)
reconcile: 0 finding(s)
real 233.59
user 94.31
sys 131.28
```

This is what the file costs when `git` is the bare binary on the caller's `PATH`. A
standalone run is *identical* before and after the change (the runner is not involved), so it
is a control, not a comparison.

**Do not compare this 233.59 s to the 86 s in §3c round 2.** It was taken at 19:26 with the
machine at 1-min load ≈ 5.7 and cold caches; round 2 ran at 20:41 at load ≈ 2–3.7 with warm
caches. Across this session the same work varied by more than 2×, purely from load and
caching (see §9.5). Only numbers taken adjacent in time are comparable.

### 3b. Through the real runner, pre-change (single run, contaminated)

```
=== run_one through runner, BEFORE, run 1 ===
reconcile: 0 finding(s)
PASS automation/tests/test_reconcile_queue.py
tests: 1/1 files passed
test elapsed: 430.61s
run_one elapsed: 430.61s
real 430.84
user 162.60
sys 233.18
```

**This number is contaminated and I am reporting it as such.** Another agent started a
full-suite measurement at 19:31 while this run (19:29–19:37) was in flight, and the shared
/private/tmp/agentfold-bench.lock I was holding disappeared without my releasing it (my
own `rmdir` at the end failed with *"No such file or directory"*, so I did not take anyone
else's lock either). The ratio 430.61 s vs the 233.59 s control is therefore an upper
bound on the wrapper tax, not a clean measurement.

Because of that, the trustworthy comparison for this file is the interleaved A/B below.

### 3c. Interleaved A/B — old wrapper env vs new env isolation

`tmp/ab_isolation.py` builds **one** projection with the real runner machinery, then runs
the same projected test file alternately under a verbatim copy of the removed
`install_isolated_git_wrapper` and under the new `install_isolated_git_configuration`.
Arm order alternates from pair to pair *within one process*.

**Round 1 — three pairs, one lock acquisition each (`tmp/ab_pairs.sh`, 20:20–20:38):**
Verbatim except that the per-arm `n=1 median=… min=… values=…` echo lines, which restate the
single sample already shown, are omitted.

```
=== pair 1: LOCK ACQUIRED 20:20:37 ===
20:20  up 2 days, 13:25, 3 users, load averages: 3.55 4.13 4.73
pair 1  old-shell-wrapper      325.09s  rc=0
pair 1  new-env-isolation      193.91s  rc=0
median saving: 131.19s (40.4%, 1.68x faster)
=== pair 1: RELEASING 20:29:17 ===
=== pair 2: LOCK ACQUIRED 20:29:17 ===
20:29  up 2 days, 13:33, 3 users, load averages: 3.60 4.01 4.44
pair 1  old-shell-wrapper      214.93s  rc=0
pair 1  new-env-isolation       87.78s  rc=0
median saving: 127.15s (59.2%, 2.45x faster)
=== pair 2: RELEASING 20:34:20 ===
=== pair 3: LOCK ACQUIRED 20:34:20 ===
20:34  up 2 days, 13:39, 3 users, load averages: 2.64 3.41 4.05
pair 1  old-shell-wrapper      141.44s  rc=0
pair 1  new-env-isolation       95.33s  rc=0
median saving: 46.11s (32.6%, 1.48x faster)
=== pair 3: RELEASING 20:38:17 ===
all pairs done
```

(The `pair 1` label repeats because each acquisition is a fresh single-pair process; the
absolute times fall across the three because the machine was draining — 1-min load
3.55 → 3.60 → 2.64 — and the OS caches were warming.)

**Methodological flaw in round 1, and its fix.** Running one pair per process meant the
alternating order never engaged: `old-shell-wrapper` ran **first** in all three pairs, so the
first arm paid every cold-cache cost. That biases *in favour of the new arm*, so round 1
overstates the win. Round 2 runs both orderings inside one process:

**Round 2 — two pairs, balanced ordering, one lock acquisition (20:41–20:48):**

```
LOCK ACQUIRED 20:41:09
20:41  up 2 days, 13:45, 3 users, load averages: 3.66 3.56 3.82
pair 1  old-shell-wrapper      144.59s  rc=0
pair 1  new-env-isolation       85.93s  rc=0
pair 2  new-env-isolation       86.94s  rc=0
pair 2  old-shell-wrapper      141.37s  rc=0

old-shell-wrapper    n=2 median=142.98s min=141.37s values=144.59, 141.37
new-env-isolation    n=2 median=86.43s min=85.93s values=85.93, 86.94
median saving: 56.54s (39.5%, 1.65x faster)
```

Round 2 is the number to trust: order-balanced, same process, adjacent in time, warm caches,
and the two runs of each arm agree to within 2 % of each other (144.59 / 141.37 and
85.93 / 86.94).

**All five pairs, both rounds:**

| | old shell wrapper | new env isolation | saving |
|---|---|---|---|
| round 1, pair 1 (old first) | 325.09 s | 193.91 s | 131.19 s (40.4 %) |
| round 1, pair 2 (old first) | 214.93 s | 87.78 s | 127.15 s (59.2 %) |
| round 1, pair 3 (old first) | 141.44 s | 95.33 s | 46.11 s (32.6 %) |
| round 2, pair 1 (old first) | 144.59 s | 85.93 s | 58.66 s (40.6 %) |
| round 2, pair 2 (**new first**) | 141.37 s | 86.94 s | 54.43 s (38.5 %) |
| **median of all five** | **144.59 s** | **87.78 s** | **56.81 s (39.3 %)** |

The order-balanced 39.5 % and the five-pair median 39.3 % both land on the full suite's
independently measured 39.6 % (§4).

### 3d. Sanity control — a file that makes no Git calls

`services/quote-cli/tests/test_quote_cli.py`, same A/B harness:

```
pair 1  old-shell-wrapper        0.79s  rc=0
pair 1  new-env-isolation        0.81s  rc=0
```

No Git calls → no difference, as expected. This shows the harness itself adds no bias.

---

## 4. Full suite

Both runs are `python3 automation/run_tests.py` (default full lane) on this worktree, one
bench-lock acquisition each, `uptime` recorded either side. The BEFORE run is the real
pre-change code: `tmp/before_suite.sh` checks out `automation/run_tests.py` and
`automation/tests/test_run_tests.py` at `bf6f726` into the working tree, runs, and restores
`HEAD` (it verified `install_isolated_git_wrapper` was present — `grep -c` → 2 — before
starting, and `0 dirty path(s)` after restoring).

**BEFORE (`bf6f726` code, 19:51–19:58):**

```
LOCK ACQUIRED 19:51:00
19:51  up 2 days, 12:55, 3 users, load averages: 5.68 6.19 7.66
reverted to bf6f726: e900216 working tree now pre-change
2
suite exit=0
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 457.15s
real 457.32
user 183.29
sys 234.69
19:58  up 2 days, 13:03, 3 users, load averages: 4.21 4.61 6.22
restored HEAD:        0 dirty path(s)
```

Per-file test counts summed from that run's `Ran N tests` lines: **624 tests in 11 files**
— matching the figure in the task.

```
$ grep -o "Ran [0-9]* tests" tmp/before_suite.txt
Ran 118 tests / Ran 55 / Ran 24 / Ran 10 / Ran 40 / Ran 28 / Ran 298 / Ran 9 / Ran 34 / Ran 5 / Ran 3
files with counts: 11 total tests: 624
```

**AFTER (commit `e900216`, 20:12–20:17):**

```
LOCK ACQUIRED 20:12:23
20:12  up 2 days, 13:17, 3 users, load averages: 4.85 4.96 5.33
2
suite exit=0
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 276.17s
real 276.36
user 115.00
sys 149.82
files with counts: 11 total tests: 625
20:17  up 2 days, 13:21, 3 users, load averages: 5.45 4.71 5.06
```

| | BEFORE | AFTER | Δ |
|---|---|---|---|
| wall (`test elapsed`) | 457.15 s | 276.17 s | **−180.98 s, −39.6 %, 1.66× faster** |
| user CPU | 183.29 s | 115.00 s | −68.29 s |
| sys CPU | 234.69 s | 149.82 s | −84.87 s |
| files | 11/11 pass | 11/11 pass | — |
| tests | 624 pass | **625 pass** | +1 (net: 1 test replaced, 1 added) |
| 1-min load at start | 5.68 | 4.85 | comparable |

The 39.6 % measured saving sits inside the investigation's predicted 34–42 % band. Total CPU
falls from 417.98 s to 264.82 s (−153.16 s), and the biggest single component is `sys`
(−84.87 s, 36 % of the suite's system time) — the direct signature of one fewer `fork`+`exec`
per Git call.

Both runs report 11/11 files passing, so **the full suite is green before and after**, and
the after-run confirms all 625 tests pass.

---

## 5. Security argument

### 5.1 What the wrapper actually provided

The removed shim was:

```sh
#!/bin/sh
HOME=<iso> XDG_CONFIG_HOME=<iso> GIT_CONFIG_NOSYSTEM=1 exec <real git> "$@"
```

installed as a file named `git` in a directory prepended to the child `PATH`. Its three
effects were: (a) empty `HOME` for Git, (b) empty `XDG_CONFIG_HOME` for Git, (c)
`GIT_CONFIG_NOSYSTEM=1` for Git — each applied to **any** `git` process reachable through
that `PATH`, regardless of what environment the caller passed.

Note what it did **not** provide: `child_environment["GIT_CONFIG_GLOBAL"] = os.devnull`
was already being set before the change and is a **no-op on this machine** —
`GIT_CONFIG_GLOBAL` landed in Git 2.32 and this machine runs **git 2.23.0**
(`git --version` → `git version 2.23.0`). Global-config isolation on the pre-change code
came entirely from the shim's `HOME`/`XDG_CONFIG_HOME`, which is exactly why the
replacement sets both directly and does not lean on `GIT_CONFIG_GLOBAL`.

### 5.2 Direct evidence — `tmp/probe_isolation.py`

The probe plants a caller `HOME` with `user.name`, `user.email`, `core.hooksPath` and a
shell alias, plus a caller `XDG_CONFIG_HOME` with a second `user.name`, then asks the
isolated child environment what Git can still see. It runs against whichever installer
`run_tests.py` exposes, so the same probe ran before and after.

(Both blocks are verbatim probe output except that the long per-run temp-directory prefixes
under /private/var/folders are elided as `...`.)

**Before (shell wrapper):**

```
installer: install_isolated_git_wrapper
caller (no isolation):
  user.name: rc=0 out='CANARY-HOME-NAME'
  core.hooksPath: rc=0 out='.../caller-hooks'
isolated child:
  HOME: rc=0 out='.../caller-home'
  XDG_CONFIG_HOME: rc=0 out='.../caller-xdg'
  user.name: rc=1 out=''
  core.hooksPath: rc=1 out=''
  alias canary: rc=1 out="git: 'canary' is not a git command. See 'git --help'."
  system push.default: rc=1 out=''
  resolved git: rc=0 out='.../runner-scratch/git-wrapper/git'
  git is a shell script?: rc=0 out='0000000    #   !   /   b   i   n   /   s   h'
isolated child, GIT_* stripped by a test:
  user.name: rc=1 out=''
  core.hooksPath: rc=1 out=''
  system push.default: rc=1 out=''
```

**After (environment isolation):**

```
installer: install_isolated_git_configuration
caller (no isolation):
  user.name: rc=0 out='CANARY-HOME-NAME'
  core.hooksPath: rc=0 out='.../caller-hooks'
isolated child:
  HOME: rc=0 out='.../runner-scratch/git-home'
  XDG_CONFIG_HOME: rc=0 out='.../runner-scratch/git-xdg-config'
  user.name: rc=1 out=''
  core.hooksPath: rc=1 out=''
  alias canary: rc=1 out="git: 'canary' is not a git command. See 'git --help'."
  system push.default: rc=1 out=''
  resolved git: rc=0 out='/usr/local/bin/git'
  git is a shell script?: rc=0 out='0000000  312 376 272 276  \0  \0  \0 002 001'
isolated child, GIT_* stripped by a test:
  user.name: rc=1 out=''
  core.hooksPath: rc=1 out=''
  system push.default: rc=0 out='simple'
```

Reading the two side by side:

- **Caller global config is still unreadable** (`user.name`, `core.hooksPath`, the alias:
  all `rc=1` / not-a-command), and it stays unreadable **even when a test strips `GIT_*`
  from its own environment**, because `HOME` and `XDG_CONFIG_HOME` do not start with
  `GIT_` and therefore survive that stripping.
- `git` now resolves to `/usr/local/bin/git`, whose first bytes are `0xcafebabe` (a Mach-O
  universal binary), not `#!/bin/sh`. The interposed process is gone; `git` still resolves
  from `PATH`, which is what the tests require. (The pre-change code reported the
  `Path(...).resolve()`d `/usr/local/git/bin/git` because it had to embed that path in the
  shim; the new code only needs to prove Git is resolvable, so it no longer canonicalizes.)
- **One line differs**, and only one: `system push.default` in the *`GIT_*`-stripped*
  sub-environment. See §5.5.

### 5.3 Property: no init-template hooks from the caller's global config run in children

`test_run_tests.py::RunTestsIsolationTests::test_main_does_not_run_hooks_from_the_callers_global_git_config`
is untouched and passes. It is a real end-to-end test (no `subprocess` mocking): it writes
a global `core.hooksPath` pointing at a `pre-commit` hook that would create a marker file,
plus a global `user.name`/`user.email`; runs `main()` with `os.environ` patched to that
caller `HOME`; the projected child test does `git init` + `git commit --allow-empty`
(`check=True`); and it asserts the marker was never created.

That test also proves the identity path still works end to end: `configured_git_identity()`
resolves `user.name`/`user.email` from the caller's config *before* isolation is installed,
seeds `GIT_AUTHOR_*`/`GIT_COMMITTER_*` (preserved by `SAFE_GIT_BEHAVIOR_VARIABLES`), and the
child's `git commit` therefore succeeds under `check=True` while the hook stays unreachable.

Under the new mechanism this test is *stronger* than it was — when run **inside the suite**,
which is how CI and the pre-commit hook run it. Pre-change, the test's own
`git config --global …` set-up calls resolved `git` from the child `PATH`, i.e. the outer
suite's shim, which overrode `HOME` again; so they wrote into the **outer runner's** isolated
`HOME` instead of the `caller-home` the test builds. Post-change they land in `caller-home` as
the test intends, and the assertion genuinely measures the inner runner isolating a real
caller global config. (Run standalone the test always had its full teeth, because standalone
there is no shim on `PATH`.)

### 5.4 Property: the projected view is still not a Git repository

Unchanged code path (`seal_bare_repository_view` / `seal_bare_repository_views`), and its
tests pass: `test_repository_view_preserves_paths_symlinks_and_ignores` asserts the
projected root's Git marker file holds `GIT_BOUNDARY_MARKER` and that `git -C <view> rev-parse --git-dir`
returns nonzero, plus the same for nested bare-shaped and linked-admin directories;
`test_runner_recurses_from_a_metadata_free_projected_view` runs the projected runner and
asserts the projection has no `.git`. `test_metadata_probe_runs_only_for_directories_with_head_entries`
still pins the probe scope.

### 5.5 Residual difference (the honest caveat)

**Scope:** *system*-level Git config, for *grandchild* Git processes launched by a test that
builds its own environment by dropping every `GIT_*` variable.

Nine call sites in the suite build an environment as
`{name: value for name, value in os.environ.items() if not name.startswith("GIT_")}`
(`automation/tests/test_inspect_workspace_boundaries.py:30` — the shared
`clean_environment()` helper — and six places in `automation/tests/test_run_tests.py`).
That comprehension drops `GIT_CONFIG_NOSYSTEM` along with the local pointers it is aimed at.

- Pre-change, those grandchildren still hit the shim, which re-imposed
  `GIT_CONFIG_NOSYSTEM=1`, so system config was unreadable everywhere.
- Post-change, they run the real binary with no `GIT_CONFIG_NOSYSTEM`, so system config is
  readable — the `system push.default: rc=0 out='simple'` line in §5.2.

This machine's system config is not empty: `/usr/local/git/etc/gitconfig` (via
`git config --system --list --show-origin`) contains `core.excludesfile=~/.gitignore`,
`credential.helper=osxkeychain`, `push.default=simple`, `include.path=~/.gitcinclude`, and
~20 aliases, several of which are `!`-shell aliases.

Why this is acceptable rather than a hole:

1. **Nothing user-specific leaks.** Every `~/`-relative path in that system config
   (`~/.gitignore`, `~/.gitcinclude`) dereferences against the **isolated** `HOME`, because
   `HOME` survives `GIT_*` stripping. Those files do not exist in the empty scratch home, so
   the entries resolve to nothing.
2. **`!`-shell aliases only execute when an alias is invoked.** No test invokes one; the
   probe confirms an alias defined in the caller's *global* config is not even visible.
3. **The direct test children — the boundary the runner actually owns — are unaffected.**
   `GIT_CONFIG_NOSYSTEM=1` is in `child_environment` exactly as before (asserted by
   `test_main_passes_the_isolated_environment_to_each_test`).
4. **No Git version knob can fix it.** The only system-config overrides are
   `GIT_CONFIG_NOSYSTEM` and `GIT_CONFIG_SYSTEM`, both `GIT_`-prefixed, so both are dropped
   by the same comprehension. Restoring the property without a wrapper means changing those
   nine call sites to keep `GIT_CONFIG_NOSYSTEM`.

**Recommended follow-up (deliberately not done here, to keep a security-boundary diff
small):** have those nine comprehensions preserve `GIT_CONFIG_NOSYSTEM=1`. That restores the
property for the whole suite and is a one-line change per site. I did not fold it into this
commit because it edits five tests unrelated to the runner and would obscure the change under
review.

One more incidental note in the same direction: `git config --system --list` ignores
`GIT_CONFIG_NOSYSTEM` on git 2.23 (verified: `GIT_CONFIG_NOSYSTEM=1 git config --system --list`
→ full listing, `rc=0`) because an explicit file selection wins. That is true before and
after the change and is why the new test probes an *effective* `--get` of a system key
rather than `--system --list`.

---

## 6. The `HOME`-semantics question (step 3)

The removed docstring promised: *"Put Git behind a config-isolated wrapper **without
changing other tools' HOME**."* Setting `HOME` in `child_environment` changes it for the
whole test process, not just Git. Nothing in the repository depends on the caller's real
`HOME`. Evidence:

```
$ grep -rn "Path\.home()\|expanduser\|environ\[.HOME.\]\|environ\.get(.HOME.\|getenv(.HOME.\|USERPROFILE" \
    --include='*.py' --include='*.sh' --include='*.yml' \
    automation/ services/ skills/ .github/ templates/ handbook/
automation/tests/test_mine_cochange.py:503:        for marker in ("expanduser", "USERPROFILE", "$HOME", "~/."):
automation/tests/test_check_core_scope.py:494:        content = "target = Path.home() / '.agent'\n"
automation/tests/test_check_core_scope.py:503:            "automation/install.ps1": "$target = $env:USERPROFILE + '/.agent'\n",
automation/tests/test_check_core_scope.py:555:        content = "target = Path.home() / '.agent'\n"
```

(excluding the `GLOBAL_STATE_MARKERS` regex table in `automation/check_core_scope.py`,
which contains those tokens as *patterns*, and excluding `history/`.)

All four hits are **string literals inside fixtures and assertions** for the core-scope
gate's own marker detection — none reads the ambient `HOME`. There is no `Path.home()`,
`expanduser()`, or `os.environ["HOME"]` read anywhere in `automation/`, `services/`,
`skills/`, `.github/`, `templates/`, or `handbook/`.

Every place that *writes* `HOME` writes a self-made fixture directory
(`test_run_tests.py:602`, `:973`, `test_inspect_workspace_boundaries.py:602`), never the
caller's. `configured_git_identity({"HOME": "/caller"})` at `test_run_tests.py:420` is a
mocked-subprocess fixture.

This is in fact the *stated repo rule*, not just a lucky absence: `automation/AGENTS.md`
— "Tracked executables use repository-local state only" — is mechanically enforced by
`global_state_findings()` in `check_core_scope.py`, whose `GLOBAL_STATE_MARKERS` reject
`Path.home()`, `expanduser`, `$HOME`, `~/.`, and `/Users/<name>/` in any tracked
`automation/` or `skills/` executable. So a future tracked executable *cannot* start
depending on the caller's `HOME` without failing the core-scope gate.

There is also a strictly-better-isolation side effect worth flagging to a reviewer, because
two tests change meaning (both still pass — see §4):

- `test_run_tests.py::test_repository_view_preserves_paths_symlinks_and_ignores` sets a
  fixture `HOME` with a global `core.excludesFile`. Pre-change, the wrapper overrode that
  `HOME`, so the fixture was inert and the test's `-c core.excludesFile=/dev/null` override
  was never actually exercised. Post-change the fixture is live and the override is really
  tested.
- `test_inspect_workspace_boundaries.py::test_inherited_git_directory_and_work_tree_are_sanitized`
  sets a fixture `HOME` with a global `core.worktree`. Same story: the scenario the test
  claims to build is now genuinely built.
- `test_inspect_workspace_boundaries.py::test_explicit_canonical_git_executable_binding_is_portable`
  passes `shutil.which("git")` to the inspector as its canonical Git binary. Pre-change,
  inside the suite, that resolved to the **wrapper shell script**; post-change it resolves to
  the real binary, which is what the test name claims to be testing.

The narrowest alternative, were a future consumer to need the caller's `HOME`, would keep the
env-only mechanism and set only `XDG_CONFIG_HOME` plus `GIT_CONFIG_GLOBAL`, accepting that
`$HOME/.gitconfig` is read on Git < 2.32 — which is not acceptable, so the real narrowest
alternative is to pass a per-call `-c` / `--no-...` set to Git, or to reintroduce a wrapper
only for the small number of runner-internal Git calls while leaving test-child calls
environment-isolated. Neither is needed today.

---

## 7. Tests changed, and why none of it is a weakening

`automation/tests/test_run_tests.py`: 34 → 35 test methods (`grep -c "    def test_"` on
`bf6f726` → 34, on the commit → 35).

**(a) Replaced** `test_nested_runner_wrapper_reuses_the_original_git_executable` with
`test_nested_runner_isolation_stacks_no_interposed_git_on_path`.

The old test asserted that a nested runner reused `AGENTFOLD_TEST_REAL_GIT` so it would not
wrap the outer wrapper. That property is about a mechanism that no longer exists; keeping it
would require keeping the shim. The replacement asserts the *same underlying safety
property* — a nested runner never accumulates an interposed `git` — through the new
mechanism, and asserts more than the old one did:

- both installs leave `PATH` **byte-identical to the caller's**;
- `shutil.which("git")` resolves to the same real executable in both, it is executable, and
  it is **not** inside any scratch root;
- **no file named `git` exists anywhere under the scratch tree** (`scratch_root.rglob("git")`
  is empty) — a direct assertion that no shim is planted, which the old test could not make;
- each install gets its **own** empty `HOME`/`XDG_CONFIG_HOME` under its own scratch root
  (`assertEqual([], sorted(second.iterdir()))`).

**(b) Two assertions were changed** in `test_main_passes_the_isolated_environment_to_each_test`.
It previously asserted `child_environment["HOME"] == "/caller/home"` and
`XDG_CONFIG_HOME == "/caller/xdg"` — i.e. it pinned the *old* docstring promise that the
caller's `HOME` is untouched. That assertion is the one thing that cannot survive the change,
by construction. It is replaced by assertions that `HOME` and `XDG_CONFIG_HOME` are exactly
`<scratch>/git-home` and `<scratch>/git-xdg-config` (so provably *not* the caller's), plus a
new assertion that `PATH` equals the caller's `PATH`, whose failure message records that Git
resolves from the caller's `PATH` rather than through an interposed wrapper. The pre-existing
`GIT_CONFIG_GLOBAL == os.devnull` and `GIT_CONFIG_NOSYSTEM == "1"` assertions are untouched.
Net effect on strength: the isolation claim moves from "we did not touch HOME" to "HOME is a
verified-empty scratch directory", which is a stronger claim about the same boundary.

**(c) Added** `test_isolated_child_reads_no_caller_git_configuration` — a new real-Git test
with no `subprocess` mocking. It plants `user.name` in a caller `~/.gitconfig` and
`user.email` in a caller `$XDG_CONFIG_HOME/git/config`, **first asserts the caller
environment really can read both canaries** (so the negative assertions cannot pass
vacuously), then asserts that under the installed child environment both `git config --get`
calls return `rc=1` with empty stdout, that `git config --list --show-origin` mentions
neither caller path, and — guarded, skipped on a machine with no system config — that a
single-valued system-config key readable by the caller is **not** readable by the child.

Nothing was deleted without an equivalent-or-stronger replacement, and the test the task
named as load-bearing
(`test_main_does_not_run_hooks_from_the_callers_global_git_config`) is byte-for-byte
untouched.

---

## 8. Gates and per-property test evidence

**Named isolation tests, run explicitly (post-change working tree):**

```
$ python3 automation/tests/test_run_tests.py -v \
    RunTestsIsolationTests.test_main_does_not_run_hooks_from_the_callers_global_git_config \
    RunTestsIsolationTests.test_isolated_child_reads_no_caller_git_configuration \
    RunTestsIsolationTests.test_repository_view_preserves_paths_symlinks_and_ignores \
    RunTestsIsolationTests.test_nested_runner_isolation_stacks_no_interposed_git_on_path \
    RunTestsIsolationTests.test_main_passes_the_isolated_environment_to_each_test \
    RunTestsIsolationTests.test_runner_recurses_from_a_metadata_free_projected_view

test_main_does_not_run_hooks_from_the_callers_global_git_config ... ok
test_isolated_child_reads_no_caller_git_configuration ... ok
test_repository_view_preserves_paths_symlinks_and_ignores ... ok
test_nested_runner_isolation_stacks_no_interposed_git_on_path ... ok
test_main_passes_the_isolated_environment_to_each_test ... ok
test_runner_recurses_from_a_metadata_free_projected_view ... ok

----------------------------------------------------------------------
Ran 6 tests in 1.072s

OK
```

Mapping to the three required properties:

- Caller's global/system Git config is never read by test children — covered by
  `test_isolated_child_reads_no_caller_git_configuration` (new, real Git, canaries verified
  live first) and `test_main_passes_the_isolated_environment_to_each_test`
  (`GIT_CONFIG_NOSYSTEM`, `GIT_CONFIG_GLOBAL`, `HOME`, `XDG_CONFIG_HOME` on the child env).
- No init-template hooks from the caller's global config run in children — covered by
  `test_main_does_not_run_hooks_from_the_callers_global_git_config`, unmodified, still `ok`.
- The projected view is still not a Git repository — covered by
  `test_repository_view_preserves_paths_symlinks_and_ignores` and
  `test_runner_recurses_from_a_metadata_free_projected_view`.

**Reconciler:**

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

(run with this `RESULT.md` present in the working tree, since the reconciler link-checks
untracked root Markdown too.)

**Core-scope gate:** `python3 automation/check_core_scope.py --staged` exits 1 with exactly
one finding — `core changes require a task/<task-id> branch and matching task folder` —
which is the experimental-branch condition, not a property of this diff. Crucially it
produces **no** `references home environment` finding: `GLOBAL_STATE_MARKERS` in
`check_core_scope.py` reject `Path.home()`, `expanduser`, `environ["HOME"]`, `$HOME`, `~/.`
and `/Users/<name>/` in tracked `automation/` executables, and
`child_environment["HOME"] = str(isolated_home)` matches none of them (the `\benviron\[`
pattern needs a word boundary before `environ`, which `child_environment[` does not have).

---

## 9. What I could not verify

1. **The 13,261-Git-calls figure** is taken from the investigation, not re-measured here;
   counting it would need a counting shim, i.e. exactly the interposed process being removed.
2. **Behaviour on Git ≥ 2.32** is reasoned, not executed: only git 2.23.0 is installed on
   this machine, so `GIT_CONFIG_GLOBAL=/dev/null` was never observed doing anything. The
   change is safe there by construction (it *adds* `HOME`/`XDG_CONFIG_HOME` isolation and
   keeps `GIT_CONFIG_GLOBAL`), but that is an argument, not a test run.
3. **Non-POSIX platforms.** `USERPROFILE` is not set for children, so on Windows a global
   `%USERPROFILE%\.gitconfig` would still be read. The removed wrapper was `#!/bin/sh`, so
   it never worked there either — this is not a regression, but it is also not a fix.
4. **Absolute-path escapes** are still out of scope, as the module docstring already says
   ("This is not a sandbox against deliberate absolute paths").
5. **Wall-clock measurements were taken on a machine with four other agents working**, and
   the advisory /private/tmp/agentfold-bench.lock was not respected end-to-end by every
   participant (§3b). Interleaved A/B pairing is my defence against that; the single
   sequential full-suite numbers in §4 carry the load figures I recorded alongside them and
   should be read as indicative, with §2 and §3c round 2 as the load-robust evidence.
   Concretely: the *same* test file under the *same* arm measured 325.09 s, 214.93 s,
   141.44 s and 144.59 s across one 20-minute window. **Absolute wall times from this session
   are not portable; the ratios are** — 2.0× per Git call and ≈ 1.65× on the long pole came
   out the same under every load I measured. Round 1 of §3c additionally had an ordering bias
   (old arm always first) which I did not notice until after it ran; round 2 corrects it, and
   round 2 is the number I stand behind.
6. **`check_core_scope.py --staged` fails on this branch** — `core changes require a
   task/<task-id> branch and matching task folder`. That is the experimental-branch
   condition, not a property of the change: the run produced exactly that one finding and no
   `references home environment` / repo-local-state finding, which is the part of that gate
   this diff could plausibly have tripped.
7. **Whether closing the §5.5 residual is safe.** I argued that adding
   `GIT_CONFIG_NOSYSTEM=1` to those nine environment comprehensions is harmless, but I did
   not make the change, so I never ran the suite against it.
