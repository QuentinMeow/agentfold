# Design notes — isolate repository tests from Git hook state

**Status:** decided

## Problem

Git exports repository-local environment variables to hooks. In a linked worktree,
those variables contain absolute paths into the common repository. The current test
runner inherits them into test processes, so a test's otherwise isolated `git init`
and commit operations can target the real repository.

## Options considered

### Option A — clear variables only in the pre-commit hook

This protects the current hook but leaves `automation/run_tests.py` unsafe when invoked
from another Git hook or any caller that already carries repository-local variables.

### Option B — sanitize every test child in the canonical runner

Query Git for its current `--local-env-vars` list once and fail closed if discovery
fails or returns nothing. Remove every returned name and every inherited `GIT_*` name
from a copy of the process environment, then restore only a closed set of identity and
noninteractive behavior settings that cannot select a repository. Run each test file
from a fresh directory outside the repository, verify that Git discovers no repository
there, and set that scratch root as Git's discovery ceiling. Ask Git for the tracked
plus non-ignored untracked paths and copy those entries, preserving symlink objects but
never repository metadata, into one disposable suite view. A deliberately invalid `.git`
marker is added only when the projected files already form a discoverable bare
repository. The check pins `--git-dir=.` so a nested view cannot inherit discovery from
a bare-shaped ancestor; ordinary projected roots remain available for an explicit
`git init`.
The enumeration overrides `core.excludesFile` with the platform null file, so global
Git configuration cannot remove inputs from the view. Repository-relative test reads
keep their prior shape without recursively copying ignored dependency trees or
restoring ambient Git discovery. Because the supported Git baseline predates
`GIT_CONFIG_GLOBAL`, the test `PATH` starts with a disposable wrapper that gives Git
alone an empty home/XDG config and disables system config; non-Git tools retain the
caller's normal home. Resolved caller name/email values are passed through explicit
author/committer environment variables without retaining the configuration that supplied
them. The projected test file—not the corresponding absolute path in the real checkout—
is the child program. Its test directory includes ignored sibling modules and fixtures
without following directory symlinks, and materialization rejects any target path that
would traverse a projected symlink. After materialization, Git's exact pinned
`--git-dir=.` probe checks every non-symlink directory containing a case-folded
`HEAD` entry—the required marker common to Git directory layouts—and seals every
discoverable metadata layout, including bare repositories and linked-worktree admin
directories. Ordinary directories require only the filesystem walk, not one Git
process each. The repository view is materialized once per suite, bounds disk usage to
one projection, and preserves the runner's prior cross-test working-tree semantics
without multiplying repository-sized copy I/O. A recursively invoked runner inherits
the exact projected-root marker; only when that marker resolves to its current
metadata-free repository may enumeration fall back from `git ls-files` to a
non-symlink-following filesystem walk that excludes every `.git` case variant.

### Option C — require each test to clean its own environment

This spreads a security boundary across every test author and allows one forgotten
temporary-repository test to corrupt shared state again.

## Chosen

Option B. The canonical process boundary owns the isolation guarantee, works for every
caller, follows Git's dynamic list, and remains safe if a wrapper truncates that list
because the prefix fallback removes unknown future Git variables too. The closed
behavior allowlist preserves temporary-commit identity and noninteractive remote tests
without retaining repository pointers or executable Git hooks. A validated,
configuration-isolated working-tree projection closes ambient parent-repository
discovery while preserving
relative paths, tracked directories named `tmp`, and even dangling/looping symlinks,
without pretending to sandbox code that explicitly addresses the real repository.
macOS and Linux are the supported baseline. Windows checkouts that materialize real
symlinks retain the existing Developer Mode/WSL limitation recorded in
`memory/known-issues/install-symlinks-windows.md`.

## Core fit

**Agent substitution:** pass — every agent invokes the same repository test runner and receives the same isolation
**Provider substitution:** not-applicable — the behavior is local and independent of a hosting provider
**Repository substitution:** pass — any adopted repository can run Git-using tests from hooks or linked worktrees
**User-global writes:** none
**Why AgentFold core:** test isolation protects the harness's own enforcement and every adopted repository's Git state
**Thin adapter:** none
