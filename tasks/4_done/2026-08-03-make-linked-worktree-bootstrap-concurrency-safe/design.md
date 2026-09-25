# Design — linked-worktree bootstrap concurrency

**Status:** decided

## Problem

Every linked worktree needs ignored instruction and skill adapters in its own checkout,
while all linked worktrees share `core.hooksPath` in the common repository's Git config.
The old installer rewrote that shared config on every run, so simultaneous bootstraps
failed on Git's `config.lock`. It also preserved real adapter files but exited 0 even
though the promised worktree setup was incomplete.

## Options considered

### Option A — add an installer-owned common-directory lock

Resolve `git rev-parse --git-common-dir`, create another lock beside Git's files, and
serialize the entire shared phase. For six worktrees this prevents concurrent writes, but
the installer would own stale-lock detection and cleanup in addition to Git's existing
atomic config lock.

### Option B — converge through Git's existing config lock

Read `core.hooksPath` before writing, return without a write when it is already correct,
and retry a losing write until a read verifies the required value. For six worktrees, one
writer changes the common config and the other five converge through verified reads; no
new lock file or stale-lock protocol is introduced.

## Chosen

Choose Option B. The common-repository phase never claims success until a read observes
`automation/hooks`, and a bounded retry turns temporary `config.lock` contention into a
correct write or no-op. The separate worktree phase creates relative links in the current
checkout and treats another installer's identical link as success. When
`extensions.worktreeConfig` enables a higher-precedence worktree override, that phase
also converges `--worktree core.hooksPath` and verifies the effective value while leaving
an already-correct common config untouched.

A real non-symlink adapter path remains byte-for-byte untouched, but now makes bootstrap
exit 1 with one aggregated repair message instead of printing a warning and exiting 0.
That compatibility change is intentional: exit 0 is the boot contract's signal that the
worktree is ready, so it cannot also mean that an instruction or skill adapter is missing.
Undoing the status change is one return-path edit, but would restore the false-success
state.

The installer preserves a stale generated symlink rather than refreshing it. Conditional
unlink is not available through Python's portable filesystem API, so another actor could
replace a just-observed symlink with a real file before unlink. Preserving the mismatch
costs a manual remove-and-rerun but makes the no-clobber guarantee hold through that race.
Skill adapter links pass directory metadata needed by Windows; `CLAUDE.md` file links do
not.

## Core fit

**Agent substitution:** pass — the setup uses Git and filesystem links, not a named agent runtime.
**Provider substitution:** not-applicable — no hosting-provider state participates in local bootstrap.
**Repository substitution:** pass — any adopted repository using linked worktrees shares Git config while keeping checkout-local files.
**User-global writes:** none
**Why AgentFold core:** the installer establishes the repository's own hooks and portable agent-adapter contract in every checkout.
**Thin adapter:** none
