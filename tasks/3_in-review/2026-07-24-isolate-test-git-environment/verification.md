# Verification — isolate repository tests from Git hook state

**Verified:** 2026-07-24 by codex

Only commands actually run and their real output are recorded here.

## Regression before implementation

```
$ python3 automation/tests/test_run_tests.py
FAILED (failures=2, errors=1)
```

The two failures reported the missing isolation/discovery boundaries. The error was
the preserved Python 3.7-incompatible `Mock.call_args.kwargs` assertion, corrected to
the equivalent `Mock.call_args[1]` access before the production change.

## Focused regression after implementation

```
$ python3 automation/tests/test_run_tests.py
Ran 11 tests in 0.200s

OK
```

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 9/9 files passed
```

The immutable-candidate panel for
`a996c1a02cb23463aef6180bc6e6ae77c5a08379` found that ignored test support
enumeration could copy a linked-worktree `.git` file or nested `.git` directory.
Support discovery now prunes both, materialization rejects metadata-bearing paths,
and the focused 17-test regression passes.

The panel for `8499ed2bb18cd7627c85b292060c91d24fe7b6ba` reproduced the metadata
escape with a `.GIT` case variant on the supported default case-insensitive macOS
filesystem. Both guards now compare path components with `casefold()`, and the focused
17-test regression passes.

The panel for `af4ec99e4b4b2705fd52317347e017c717ed9fdb` found that an ignored
bare-repository fixture below the test directory remained active even without a
`.git` component. The completed projection now seals every bare-shaped directory
without following symlinks, and the focused 17-test regression passes.

The panel for `8a92afcb1883c840d77c92faf57401070b91fe0f` found that bare candidate
detection was case-sensitive and incorrectly required a config file. Detection now
case-folds metadata names and probes every directory with `HEAD` plus `objects` or
`refs`; the focused 17-test regression passes.

The panel for `cd8fd59623eea142cc070be352a4464013b36067` found that pruning
directory symlinks before bare-shape detection hid symlinked `objects` or `refs`.
Candidate names are now captured before symlinks are removed from traversal, and the
focused 17-test regression passes with a symlinked object directory.

The panel for `71aec2ef167c464e6d5ddba4823559ca118749f9` found that a linked-worktree
admin directory with `HEAD` plus `commondir` bypassed the remaining shape catalogue.
The catalogue is gone: Git's exact pinned probe now checks every non-symlink directory.
The focused 17-test regression passes with an external-common-directory fixture.

The panel for `7359bcff849ae30df3dcbb8d647deb9d727fff4d` found that an exact probe
per directory scaled poorly, while a case-variant metadata fixture was not portable to
case-sensitive Linux. The scan now uses a case-folded `HEAD` prefilter and exact Git
probe only for candidates. The canonical fixture and a 100-ordinary-directory probe
regression pass:

```
$ python3 automation/tests/test_run_tests.py
Ran 18 tests in 0.826s

OK
```

A fresh blast-radius review of
`238c00e9d090d831bc2170ac83c8597e3e92b105` blocked publication because the first
repair removed normal config-backed identity, retained repository-size-times-test-count
copy I/O, and omitted ignored/generated discovered tests. Those findings were repaired
in the next candidate.

```
$ python3 automation/tests/test_run_tests.py
Ran 14 tests in 0.428s

OK
PASS automation/tests/test_git_init_probe.py
tests: 1/1 files passed
PASS automation/tests/test_first.py
PASS automation/tests/test_second.py
tests: 2/2 files passed
PASS automation/tests/test_probe.py
tests: 1/1 files passed
```

The first full-suite run after the Git-only-home repair failed the nested-runner
global-hook regression because the inner wrapper selected the outer wrapper as its Git
executable. The runner now carries the validated original executable into nested
invocations.

```
$ python3 automation/tests/test_run_tests.py
Ran 17 tests in 0.835s

OK
PASS automation/tests/test_git_init_probe.py
tests: 1/1 files passed
PASS automation/tests/test_first.py
PASS automation/tests/test_second.py
tests: 2/2 files passed
PASS automation/tests/test_probe.py
tests: 1/1 files passed
```

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 9/9 files passed
```

The next final-candidate review of
`9198f83f356d59b05363eb49f26f91ab86aa2a82` blocked publication because ignored
test support files were incomplete, a discovered path through a directory symlink
could escape the scratch destination, and redirecting the entire child home would
break unrelated toolchains. Those findings were repaired in the next candidate.

```
$ python3 automation/tests/test_run_tests.py
Ran 16 tests in 0.790s

OK
PASS automation/tests/test_git_init_probe.py
tests: 1/1 files passed
PASS automation/tests/test_first.py
PASS automation/tests/test_second.py
tests: 2/2 files passed
PASS automation/tests/test_probe.py
tests: 1/1 files passed
```

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 9/9 files passed
```

## Hook-driven repository suite

```
$ git commit -m 'fix: scope projected repository detection exactly' -m 'Inspect only the candidate Git directory so a nested projected view cannot inherit bare discovery from its parent.' -m 'task: 2026-07-24-isolate-test-git-environment'
pre-commit: core scope
core-scope: pass (2 core path(s), task 2026-07-24-layered-development-workspace; independent review manual; not invoked)
pre-commit: reconciler
reconcile: 0 finding(s)
pre-commit: repository tests
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 9/9 files passed
pre-commit: OK
```

## Real linked-worktree state-preservation probe

```
$ probe_parent=$(mktemp -d /private/tmp/agentfold-linked-probe.XXXXXX)
$ probe_path="$probe_parent/worktree"
$ git worktree add --detach "$probe_path" adf05c43033035fb80e64b1178502d228159d6f5
$ hash_or_missing() { if test -f "$1"; then git hash-object "$1"; else printf '%s\n' missing; fi; }
$ common_config_path="$(git rev-parse --git-common-dir)/config"
$ root_index_path="$(git rev-parse --git-path index)"
$ main_index_path=$(git -C /private/tmp/agentfold-main-20260724 rev-parse --git-path index)
$ isolation_index_path=$(git -C /private/tmp/2026-07-24-isolate-test-git-environment rev-parse --git-path index)
$ probe_index_path=$(git -C "$probe_path" rev-parse --git-path index)
$ probe_config_path=$(git -C "$probe_path" rev-parse --git-path config.worktree)
$ common_config_before=$(hash_or_missing "$common_config_path")
$ probe_config_before=$(hash_or_missing "$probe_config_path")
$ root_index_before=$(hash_or_missing "$root_index_path")
$ main_index_before=$(hash_or_missing "$main_index_path")
$ isolation_index_before=$(hash_or_missing "$isolation_index_path")
$ probe_index_before=$(hash_or_missing "$probe_index_path")
$ refs_before=$(git for-each-ref --format='%(refname) %(objectname)')
$ probe_head_before=$(git -C "$probe_path" rev-parse HEAD)
$ probe_tree_before=$(git -C "$probe_path" rev-parse HEAD^{tree})
$ git -C "$probe_path" commit --allow-empty -m 'probe: verify final linked-worktree test isolation'
pre-commit: reconciler
reconcile: 0 finding(s)
pre-commit: repository tests
tests: 9/9 files passed
pre-commit: OK
[detached HEAD 3cf335d] probe: verify final linked-worktree test isolation
common-config PASS 8a09fa16dc1fe2d6a28d0ac86dea308f3f63a9e6
root-index PASS 7add531eefde2299e83f1f37594261df41f49682
main-index PASS 8d2927fe8816295faccecc14892c47c0e6459d97
isolation-index PASS e9c59a93b502f8a855f2800861948f7817e2d56f
probe-index PASS 5241e739057921a5278fb2d936b4a22efded306a
probe-config PASS missing
all-refs PASS
probe-parent PASS adf05c43033035fb80e64b1178502d228159d6f5
probe-tree PASS 0b9c14aff8ca1a4d364cc2dac0e7e4e91029f7f6
probe-parent-count PASS 1
probe-commit 3cf335dadeb5f4cfc09d28aa3766f856a37eddb8
probe-result PASS
```

The probe hashes were captured after adding the disposable worktree and before its
commit. The expected commit changed only the disposable worktree's detached `HEAD`;
its parent and tree were exact, and its index remained byte-identical.
The final reviewed revision changes only exact projected-root discovery and its
regression/docs; its own hook-driven nine-file suite passed as recorded above.

## Review verdicts (when a review was explicitly run)

The first panel reviewed superseded revision
`006783c5645a9a15df59c791f931087af72d342b`:

- correctness / independent reviewer: block — incomplete successful discovery could leak repository pointers
- contract / independent reviewer: block — truncated discovery and the probe's own index/parent were untested
- blast radius / independent reviewer: block — pre-receive `GIT_QUARANTINE_PATH` survived sanitization

The second panel reviewed superseded revision
`c366a553f7f3ca8826d7b725cad2613cf660d088`:

- correctness / independent reviewer: block — inherited `GIT_CONFIG` could survive the fixed baseline
- contract / independent reviewer: block — the required-name baseline rejected older supported Git versions
- blast radius / independent reviewer: block — repository-root child working directories preserved ambient discovery

The third panel unanimously blocked superseded revision
`c7d05453f43d01e69f1ccd894e059a0be9a8eb99`:

- correctness / independent reviewer: block — an unsafe `TMPDIR` containing a path
  separator and nested in another checkout could defeat the discovery ceiling
- contract / independent reviewer: block — the regression mocked away the ambient
  `os.environ` path used by `main()`
- blast radius / independent reviewer: block — the empty scratch working directory
  broke repository-relative tests and removed safe identity/noninteractive settings

The fourth panel unanimously blocked superseded revision
`bb225a7a36990082051797739d65178eace24148`:

- correctness / independent reviewer: block — dereferencing a looping directory
  symlink recursed until failure
- contract / independent reviewer: block — dereferencing a tracked dangling symlink
  aborted before any test ran
- blast radius / independent reviewer: block — recursive copying also dropped nested
  `tmp` paths and multiplied ignored dependency trees for every test

The fifth panel unanimously blocked superseded revision
`7fad3643712dbee9c154b29d479b6a531534dee9`:

- correctness / independent reviewer: block — `.strip()` corrupted a nested
  repository path ending in whitespace
- contract / independent reviewer: block — recursion failed when an omitted parent
  directory had not yet been created
- blast radius / independent reviewer: block — whitespace/newline paths were
  normalized, and unconditional symlink setup ignored the known Windows limitation

The sixth panel reviewed superseded revision
`971a58e1428248b8fe1214b1c9adda919e3cc2a8`:

- correctness / independent reviewer: block — bare-repository-shaped tracked files
  made the projected root discoverable
- contract / independent reviewer: block — user-global excludes could change the
  repository view
- blast radius / independent reviewer: no blocker found

The seventh panel reviewed superseded revision
`20247d9a8895811fbdafb6c1400f19a7dc4a2eaa`:

- correctness / independent reviewer: no blocker found
- contract / independent reviewer: no blocker found
- blast radius / independent reviewer: block — the unconditional invalid marker also
  prevented an explicit `git init` in an ordinary fresh test root
- panel result: two-to-one no-blocker majority; the dissent was repaired before
  completion

The eighth panel reviewed superseded revision
`adf05c43033035fb80e64b1178502d228159d6f5`:

- correctness / independent reviewer: block — the conditional seal could discover a
  bare-shaped ancestor instead of only the nested candidate
- contract / independent reviewer: no blocker found
- blast radius / independent reviewer: no blocker found
- panel result: two-to-one no-blocker majority; the dissent was repaired before
  completion

The ninth panel reviewed final revision
`4d5f769d99158ae56087ce38b4fa7ef5c8c568fb`:

- correctness / independent reviewer: no blocker found
- contract / independent reviewer: no blocker found
- blast radius / independent reviewer: no blocker found
- panel result: unanimous no-blocker verdict

**Reviewed revision:** 4d5f769d99158ae56087ce38b4fa7ef5c8c568fb

## Reconstructed publication range

```
$ python3 automation/check_core_scope.py \
    --range c05e8002e495e4ee346e685213c48f8d6632fa85...HEAD \
    --branch task/2026-07-24-isolate-test-git-environment
core-scope: pass (2 core path(s), task 2026-07-24-isolate-test-git-environment; independent review manual; not invoked)
```

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

```
$ git diff --check c05e8002e495e4ee346e685213c48f8d6632fa85...HEAD
```

No output; exit status 0.

## Main-recovery review and repair

The three-reviewer panel unanimously blocked the stranded combined revision
`7fa18cade7a1a7aa1cff29645630a1f62ce8c9d0`:

- correctness: tests executed the real checkout path and inherited caller
  global/system Git behavior
- contract: the exact range was not based on `main`, carried two unresolved merge
  reviews, and prematurely activated layered-workspace follow-up coordination
- blast radius: the real checkout path bypassed the disposable view, while retaining
  every full projection multiplied scratch storage by the number of test files

The isolation-specific findings were repaired on a fresh task branch based on
`2372e4824c136af579da5665e6f632ca6f98dd59`.

```
$ python3 automation/tests/test_run_tests.py
Ran 13 tests in 0.341s

OK
PASS automation/tests/test_git_init_probe.py
tests: 1/1 files passed
PASS automation/tests/test_probe.py
tests: 1/1 files passed
PASS automation/tests/test_first.py
PASS automation/tests/test_second.py
tests: 2/2 files passed
```

```
$ python3 automation/run_tests.py
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 9/9 files passed
```
