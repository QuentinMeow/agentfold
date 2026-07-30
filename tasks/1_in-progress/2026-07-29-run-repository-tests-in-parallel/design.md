# Design notes — parallel test shards

**Status:** decided

## Problem

The runner spawns one subprocess per selected test file and waits for each in turn. One
file, `automation/tests/test_reconcile_queue.py`, holds 299 of the suite's 653 test
methods and dominates every lane that selects it, so splitting work per file caps the
speedup at roughly 1.4x no matter how many cores are free. The constraints are that the
suite may use nothing but the Python standard library, that discovery may not cost a
subprocess per file, that one file is not safe to run beside anything else, and that a
sharded run must never quietly execute fewer tests than a serial one.

## Options considered

### Option A — file-level parallelism
Run the existing per-file subprocesses through a pool. Trivial to write and provably
covers the same tests, because the unit of work does not change. Bounded above by the
longest single file, which is 68-79% of the suite's cost: measured ceiling 1.27-1.46x.

### Option B — one subprocess per test method
Maximum balance, no scheduling question at all. Each of the 653 processes re-imports its
test module; `automation/tests/test_reconcile_queue.py` costs 0.51s to import, so this
alone would add roughly five minutes of CPU across the suite.

### Option C — chunked test-method shards over one shared projection
Enumerate test methods statically, group them into chunks, and hand chunks to a pool of
workers. `unittest.main()` already accepts test names positionally, so no test file
changes. Balance is tunable through chunk size, and import cost is amortised over a
chunk rather than paid per test.

### Discovery cost — module import versus source reading
Importing each test module to list its cases is exact but costs a subprocess per file,
which is the cost the task exists to remove. An `ast` walk costs milliseconds for the
whole suite but can be fooled by tests it cannot see in the source.

## Chosen

Option C, with `ast` discovery that fails safe.

**Scheduling.** `shard_plan` reads every selected file, splits each file's test names
into near-equal chunks of about `total / (workers * SHARD_UNITS_PER_WORKER)` names
(floor `MINIMUM_SHARD_TESTS`), and emits the chunks longest-file-first. Six units per
worker is the compromise between tail balance and re-import cost: with 8 workers the
full suite becomes 47 units, the largest file contributing 23 of them, so the long pole
starts first and no worker sits idle waiting for it. A `ThreadPoolExecutor` dispatches in
that order and each thread blocks in `subprocess.run`, so work is pulled dynamically and
a slow chunk cannot strand the others.

**Why a thread pool is safe here.** Threads share mutable state, and this repository has
two pieces of module-global state that would corrupt under them: the persistent
`git cat-file --batch` pipe that `automation/reconcile/reconcile.py` keeps in a module
global, and the direct `os.environ` edits inside
`automation/tests/test_check_action_projection.py`. Neither lives in the parent: the
runner imports no repository module — it does not import the reconciler at all — and the
pool threads only build an argument list, block in `subprocess.run`, and print under one
lock. Every piece of test code, and therefore every piece of that shared state, runs in
its own process. A thread pool inside a test module would be the unsafe shape; a thread
pool that only waits on processes is not.

**Fail-safe discovery.** `discovered_test_names` returns either every `Class.test_method`
in a module or `None`, and `None` means the caller runs that whole file. It returns
`None` for a base class defined outside the file, a `load_tests` function, a class
decorator or metaclass, a three-argument `type` call, `setattr`/`globals`/`vars`, a class
nested inside other code, unparseable source, and a file with no case at all. Methods
inherited from a base class defined in the same file are resolved through a transitive
closure over local bases, so a child case carries its parent's tests, and a plain mixin
that is not itself a case contributes its methods to the case that mixes it in. The
guarantee is tested three ways: unit cases for each fallback trigger, a case that diffs
`ast` discovery against `unittest.defaultTestLoader` for every real test file, and a case
that asserts every discovered name lands in exactly one shard or the serial tail.

**Quarantine as data, not a special case.** `QUARANTINED_TEST_FILES` pairs a path with
the reason it cannot share the machine, and the run prints both on its `serial tail:`
line rather than dropping the file silently. Quarantined files are excluded from the
shard pool and run whole, one at a time, after every shard finishes.

**What the quarantine reason may and may not claim.**
`automation/tests/test_run_tests.py` is the only entry, and the stated reason is the one
thing about it that is verifiable from its source: several of its tests re-run this whole
runner, which now defaults to a worker pool, so sharding it would nest a second pool
inside the first and oversubscribe the machine by a factor nobody chose. The stronger
claim that first motivated the quarantine — that it rewrites process-global HOME, PATH
and Git configuration — is true of the file but is *not* a cross-process hazard: those
writes are per-interpreter, its temporary homes are per-test, and each nested runner
builds its own projection. An independent profiler ran it seven times concurrently
without a failure. The quarantine stays because nesting pools is a real effect and the
file is a small part of a run, but the printed reason now says only what was checked.

**Sweep for other unsafe files.** Every other test file was checked for `os.environ`
mutation, `os.chdir`, module-attribute patching, and fixed non-temporary paths. No test
file in the repository calls `os.chdir`; every write goes to a `tempfile` directory; and
no test writes into the projection that all shards share, so concurrent readers of the
one projection built by `materialize_repository_view` are safe. `mock.patch` and
`os.environ` edits are process-local and therefore harmless once each shard is its own
process. The one fixed shared path in the suite is the deliberately invalid scratch root
in `automation/tests/test_run_tests.py`, which `validate_scratch_root` rejects before
anything touches the filesystem, so it never exists to be contended.

**Cost of the tail.** The quarantine is cheap: the whole file runs in 3.4s on an idle
machine against an eight-worker run of 37-46s, so the serial tail is under a tenth of
the run and lifting the quarantine would not change the headline. That is the reason to
leave it in place rather than spend the risk budget on removing it.

**Default worker count.** `os.cpu_count()` reports 16 on this machine, which is logical
CPUs; there are 8 physical cores. The suite spends more system than user time, so it is
bound by process creation and Git calls; simultaneous-multithreading siblings share one
core's execution resources and add contention rather than throughput for that shape of
work. `default_worker_count` therefore asks the platform for physical cores — `sysctl -n
hw.physicalcpu` on Darwin, unique physical-id/core-id pairs from the kernel's cpuinfo
file on Linux — and falls back to half the logical count, floored at two, where neither
answer is available. The probe runs only when `--jobs` is absent.

**Output.** Shard output is captured and written as one block under a lock, so no
traceback can be cut in half by another worker. A passing shard prints nothing unless
`--verbose` asks for names; a failing shard prints its whole `unittest` report, so a
sharded run names exactly the tests a serial run names. Per-file `PASS`/`FAIL` lines, the
`tests: X/Y files passed` summary, and the exit code keep their old shape and meaning.

**One worker is the old runner.** `--jobs 1` takes the original loop: one subprocess per
file, inherited stdio, and an argument vector of exactly the interpreter and the test
path. A unit test asserts that vector has no third element.

## Core fit

**Agent substitution:** pass — the runner is a plain Python entry point invoked by a Git hook and CI, with no agent runtime in the path; any agent that can run a shell command gets the same shards and the same exit code.
**Provider substitution:** not-applicable — nothing here talks to a model or hosting provider; the only external programs are `git` and a platform core-count probe.
**Repository substitution:** pass — any adopted repository whose suite is dominated by one large test file needs test-granular sharding for the same reason, and the shard planner reads only discovered test files and the standard library, with no AgentFold-specific naming.
**User-global writes:** none
**Why AgentFold core:** The tracked runner is the harness's own quality gate: the pre-commit hook and CI both call it, so its wall time is the cost every adopter pays per commit. Making it use the cores already present is a property of the shared mechanism, not of one person's machine, and it writes nothing outside the repository and a temporary directory.
**Thin adapter:** none
