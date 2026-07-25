# Isolate repository tests from Git hook state

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-24, by codex, from linked-worktree corruption observed during the layered workspace research session
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md`

## Goal

Ensure the repository-wide test runner neither passes the invoking hook's
repository-selecting Git environment into tests nor starts them inside any existing
repository's discovery path. Accidental Git commands must resolve only an explicitly
selected temporary repository, including when the runner starts from a hook in a
linked worktree.

This is process-state isolation, not a filesystem sandbox: test code that deliberately
targets the real repository by an explicit absolute path remains capable of changing it.
The supported baseline is macOS and Linux; Windows keeps the repository's documented
symlink-creation limitation and may require Developer Mode or WSL.

## Acceptance criteria

- [x] A regression test reproduces inherited `GIT_DIR` / `GIT_INDEX_FILE` contamination
      and fails before the runner is fixed.
- [x] Every test subprocess receives an environment with all names reported by
      `git rev-parse --local-env-vars` removed.
- [x] Failure to discover Git's local environment variable names stops the test runner
      instead of silently running contaminated children.
- [x] Every test subprocess starts in one fresh suite view outside the repository with
      Git discovery capped at the scratch root.
- [x] Existing repository-relative test reads continue through a repository-metadata-
      free working tree view, and safe Git identity/noninteractive settings remain
      available.
- [x] Each subprocess executes the projected test file, so `__file__` and ordinary
      repository-relative path derivation stay inside the disposable view.
- [x] Caller global/system Git configuration, hooks paths, and initialization
      templates are unavailable to test subprocesses while resolved caller identity
      values and the caller home used by non-Git tools remain available.
- [x] A test that invokes the repository runner recursively reuses the original Git
      executable instead of stacking wrappers with the parent runner's isolated home.
- [x] One repository projection is materialized for the suite, including every
      discovered ignored/generated test with its sibling support tree, and removed
      when the runner exits.
- [x] Test discovery and support projection do not follow directory symlinks, and no
      projected path can write through a symlink outside the scratch view.
- [x] Ignored support trees prune every case variant of a `.git` file/directory, and
      materialization rejects any additional path containing a Git-metadata component
      on case-sensitive or case-insensitive filesystems.
- [x] Bare-repository-shaped tracked files cannot make the view discoverable, and
      every nested bare-repository-shaped support directory is sealed even when its
      config is absent, its metadata names use case variants, or its object/ref
      directories are symlinks; user-global ignore configuration cannot alter the
      view's contents.
- [x] On macOS/Linux, valid dangling/looping symlinks and nested repositories with
      whitespace-bearing paths project without dereferencing or path normalization.
- [x] The focused regression, repository test suite, reconciler, and a real
      linked-worktree commit probe pass without changing the common repository config,
      refs, or worktree index.
- [ ] [After the preceding PR has merged, this PR's base is stable, and this item becomes waiting, inspect the exact Git range and approve it, request a named change, or reject it before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md)

## Links

- `automation/run_tests.py`
- `handbook/git-workflow.md`
- `memory/known-issues/install-symlinks-windows.md`
