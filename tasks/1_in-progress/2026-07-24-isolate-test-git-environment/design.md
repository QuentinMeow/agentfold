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

Ask Git for its current `--local-env-vars` list once, remove every returned name from a
copy of the process environment, and pass that clean environment explicitly to each
test subprocess. Fail closed if Git cannot provide the list.

### Option C — require each test to clean its own environment

This spreads a security boundary across every test author and allows one forgotten
temporary-repository test to corrupt shared state again.

## Chosen

Option B. The canonical process boundary owns the isolation guarantee, works for every
caller, follows Git's own dynamic list rather than a stale hand-maintained subset, and
is directly regression-testable.

## Core fit

**Agent substitution:** pass — every agent invokes the same repository test runner and receives the same isolation
**Provider substitution:** not-applicable — the behavior is local and independent of a hosting provider
**Repository substitution:** pass — any adopted repository can run Git-using tests from hooks or linked worktrees
**User-global writes:** none
**Why AgentFold core:** test isolation protects the harness's own enforcement and every adopted repository's Git state
**Thin adapter:** none
