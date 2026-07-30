# Lane D — spawn reduction

Worktree /private/tmp/agentfold-exp/d-spawn-reduction, branch
exp/d-spawn-reduction from main @ `bf6f726`. One commit, `e33f925`
(`perf: spawn fewer Git processes in the reconciler and its fixtures`), made with
`git commit --no-verify` — stated as required — to skip the pre-commit suite.

**Headline (whole suite, locked, measured three minutes apart):
219.42 s → 166.04 s, 11/11 files passing.** Git spawns for the long-pole test
file: **9981 → 7045 (−29.4 %)**. Lever 2 delivered essentially all of it;
Lever 1's effect was too small to separate from run-to-run noise.

---

## What changed

### Lever 1 — hoist the per-test git fixture (test code)

`automation/tests/test_reconcile_queue.py` and
`automation/tests/test_check_action_projection.py` ran `git init` plus two
`git config` calls per test — three spawns for a repository that is identical
every time. Both files now build that skeleton once per process with a real
`git init --template=<empty dir>` plus the two `config` calls, and each test
copies it with `shutil.copytree` into its own fresh temp dir (so no test shares
a mutable repository).

The empty `--template` is what makes the copy cheap: the skeleton is 2 files and
4 empty directories instead of ~16 files of sample hooks, `description`, and
the repository exclude file, none of which any test reads.

The shortcut cannot mask a regression in repository creation:
`test_copied_fixture_skeleton_matches_a_real_git_init` (new, in both files) runs
the **real** `git init` path again into a fresh temp dir and compares the tree
listing and every file's bytes against the copied skeleton, then commits through
a copied repository and asserts the fixture identity config travelled with it.

### Lever 2 — batch the reconciler's git reads (production code)

`automation/reconcile/reconcile.py` already had a reusable
`git cat-file --batch` reader, but only the staged-index path with the
invocation snapshot cache active used it. Two changes:

1. **Every blob read goes through the batch reader.** `git_artifact_bytes_at`
   used one `git ls-tree` plus one `git show <rev>:<path>` per artifact; it now
   takes the mode and object ID from the tree entry and reads the bytes through
   the already-open `cat-file --batch` process. The uncached index path likewise
   takes the object ID from the `ls-files --stage` output it was already running
   instead of spawning `git show :<path>`. `git show` spawns: 1344 → 33.
   The `--batch` framing was verified on this git (2.23.0) before relying on it:
   `<oid> <type> <size>\n<payload>\n`, and `<name> missing\n` for an absent
   object (`printf 'HEAD:AGENTS.md\nHEAD:nope.md\n' | git cat-file --batch`).
2. **Facts about full object IDs are cached for the repository, not for one
   invocation.** The file already cached tree entries, parents, and schema
   activations, but only while `_GIT_SNAPSHOT_CACHE_ACTIVE`. What a 40-hex object
   ID contains cannot change, so those caches are now also consulted whenever the
   revision is a full object ID, plus new ones for ancestry
   (`merge-base --is-ancestor`), merge bases, commit availability
   (`cat-file -e`), object kind (`cat-file -t`), and repository metadata paths
   (`rev-parse --git-path`). `scope_immutable_git_caches()` binds them to one
   repository and drops everything — including the open reader — when `REPO`
   changes, which only tests do.

---

## Spawn counts — `automation/tests/test_reconcile_queue.py`, exact

Counted by patching `subprocess.Popen.__init__` in-process, so both fixture and
reconciler spawns are counted with no wrapper process and no measurable
overhead. Deterministic; cross-checked once against a `PATH`-shadowing `git`
wrapper (both reported 683 on the same 20-test subset).

```
BEFORE  Ran 298 tests in 224.954s / OK
        SPAWNS tests=298 total_git_spawns=9981

AFTER   Ran 299 tests in  76.544s / OK
        SPAWNS tests=299 total_git_spawns=7045
```

| git command class | before | after | delta |
|---|---|---|---|
| `add/commit/checkout/... (test fixture)` | 1375 | 1377 | +2 |
| `show (one blob per spawn)` | 1344 | 33 | −1311 |
| `ls-tree -z <oid> -- <path>` | 1316 | 795 | −521 |
| `ls-files` | 789 | 789 | 0 |
| `rev-list` | 716 | 712 | −4 |
| `merge-base` | 695 | 384 | −311 |
| `init + config (test fixture)` | 687 | 7 | −680 |
| `rev-parse (other)` | 671 | 671 | 0 |
| `ls-tree -r (whole-tree listing)` | 654 | 654 | 0 |
| `log` | 596 | 512 | −84 |
| `diff-tree` | 361 | 361 | 0 |
| `diff` | 279 | 279 | 0 |
| `cat-file --batch (reusable reader)` | 205 | 261 | +56 |
| `rev-parse --git-path` | 198 | 122 | −76 |
| `cat-file -e/-t (probe)` | 80 | 73 | −7 |
| `diff-index` | 8 | 8 | 0 |
| `diff-files` | 7 | 7 | 0 |
| **total** | **9981** | **7045** | **−2936 (−29.4 %)** |
| per test | 33.5 | 23.6 | |

The +56 `cat-file --batch` spawns are the reader itself: one long-lived process
per repository replacing hundreds of `git show` runs.

---

## Timings

### Full suite (`python3 automation/run_tests.py`) — the gate that matters

Both runs under the shared lock, three minutes apart, same quiet window. I did
**not** reuse the brief's 219.16 s; I measured the baseline myself and it landed
on 219.42 s, which is a useful confirmation that the two setups agree.

```
BEFORE (base code)                       AFTER (this branch)
tests: 11/11 files passed                tests: 11/11 files passed
test elapsed: 219.42s                    test elapsed: 166.04s
real 219.50   user 89.48   sys 109.86    real 166.12   user 68.87   sys 82.73
```

**219.42 s → 166.04 s = −53.4 s (−24.3 %).**

Per-file, inside the suite (`Ran N tests in Xs` from the same two runs):

| test file | before | after | delta |
|---|---|---|---|
| `test_reconcile_queue.py` | 160.005 s | 116.399 s | −27.3 % |
| `test_check_action_projection.py` | 35.132 s | 23.882 s | −32.0 % |
| `test_inspect_workspace_boundaries.py` | 10.444 s | 11.120 s | +6.5 % (noise) |
| all other 8 files | ~10.7 s | ~11.6 s | noise |

### Long-pole file alone, and which lever delivered what

Three variants interleaved **inside one lock hold** so machine load cannot drift
between the things being compared: base code, Lever 1 only (new fixtures + base
reconciler), and both levers. Two passes.

| variant | pass 1 | pass 2 | mean | vs base | spawns |
|---|---|---|---|---|---|
| base (neither lever) | 90.59 s | 92.02 s | 91.31 s | — | 9981 |
| Lever 1 only | 92.42 s | 89.39 s | 90.91 s | −0.4 % | 9304 |
| both levers | 73.84 s | 72.32 s | 73.08 s | **−20.0 %** | 7045 |

Real output (pass 2, abridged):

```
=== pass 2 BASE (neither lever) ===        === pass 2 BOTH LEVERS ===
Ran 298 tests in 91.604s                   Ran 299 tests in 71.924s
OK                                         OK
real 92.02  user 39.23  sys 49.23          real 72.32  user 30.70  sys 38.43
```

**Attribution: Lever 2 delivered the whole measurable win. Lever 1 did not
register** (see the negative results below).

### Production reconciler (`reconcile.py --check`), under the lock

```
BEFORE  real 5.13 / 5.33 / 4.92   307 git spawns   reconcile: 0 finding(s)
AFTER   real 4.56 / 4.29 / 4.51   214 git spawns   reconcile: 0 finding(s)
```

−30.3 % spawns, ≈ −13 % wall. Lever 2 helps the pre-commit gate itself, not just
the tests: `ls-tree` 121 → 101 and `show` 118 → 45.

---

## Verification

- `python3 automation/tests/test_reconcile_queue.py` → `Ran 299 tests / OK`
  (298 original + the new guard test).
- `python3 automation/run_tests.py` → `tests: 11/11 files passed`.
- `python3 automation/reconcile/reconcile.py --check` → `reconcile: 0 finding(s)`,
  exit 0, with the change **staged** (the reconciler reads the index).
- Behavioural equivalence harness (`tmp/equivalence.py`): loads the base and new
  reconciler side by side and asks both the same questions about one repository
  holding a regular file, an executable, an empty file, CRLF bytes, a non-ASCII
  name, a symlink, a nested directory, a bare directory, absent paths, `.`, a
  trailing-slash path and an empty path, then repeats after an unstaged edit and
  after a second commit, and compares `git_artifact_bytes_at`,
  `repo_artifact_bytes`, `repo_text`, `git_tree_path_entry`, `git_is_ancestor`,
  `parent_merge_base`, `revision_parents`, `git_review_revision_problems` and
  `staged_parent_oids`, values and exception text alike:
  `EQUIVALENCE checks=69 mismatches=0`.

---

## Risk of each change

**Lever 1 (test-only, low risk).** The copied skeleton is byte-identical to what
`git init --template=<empty>` plus the two `config` calls writes, and the guard
test asserts exactly that on every run, so a git upgrade that changes default
config or layout fails loudly instead of diverging silently. The skeleton omits
`hooks/*.sample`, `description`, and the repository exclude file; an empty the repository exclude file has
no effect and nothing reads the other two. Residual risk: the skeleton is built
under `tempfile`'s directory, so its filesystem-dependent config
(`core.ignorecase`, `precomposeunicode`) matches the per-test repositories only
because they come from the same place — a fixture creating repositories on a
different filesystem would need its own skeleton.

**Lever 2 (production code, moderate risk).** The correctness argument is that a
full object ID names immutable content, so an answer about it cannot go stale:

- Cached only when every revision in the key matches `FULL_GIT_OID_RE` (40/64
  hex). `HEAD`, branch names, and the index are never cached by the new paths.
- Only definite answers are cached: `merge-base` return codes 0/1, present
  commits, successful reads. Failures are re-asked, because a missing object can
  be written later in the same process — tests do exactly that.
- Each call site keeps its own `--no-replace-objects` regime; the shared
  primitives take a `replace_objects` flag instead of normalising it away.
- Caches are scoped to one `REPO`; changing it clears them and closes the reader.
  The residual hole: a process that replaced the repository at the same absolute
  path and re-asked about an object ID it had already asked about would get the
  old answer. Nothing in the harness does this (every fixture uses a fresh
  `mkdtemp`), but that is the assumption the scope key rests on. A stronger key
  would add the `.git` inode.
- Error *text* changed in two unreachable-in-practice places: a blob the object
  database cannot return now reports `could not read captured Git object <oid>`
  instead of ``could not read `<path>` at <rev>`` / ``could not read staged Git
  object for `<path>` ``. Both require a corrupt object database — the object ID
  was just read out of the tree or index. No test asserts either string
  (grepped), and the equivalence harness compares exception text.
- The batch reader now stays open while the index is mutated (tests commit
  mid-test). Reading a blob by an object ID a just-run `ls-files`/`ls-tree`
  reported is safe: the object exists, and git resolves exact object IDs by stat
  rather than from a cached listing.

---

## What did not help (negative results)

- **Lever 1 does not show up at whole-file scale.** In isolation the new fixture
  is unambiguously cheaper — a full per-test sequence (fixture, write, `add`,
  `commit`, `rev-parse`) measured on a quiet machine:

  ```
  init+config then add/commit/rev-parse    median= 57.94ms mean= 59.30ms  x229=13.58s
  copytree then add/commit/rev-parse       median= 34.86ms mean= 36.58ms  x229= 8.38s
  init+config then add/commit/rev-parse    median= 60.19ms mean= 61.27ms  x229=14.03s
  copytree then add/commit/rev-parse       median= 36.52ms mean= 37.42ms  x229= 8.57s
  ```

  ≈ 23 ms × 229 repository tests ≈ 5 s expected. The interleaved whole-file runs
  put it at −0.4 s ± ~1.5 s: base 90.59/92.02 s vs Lever 1 only 92.42/89.39 s.
  So the 680 removed spawns are real and the microbenchmark is real, but the
  file-level effect is inside the noise floor and I will not claim it. Lever 1's
  durable value is the guard test and 680 fewer processes, not measured seconds.
- **My first before/after pair was load-inflated and I threw it away.** Under the
  lock at 20:05 the base file measured 193.25/193.49/192.79 s (user 80.7, sys
  105.0); the same code in the same lock at 21:16 measured 90.59/92.02 s (user
  38.4, sys 48.4). The *CPU* time doubled too, so this was not the process being
  descheduled — it is core/SMT contention from other work on the machine
  inflating identical work by ~2×. **The lock alone does not make timings
  comparable on this machine; only variants interleaved inside one hold are.**
  Had I trusted the first pair I would have reported −63 % instead of −20 %.
- **`rev-parse --git-path MERGE_HEAD` caching returned a fifth of what the raw
  count promised** (198 spawns, only 76 removed): almost every call is the first
  one for that test's repository, so there is nothing to reuse. Same shape for
  `merge-base` (695 → 384, not → ~170) and `log --full-history` (596 → 512). The
  duplicate counts I first measured across the whole file were mostly cross-test
  duplicates against *different* repositories, which cannot be shared.
- **Stride-sampled subsets are a trap for before/after work.** Adding one test
  changed which tests `flat[::15]` selects, so subset counts before and after are
  not comparable. Every headline number here is a whole-file or whole-suite run.
- **`git init --template=` alone is a rounding error**: ~6 ms off a ~25 ms
  three-spawn fixture. It matters only because it shrinks what has to be copied.
- **The same file is much slower inside `run_tests.py` than standalone**
  (160.0 s vs 91.3 s on identical base code) and improves more there
  (−43.6 s vs −18.2 s). The runner puts a shell wrapper in front of `git`
  (`install_isolated_git_wrapper`), so every git call pays an extra
  `fork`+`exec`; that both inflates the file and roughly triples what removing a
  spawn is worth (≈ 15 ms in-suite vs ≈ 6 ms standalone). If someone wants
  another double-digit win with no behaviour change, replacing that wrapper
  script with environment variables on the child (`HOME`, `XDG_CONFIG_HOME`,
  `GIT_CONFIG_NOSYSTEM` are all inheritable) is worth measuring — I did not
  touch it because it is the runner's isolation boundary.

---

## What I did not do

- **The two remaining `git show <commit>:<path>` sites**
  (`automation/reconcile/reconcile.py:6079` and `:6177`, the handover
  creation-snapshot readers). They run with `text=True`, whose universal-newline
  translation turns `\r\n` into `\n`; a raw blob read would not, and the
  reconciler has CRLF-sensitive checks, so this is not a byte-identical change
  without reimplementing that translation. Only 33 spawns in the test file, but
  **45 of the production `--check`'s remaining 214** — the largest remaining
  production win, deliberately left.
- **Collapsing `ls-tree -z <oid> -- <path>` into one `ls-tree -r -z <oid>` per
  revision.** 795 of the remaining 7045 spawns are single-path tree reads across
  443 distinct commits, so one full-tree read per commit would remove ~350 more
  spawns (5 %). Not done: it reads and retains every path of every visited tree —
  cheap for a fixture, unbounded for a large repository. A safer variant is to
  promote to a full-tree read only when a second path of the same revision is
  asked for, which caps it at two spawns per revision.
- **The `add`/`commit` fixture churn** (1377 spawns, 20 % of what is left) is
  untouched: each test commits different content, so there is no shared prefix to
  hoist. `git commit -m … <paths>` would fold each pair into one spawn but
  changes staging semantics across 500+ call sites.
- **`test_check_core_scope.py`**: checked as instructed, no change made. It has
  five `git init` literals but the whole file runs in ~1.5 s (it mostly exercises
  pure path predicates over temp directories), so there is no win to take. Same
  for the other files with real `git init` calls
  (`test_inspect_workspace_boundaries.py` ~11 s, `test_run_tests.py` ~1.6 s,
  `test_mine_cochange.py`).
- **Parallelism, RAM disks, `GIT_CONFIG_NOSYSTEM` on its own, `sh -c` batching**:
  out of scope per the brief.

---

## Environment and method

```
Python 3.7.6        git version 2.23.0        8 physical cores, shared
```

Stdlib only, no new dependencies, no new files in the tracked tree (scratch lives
in the git-ignored `tmp/`: `count_spawns.py`, `count_reconcile.py`,
`equivalence.py`, `repro_runner.py`, and the measurement shell scripts with their
logs). Every timed run acquired the shared bench lock at /private/tmp/agentfold-bench.lock and released
it immediately after; no hold exceeded three long-pole runs. The full suite was
run three times in total (one baseline, one after, one that caught the failure
below).

**A failure the suite caught that direct runs did not.** My first guard test
asserted the recorded commit author (`git log --format=%an`) was `Test`. That
passes standalone but fails under `run_tests.py`, which exports the real user's
`GIT_AUTHOR_NAME`, and environment identity overrides repo config — so the first
full-suite run reported `FAIL` for both files I touched. The assertion now checks
`git config user.name` (what the copy actually carries) plus the commit subject.
Reproduced and fixed with `tmp/repro_runner.py`, which drives one file through
the runner's own projection and sanitized environment; the commit was amended and
the suite re-run to 11/11. Worth knowing: `python3 <test file>` is not
equivalent to what the gate runs.
