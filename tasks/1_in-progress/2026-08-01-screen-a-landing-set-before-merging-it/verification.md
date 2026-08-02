# Verification — Screen a set of branches for collisions before any of them merges

Everything below is real output. Where a run printed more than is quoted, the omission is
marked `[... n lines ...]`; nothing is paraphrased and nothing is reconstructed from
memory. The end-to-end runs use a throwaway clone of this task branch under the session's
scratch root, so the tool, the reconciler and the test runner are all the ones this branch
ships, and the legs are real branches carrying real commits.

## 1. The environment that makes the fallback necessary

```
$ which -a git
/usr/local/bin/git
/usr/bin/git
$ git --version
git version 2.23.0
$ /usr/bin/git --version
git version 2.50.1 (Apple Git-155)
```

The Git on `PATH` predates `merge-tree --write-tree` by fifteen releases. Every run below
that does not say otherwise used it.

## 2. A real cross-leg collision, screened

Two branches off the same trunk, each adding twenty-three lines to `docs/AGENTS.md` — one
at the top, one at the bottom, so they never touch the same region. This is the shape of
the 2026-08-01 incident recorded in
`memory/lessons/automation/green-branches-can-merge-to-red.md`: a finding that exists on
neither branch.

```
### each leg is green on its own
legA: reconcile: 0 blocking finding(s)
legB: reconcile: 0 blocking finding(s)

### plan: no textual collision anywhere in the set
$ python3 automation/integrate.py plan --trunk main --leg legA --leg legB --out tmp/integration/collide
integrate: git: git version 2.23.0
integrate: conflict probe: worktree (fell back: usage: git merge-tree <base-tree> <branch1> <branch2>)
  clean    main + legA
  clean    main + legB
  clean    legA + legB
integrate: manifest: /private/tmp/claude-501/-Users-quentinmiao-code-ai-harness/e94d07c4-c07c-4f08-b5d5-847ba3aad3fe/scratchpad/verify-clone/tmp/integration/collide/manifest.json
integrate: 3 pair(s) screened, 0 colliding, 0 leg(s) behind trunk
plan exit=0
```

`build` then found what `plan` structurally cannot: the two legs merge cleanly and the
merged tree is over budget.

```
$ python3 automation/integrate.py build --manifest tmp/integration/collide/manifest.json
[... 30 lines of the staged test lane for leg 1 and leg 2 ...]
no discovered test file can be affected by the staged change
tests: 0/0 files passed
test elapsed: 0.12s
integrate: committed 3860e61d2aca (parents 8eb8942c7da4 d87683dbfde5)
integrate: reconciler: /private/tmp/claude-501/-Users-quentinmiao-code-ai-harness/e94d07c4-c07c-4f08-b5d5-847ba3aad3fe/scratchpad/verify-clone/tmp/integration/collide/workspace/automation/reconcile/reconcile.py --check --at-transition merge --branch legB --range 8eb8942c7da43fc150f9f71f6ce5cf708a5f3436...d87683dbfde5b06d323bcff01d3f56b8cd9d6993
[agents-budget] docs/AGENTS.md: 61 lines exceeds the 60-line budget
    fix: move depth into a linked doc (handbook/principles/progressive-disclosure.md)
reconcile: 1 blocking finding(s)
integrate: leg 2 of 2 (legB) failed at the reconciler
integrate:   bracket base  8eb8942c7da43fc150f9f71f6ce5cf708a5f3436  the integration head before this merge
integrate:   bracket leg   d87683dbfde5b06d323bcff01d3f56b8cd9d6993  legB, the tip merged in
integrate:   bracket merge 3860e61d2acae083d739a74754919649598dbdc4  the merge commit the gate rejected
integrate:   workspace /private/tmp/claude-501/-Users-quentinmiao-code-ai-harness/e94d07c4-c07c-4f08-b5d5-847ba3aad3fe/scratchpad/verify-clone/tmp/integration/collide/workspace
build exit=1
```

Each leg is 38 lines on its own, under the 60-line budget; merged they are 61. The failure
belonged to no branch, the real reconciler caught it at the merge, and the report names the
three commits a reader needs.

## 3. A clean set, built green

Two more legs off the same trunk, one line each.

```
$ python3 automation/integrate.py plan --trunk main --leg legC --leg legD --out tmp/integration/clean
integrate: git: git version 2.23.0
integrate: conflict probe: worktree (fell back: usage: git merge-tree <base-tree> <branch1> <branch2>)
  clean    main + legC
  clean    main + legD
  clean    legC + legD
integrate: 3 pair(s) screened, 0 colliding, 0 leg(s) behind trunk
plan exit=0

$ python3 automation/integrate.py build --manifest tmp/integration/clean/manifest.json
build exit=0
[... leg 1 ...]
integrate: leg 2 of 2: merging legD (2963fa4914d0) into 7f8931f5185c
integrate: staged tests: .../workspace/automation/run_tests.py --staged
tests: 0/0 files passed
integrate: committed c1dd67260676 (parents 7f8931f5185c 2963fa4914d0)
integrate: reconciler: .../workspace/automation/reconcile/reconcile.py --check --at-transition merge --branch legD --range 7f8931f5185cbd5011993cb6ad59d4367e2b336c...2963fa4914d0d7ec5ffb91a9a6e2904beda3f145
reconcile: 0 blocking finding(s)
integrate: full suite: .../workspace/automation/run_tests.py
tests: 13/13 files passed
integrate: build: 2 leg(s) merged, head c1dd672606761759b6639d45b6881f6e2d2e5c2b
integrate: record: .../tmp/integration/clean/build.json
integrate: keep .../tmp/integration/clean/workspace until verify has run; it is what holds the merge commits
```

The per-leg `--at-transition merge --range` invocation exits 0 on a clean set, and the full
suite runs once, at the end, against the integrated head. The two `.../` elisions above
replace the same scratch prefix quoted in full in section 2.

## 4. `verify` before the landing, after it, and under drift

```
### before the merges land
$ python3 automation/integrate.py verify --manifest tmp/integration/clean/manifest.json
integrate: main at 73b4a167b7af differs from the integrated head c1dd67260676
  docs/AGENTS.md
verify exit=1

### after landing legC then legD for real, in manifest order
integrate: main at 33b861bc7781 has the tree the build produced at c1dd67260676
verify exit=0

### after one more commit on legD, screened evidence no longer describes it
integrate: drift: legD moved from 2963fa4914d0 to 8df729f4985f after it was screened
integrate: 1 ref(s) drifted; what landed is not what was screened
verify exit=1
```

## 5. The same matrix with and without `merge-tree`, forced both ways

By this point the trunk has moved past legA and legB, so the refusal fires first:

```
$ python3 automation/integrate.py plan --trunk main --leg legA --leg legB --out tmp/integration/behind
integrate: drift: legA branched at 73b4a167b7af, which main has moved past (33b861bc7781)
integrate: drift: legB branched at 73b4a167b7af, which main has moved past (33b861bc7781)
integrate: 2 leg(s) are behind main; update them, or pass --allow-behind-trunk to screen them anyway
plan exit=1
```

Screened anyway, once by really merging under Git 2.23 and once by `merge-tree` under Git
2.50, the two runs are compared field for field:

```
$ python3 automation/integrate.py plan --trunk main --leg legA --leg legB --allow-behind-trunk --conflict-probe worktree --out tmp/integration/probe-worktree
integrate: git: git version 2.23.0
integrate: conflict probe: worktree (forced by --conflict-probe worktree)
  COLLIDES main + legA: docs/AGENTS.md
  COLLIDES main + legB: docs/AGENTS.md
  clean    legA + legB
integrate: 3 pair(s) screened, 2 colliding, 2 leg(s) behind trunk
plan exit=1

$ PATH=/usr/bin:$PATH python3 automation/integrate.py plan --trunk main --leg legA --leg legB --allow-behind-trunk --conflict-probe merge-tree --out tmp/integration/probe-merge-tree
integrate: git: git version 2.50.1 (Apple Git-155)
integrate: conflict probe: merge-tree (merge-tree --write-tree answered the probe)
  COLLIDES main + legA: docs/AGENTS.md
  COLLIDES main + legB: docs/AGENTS.md
  clean    legA + legB
integrate: 3 pair(s) screened, 2 colliding, 2 leg(s) behind trunk
plan exit=1

### the two manifests, compared field by field
probe:   worktree | merge-tree
git:     git version 2.23.0 | git version 2.50.1 (Apple Git-155)
matrix identical: True
legs identical:   True
```

And forcing the capability that is not there reports one line and the "cannot run" status,
never a finding:

```
$ python3 automation/integrate.py plan --trunk main --leg legA --allow-behind-trunk --conflict-probe merge-tree --out tmp/integration/forced
integrate: drift: legA branched at 73b4a167b7af, which main has moved past (33b861bc7781)
integrate: --conflict-probe merge-tree was forced but usage: git merge-tree <base-tree> <branch1> <branch2>
plan exit=2
```

The same equivalence is asserted machine-independently by
`test_the_same_matrix_comes_back_without_merge_tree`, which patches in a shim that refuses
`merge-tree --write-tree` exactly as Git 2.23 does, so the fallback is exercised even on a
machine whose Git is new enough never to need it.

## 6. The repository's own gates

```
$ python3 automation/run_tests.py
[... 12 files ...]
PASS automation/tests/test_integrate.py
[... ]
tests: 13/13 files passed
test elapsed: 191.12s
```

The task's acceptance criterion says `11/11`. That number was written when the tree held
eleven discovered test files; it held twelve before this branch and thirteen with
`automation/tests/test_integrate.py` added. The criterion is read as "the full suite
passes", and it does — no file is skipped or excluded to reach it.

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)

$ python3 automation/check_core_scope.py
core-scope: pass (5 core path(s), task 2026-08-01-screen-a-landing-set-before-merging-it; independent review manual; not invoked)
```

The ownership-table registration narrows the staged lane to the new test rather than
falling back to everything:

```
$ git add automation/integrate.py && python3 automation/run_tests.py --staged
test lane: staged
test reason: every staged path maps to its registered test owners
staged paths: 1
  automation/integrate.py -> test_integrate.py
selected test files:
  automation/tests/test_integrate.py
skipped test files: 12 (no staged path owns them); the complete suite still runs on every push
[... 12 names ...]
test elapsed: 23.34s
```

The commit that carries the tool passed the installed pre-commit hook with no `--no-verify`:

```
tests: 3/3 files passed
test elapsed: 134.77s
pre-commit: OK
```

## 7. What is proved end to end, and what is not

- **End to end, against the real gates**: `plan` on real branches under both Git versions;
  `build` merging, committing, and driving the real `run_tests.py --staged`, the real
  reconciler at `--at-transition merge`, and the real full suite; the first-failure report
  on a real reconciler finding; all three `verify` outcomes on a really landed set.
- **Unit-tested with stub gates** (22 tests in `automation/tests/test_integrate.py`): the
  ordering and hand-off that only a stub can observe — that the reconciler is handed a
  committed two-parent merge with a clean index, that the staged lane is handed the
  uncommitted merge with the leg's paths in `git diff --cached`, that the third leg is
  never merged once the second fails, that a gate exiting 2 is reported as "cannot run"
  rather than as a finding.
- **Not verified**: `verify --fetch`, which is the only code path that touches a network,
  is not exercised by any run here. No test and no run above uses a remote.
- **Not verified**: nothing here proves the screen's behaviour on a repository using
  SHA-256 object ids, or on a Git older than 2.23.
