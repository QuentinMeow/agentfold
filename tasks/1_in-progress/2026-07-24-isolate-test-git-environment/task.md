# Isolate repository tests from Git hook state

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-24, by codex, from linked-worktree corruption observed during the layered workspace research session
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Ensure the repository-wide test runner never passes the invoking repository's
hook-local Git environment into test processes. A test that initializes a temporary
repository must be unable to mutate the real repository's config, refs, or worktree
index, including when the runner is invoked by a hook in a linked worktree.

## Acceptance criteria

- [ ] A regression test reproduces inherited `GIT_DIR` / `GIT_INDEX_FILE` contamination
      and fails before the runner is fixed.
- [ ] Every test subprocess receives an environment with all names reported by
      `git rev-parse --local-env-vars` removed.
- [ ] Failure to discover Git's local environment variable names stops the test runner
      instead of silently running contaminated children.
- [ ] The focused regression, repository test suite, reconciler, and a real
      linked-worktree commit probe pass without changing the common repository config,
      refs, or worktree index.

## Links

- `automation/run_tests.py`
- `handbook/git-workflow.md`
