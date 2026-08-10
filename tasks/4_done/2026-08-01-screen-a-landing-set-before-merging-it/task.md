# Screen a set of branches for collisions before any of them merges

**Claimed-by:** claude (session 2026-08-02, branch task/2026-08-01-screen-a-landing-set-before-merging-it)
**Filed:** 2026-08-01, by claude, from task `2026-08-01-stop-human-answers-from-gating-git-edges`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`handbook/git-workflow.md` now tells an agent to "screen a landing set for cross-leg
collisions before merging any of it", and nothing screens it. The trunk went red on
2026-08-01 because a branch was merged while its own checks were already failing, and
because two branches that each passed alone collided once both were in.

Build a new integrate script under `automation/` with three subcommands, stdlib and pure
Git only:

- `plan --trunk REF --leg REF…` — pin every ref to a full object ID, screen each leg for
  trunk drift, build the pairwise textual conflict matrix, and write
  `tmp/integration/<stamp>/manifest.json`.
- `build --manifest PATH` — per leg, in manifest order: a real `--no-ff` merge, **commit
  it**, then `reconcile --check --at-transition merge --branch <leg> --range <prev>...<leg>`
  and `run_tests.py --staged`; the full suite once at the end.
- `verify --manifest PATH` — re-fetch, re-pin every ref, fail on drift, then assert
  `git diff --quiet <new-trunk> <aio-head>`.

Two findings from the design work that the implementation must not rediscover the hard
way. First, the reconciler cannot be run against a *staged* merge: `validate_range_candidate`
reads the committed `_GIT_HEAD_OID`, which during `git merge --no-commit` is still the
pre-merge tip, and it also refuses a candidate carrying staged changes — the two paths are
mutually exclusive, so the merge must be committed first. Second, `plan`'s screen wants
`git merge-tree --write-tree` (Git ≥ 2.38); on at least one machine here the git on `PATH`
is 2.23.0 while the system one is 2.50.1, so it must feature-detect and fall back to real
merges in a scratch worktree. A naive implementation reports every pair as conflicting and
the screen silently becomes noise.

Deliberately out of scope: a `land` subcommand. Its whole body would be `gh` calls, which
fails the Core-admission guardrail; that content is a procedure and now lives in
`handbook/git-workflow.md`. Also out of scope: bisect and delta-debugging failure
attribution — two `git log` calls resolved both real incidents in this repository's
history, and the honest worst case for delta debugging is roughly 81 evaluations ending in
"unattributed".

## Acceptance criteria

- [ ] `plan` writes a manifest with every ref pinned to a full object ID, and refuses a
      leg whose trunk base has drifted.
- [ ] `plan` produces the same conflict matrix with and without
      `git merge-tree --write-tree` available, proven by forcing the fallback.
- [ ] `build` commits each merge before running the reconciler, and its per-leg
      `--at-transition merge --range` invocation exits 0 on a clean set.
- [ ] `build` stops at the first leg whose checks fail, and its report names the two
      commits that bracket the failure.
- [ ] `verify` fails when any pinned ref moved between `plan` and the real merge.
- [ ] `python3 automation/run_tests.py` reports 11/11 files passed.

## Links

- `handbook/git-workflow.md` — the landing procedure and the stacked-branch rule
- `memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md`
- `memory/lessons/automation/green-branches-can-merge-to-red.md`
