# Design notes — accelerate the local development feedback loop

**Status:** decided

## Problem

The pre-commit hook ran the complete isolated repository suite for every change. That
made a small service edit pay for unrelated Git-heavy automation tests, while removing
isolation or broadly guessing dependencies would weaken the safety boundary. The fast
path must also be honest about the existing runner: it copies working-tree bytes into
its isolated view even when selection is based on staged paths.

## Options considered

### Option A — keep the full suite at every boundary

This preserves one simple verification boundary, but repeats the roughly four-minute
full-suite cost for service-only milestone commits and leaves agents waiting on tests
that cannot be affected by the change.

### Option B — conservative staged-path selection with full fallback

Keep the full isolated suite as the default. Let the pre-commit hook request a narrow
lane only for ordinary additions or modifications wholly inside a small registered
service dependency map. Any other path, Git status, index type, missing test, malformed
output, or unavailable evidence selects the full suite.

### Option C — general dependency inference and concurrent execution

Infer tests for all repository paths and parallelize them. This could reduce more wall
time, but it expands the correctness surface and isolation assumptions beyond the
evidence needed for the first safe improvement.

## Chosen

Option B. `quote-cli` changes select its test; `quote-api` changes select both its own
test and the dependent CLI test. The runner parses NUL-delimited staged Git output and
checks that every selected path is one regular stage-zero index entry with usable,
non-symlinked working-tree bytes. The full runner remains the no-argument interface for
CI, release evidence, and all fail-closed cases. Suite parallelism and reconciler
redesign remain outside this task.

## Core fit

**Agent substitution:** pass — selection and fallback are executable repository policy independent of any agent runtime
**Provider substitution:** not-applicable — the local hook and runner require no hosting-provider behavior
**Repository substitution:** pass — an adopted repository can keep the fail-closed mechanism and replace the small repository-local service dependency registration with its own known-safe scopes
**User-global writes:** none
**Why AgentFold core:** fast, safe local verification is a repository harness concern shared by agents and humans, not personal configuration or product behavior
**Thin adapter:** none
