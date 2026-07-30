# Fast local test feedback

**Status:** proposal (not an accepted decision — see `docs/designs/AGENTS.md`)
**Measured:** 2026-07-29, by claude, on one macOS host (8 physical / 16 logical cores,
git 2.23.0, `python3` 3.7.6 on `PATH`, 3.9.6 at `/usr/bin`).

## The invariant

Routine local feedback should arrive fast enough that agents keep checkpointing, without
weakening what the repository actually proves before work is shared.

Two properties must survive any change here:

1. **No silent coverage loss.** If something is not run, that must be visible and its
   coverage must happen somewhere named.
2. **Test isolation is a security boundary.** Repository tests must never read the
   caller's Git configuration or run hooks from it (`automation/run_tests.py`).

## Measurement, not inference

| Fact | Value | Source |
|---|---|---|
| Full suite, serial | **219.16s** / 224.72s / 457.15s under load | three runs today |
| `test_reconcile_queue.py` share | **~68-79%** of the suite (298 tests) | per-file timing |
| git subprocess calls per full run | **13,261** | instrumented census |
| git spawns per test (long pole) | **33.3**, ~36.5ms each | instrumented census |
| wall time inside `subprocess.run` | **92-93%** | per-file accounting |
| projection + isolation machinery | **0.21-0.79s (~0.25%)** | instrumented |
| `git init`+`add`+`commit` fixture | 53-79ms | micro-benchmark |
| `shutil.copytree` of a built repo | **17ms** (minimal template 5.85ms) | micro-benchmark |
| CPU split | `sys` **exceeds** `user` in every run | `/usr/bin/time` |

**The suite is `fork`/`exec`-bound.** It is not compute-bound, not disk-bound, and the
isolation machinery is not the cost.

### Ruled out by measurement

- **RAM disk / tmpfs** — 9%; fsync tuning 8%. Git's own test README calls tmpfs "massive",
  but that is Linux advice where `fork` is cheap. Do not build one here.
- **Batching git calls through `sh -c`** — measurably *slower*; the shell is a process.
- **`GIT_CONFIG_NOSYSTEM` / `GIT_CONFIG_GLOBAL` as speed knobs** — 0%. They are isolation
  prerequisites, not optimisations.
- **`cp -Rc` (APFS clonefile)** — 20.3ms vs `copytree` 17.0ms; it pays a spawn.
- **Coverage-based selection (pytest-testmon and kin)** — `coverage.py` cannot see
  subprocesses, and this suite's behaviour lives entirely in git subprocesses.
- **pygit2** — plausibly the largest single win, but it adds a C dependency and
  `automation/AGENTS.md` requires "Python stdlib only, so automation runs on a bare clone".
- **Gating test depth on change *size*** — no credible engineering source does this;
  published risk signals are path- and domain-based. Size may add tests, never subtract.

## Approaches considered

Each was implemented on its own branch and measured. Branches are experiments, committed
with `--no-verify` because the core-scope gate requires a `task/<task-id>` branch.

### E — Isolate child Git by environment, not a shell wrapper (branch exp/e-git-wrapper)

`install_isolated_git_wrapper` wrote a `#!/bin/sh` script named `git` and prepended it to
the child `PATH`, so **every** git call spawned a shell that then `exec`d git. Setting
`HOME`, `XDG_CONFIG_HOME`, and `GIT_CONFIG_NOSYSTEM` directly in the child environment is
identical isolation with one fewer process per call.

*Why the shell existed:* `GIT_CONFIG_GLOBAL` arrived in git 2.32; on git 2.23 that line is
a no-op, so the wrapper's `HOME` was doing the real work. Any replacement must isolate via
`HOME` **and** `XDG_CONFIG_HOME`.

Controlled before/after, both arms under a bench lock at comparable load:

| | before | after |
|---|---:|---:|
| wall | 457.15s | **276.17s** (−39.6%, 1.66×) |
| `sys` CPU | 234.69s | 149.82s (−36%) |
| tests | 624 pass | 625 pass |

Per call, interleaved: 25.39ms → 12.53ms (**2.03×**); load-invariant (2.01× when quiet).

**Residual, open:** nine call sites build child environments by dropping every `GIT_*`
variable, which also drops `GIT_CONFIG_NOSYSTEM`. The old shim silently re-imposed it, so
*grandchild* git processes can now read **system** config. Bounded — `~/`-relative entries
resolve against the isolated `HOME`, and direct test children are unaffected — but it
should be closed in the same change, one line per site.

### B — Shard by test name across cores (prototype)

File-level parallelism is useless here: one file is ~68-79% of the suite, so the Amdahl
ceiling is **1.27-1.46×**, and it was measured at 1.26×. Sharding must be at *test*
granularity. `unittest.main()` accepts test names positionally, so no test file changes.

Balance is not the risk: greedy longest-processing-time packing of real per-test times
splits the long pole **perfectly** 8 ways (max bin 51.9s vs a theoretical 51.9s).

**`test_run_tests.py` is the only file that is not concurrency-safe** — it recursively
invokes the runner and patches `os.environ` (`clear=True`), `HOME`, global git config, and
`PATH`. It fails against copies of *itself*, passes beside other files, and passes
serially. It costs 2.2s, so quarantining it to a serial tail is sufficient.

Measured speedup depends on free cores — 4.10× isolated at 8 workers, 1.40× on a machine
at load 8-11. Efficiency falls from 91% (2 workers) to 51% (8) to 26% (16); the sum of
shard times *grows* with worker count, which is kernel contention. **Budget ~4×, not 8×.**

### E + B combined — the recommended pair

Real committed E code, sharding prototype, one unsafe file quarantined:

| run | wall | shards |
|---|---:|---|
| 1 | **26.03s** | 30/30 pass |
| 2 | **30.11s** | 30/30 pass |

**219.16s → 26-30s (~8×), all 625 tests run, nothing skipped.** With core scope (0.4s) and
the reconciler (~6s), the whole pre-commit gate is **~32-37s**.

### D — Spawn fewer git processes (branch exp/d-spawn-reduction)

Two levers: build the per-test fixture once with a real `git init --template=<empty>` and
`copytree` it (a guard test rebuilds it with real Git and compares byte for byte), and read
blobs through one reusable `git cat-file --batch` instead of a `git show` per artifact,
caching facts keyed on immutable object IDs. Independent of A/C/E — it touches no file they
touch — and it is the only lever that also speeds up **CI**, where local cores do not help.

Measured, both arms under one lock in the same quiet window:

| | before | after |
|---|---:|---:|
| full suite | 219.42s | **166.04s** (−24.3%) |
| git spawns (long pole) | 9,981 | **7,045** (−29.4%) |
| `reconcile --check` | 5.13s / 307 spawns | 4.56s / 214 spawns |

Spawn reductions land where predicted: `git show` **1344 → 33**, fixture `init`+`config`
**687 → 7**, `ls-tree` −521, `merge-base` −311. All 11 files pass; 0 reconciler findings.

**Attribution, measured by interleaving three variants inside one lock hold:** base
91.31s, Lever 1 only 90.91s (**−0.4%, inside the noise floor**), both levers 73.08s
(−20%). **Lever 2 delivered the entire measurable win; the fixture template did not
register**, even though its microbenchmark is genuinely 23ms/test cheaper and external
research ranked it the #2 lever. Its durable value is 680 fewer processes and its guard
test, not seconds. This is a useful correction to the research prior.

Other negative results worth keeping: `rev-parse --git-path` caching returned a fifth of
what raw duplicate counts promised, because almost every call is the first for that test's
repository — the duplicates were across *different* repositories and cannot be shared.
`git init --template=` alone is a rounding error (~6ms of a ~25ms fixture).

### D and E are NOT additive

The wrapper triples what removing a spawn is worth: ≈15ms in-suite versus ≈6ms standalone.
So D's measured −53.4s was earned *on top of* the wrapper tax. Once E removes the wrapper,
D's 2,936 removed spawns are worth roughly 2,936 × 6ms ≈ **18s, not 53s**. Do not add the
two savings together.

The same interaction explains why the long-pole file measures 160.0s inside `run_tests.py`
but 91.3s standalone on identical code. D reached the wrapper conclusion independently,
from the opposite direction, which is the strongest confirmation of E available here.

### A — Select tests by staged input ownership (branch exp/a-input-scope)

Proven safe by experiment: with all 292 projected record files corrupted — and, in the
stronger version, the record trees *deleted* — the suite still passes. So a commit touching
only records cannot change a test outcome.

Replayed over the last 60 non-merge commits: **52 select zero tests**, 8 select 1-4, and
**none** fall back to full. Records-only test step: 0.24s.

*But its own measurement bounds its value:* a `reconcile.py` edit still selects the file
that is 68-79% of the suite. Selection does not help where the work actually is.

### C — Tiered lanes with CI as the complete gate (branch exp/c-tiered)

`.github/workflows/harness.yml` is `on: push:` with no branch or path filter, and its test
step is `if: ${{ always() }}`. **Every push already runs the full suite remotely and
blocks**, so the local full suite duplicated an existing gate. Records-only pre-commit
measured 13.33s, reconciler-bound.

**Rejected for now.** With today's selector an `automation/` change selects **0 of 11**
files, so the file every agent depends on stops being tested locally, and a printed
deferral is not a tracked obligation. At 26-30s the trade buys nothing.

### Rejected: the previously accepted design

A root `agentfold.toml` with routine/final lanes, budget deadlines, content-bound receipts,
risk categories, and auto-filed regression tasks. It produced no measured speedup, and
`tomllib` exists on neither interpreter here (it needs 3.11+), which forced vendoring an
840-line parser. Its deadline mechanism was actively harmful: killing tests mid-run leaks
the ~596 git repositories each run creates, Spotlight indexes them, and each run degrades
the next — the likely mechanism behind recorded finals escalating 309s → 900s.

## Recommendation

Land **E**, then **B**, and **D** on its own track. Keep **A** on the shelf; drop **C**.

Criteria: meets the 60s invariant with margin; loses no coverage; adds the smallest
permanent surface; and introduces no rule that must be kept correct forever.

## Non-goals and trust assumptions

- Not a sandbox. `run_tests.py` already documents that its projection is not a defence
  against deliberate absolute paths; nothing here changes that.
- Numbers are from one host. Ratios reproduced across runs and agents; absolute seconds
  varied up to 2.4× with machine load. Treat ratios as the finding.
- Shard speedup assumes free cores. On a busy machine it degrades toward serial.

## How reality gets verified

- E: the isolation tests must stay green, including
  `test_main_does_not_run_hooks_from_the_callers_global_git_config`, plus a canary probe
  showing caller config is invisible to children.
- B: the full sharded run must pass the same test set as the serial run, repeated to check
  for concurrency-induced flakiness, with `--jobs 1` preserving today's behaviour exactly.
- D: a guard test that rebuilds the template fixture with real Git and compares byte for
  byte, so the shortcut cannot mask a regression in repository creation.

## Open questions

- Whether to close E's nine-site `GIT_CONFIG_NOSYSTEM` gap in the same change
  (recommended) or as a follow-up.
- Whether the reconciler's ~6s becomes the next target once tests are ~26s.

## Resolution

The owner chose Option B and then asked for more than it offered, rejecting 26-30s as a
stopping point and directing that the parts of the tiered-lane experiment worth keeping be
rebuilt rather than merged. That answer is folded into
`memory/decisions/2026-07-30-commit-gate-skips-only-on-proof.md`, which records the durable
rule: a local gate may skip a test only on evidence that running it cannot change the
answer, never on the promise that a later boundary will run it.

## Revision, 2026-07-30: what E, D and A actually delivered, and what is left

E, D and A merged as pull requests 20, 21 and 22. Everything below was re-measured on
merged main rather than carried over, because the earlier numbers described a repository
that no longer exists.

### Re-measured

| | Before | Now | Change |
|---|---|---|---|
| Git spawns per full run | 13,261 | **9,466** | −28.6% |
| Wall time with a Git child alive | 92-93% | **71.2%** | −21pp |
| `git show` calls | 1,344 | 215 | the batching landed |
| Full suite | 219s | ~120s | separate sessions, not comparable |

The spawn census was run twice and produced byte-identical totals, so the counts are
measurements and not estimates. System time still exceeds user time: the suite remains
bound by process creation.

The three poles are `automation/tests/test_reconcile_queue.py` at 67.3%,
`automation/tests/test_check_action_projection.py` at 13.4%, and
`automation/tests/test_inspect_workspace_boundaries.py` at 9.2% — 89.9% between them.

### Two beliefs this revision corrects

**Fixture templating is already harvested, not pending.** 487 of the 603 temp
repositories a full run creates already cost zero spawns, because the two biggest files
build a `.git` skeleton once and copy it. Eliminating every remaining `git init` fixture
would remove ~206 spawns, about 2% of the suite. A micro-benchmark confirms the mechanism
choice: copying the skeleton is 9.58x faster than `git init` plus two `git config`, while
`git init --template=<empty>` is only 1.15x, because the empty template shrinks what
`init` writes and does nothing about the two config spawns that dominate.

**75.9% of spawns come from the code under test, not from fixtures.** Those are the tests
doing their job and cannot be optimized away. Of the remainder, 21.2% is scenario
construction — `add` and `commit` sequences building distinct histories, which one shared
skeleton cannot express — and 2.5% is bare repository creation. This is the ceiling on
every spawn-elimination approach, and it is why the next lever is not spawn elimination.

### The remaining lever is parallelism, measured

Interleaved serial-versus-four-shard A/B inside one session, which is the only comparison
this host supports: **3.27x overall, 3.83x on the long pole** (130.88s to 34.21s), zero
failures. All eleven files are concurrency-safe at process-level sharding, including the
one previously assumed unsafe — seven concurrent executions of it produced no failures,
because `os.environ` is per-interpreter and its `HOME` and `PATH` writes land in per-test
temporary directories.

Running all eleven files concurrently but unsharded takes 80.78s, capped by the single
long-pole process. That number is the argument for sharding below the file: file-level
parallelism alone cannot beat its slowest file.

### Ruled out by measurement: per-test result caching

The idea was to make gate cost scale with what changed rather than with what exists, by
recording what each test reads and skipping any test none of whose inputs moved. It is
the only approach that changes the growth curve rather than the constant, and it is the
one this repository cannot currently build.

- `sys.addaudithook` requires Python 3.8. The interpreter on `PATH` here is **3.7.6**,
  where the function does not exist, and the workflow calls a bare `python3` with no
  version pin, so the floor is whatever the runner provides.
- Even where it exists, `os.stat` and `Path.exists()` emit **no audit event**. A read set
  built this way silently misses "this test asserted the file is absent", which is
  exactly the dependency an ownership table needs.
- Audit hooks are strictly in-interpreter. Across two Git invocations, zero of six audit
  records named any file inside the repository the child was working in. Since 75.9% of
  spawns come from the code under test, the observable unit for them is the directory
  handed to the child, which says only "this test read its own fixture".
- Line-level tracing, the alternative capture mechanism, measured **11.65x** overhead in
  pure Python. `sys.monitoring` would fix that and needs 3.12.

So the mechanism is unavailable, and where available it is unsound in a way that fails
open. Building it anyway would mean a gate that reports success for tests it did not run
and could not prove it was safe to skip, which the repository's own honesty invariant
forbids. Reviving it requires declaring and enforcing a minimum interpreter, and closing
the metadata-read gap — most plausibly by hashing directory listings so an absence
becomes a positive fact about a directory rather than an unobservable one.

### What this means for the growth concern

The concern that motivated this revision is that a fast suite still grows. It does. What
changed is where the growth lands:

- A commit touching no code selects nothing and costs 0.02s. Growth is irrelevant there.
- A commit touching the reconciler selects the file that is 67.3% of the suite. Selection
  is already correct; sharding divides that cost by the core count. Growth is divided,
  not removed.

Nothing measured here removes growth. The honest statement is that the constant is now
small enough that linear growth is affordable for a long time, and that the mechanism
which would remove it is blocked on an interpreter floor this repository has not set.
