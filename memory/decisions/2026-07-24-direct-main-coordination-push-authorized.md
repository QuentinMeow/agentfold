# The stacked-review coordination sequence may be pushed directly to main

**Status:** decided
**Date:** 2026-07-24
**Decided-by:** human (explicit queue answer recorded in commit 9e2c04a)
**Description:** The prepared lifecycle-only coordination sequence may be pushed directly to main before publishing the three dependent pull requests
**Review-by:** 2027-01-20

## Context

AgentFold's [Git workflow](../../handbook/git-workflow.md) requires live queue state,
task claims and status, owner decisions, and handovers to land directly on `main`.
The owner had requested sequential implementation PRs but had not explicitly
authorized the separate shared-branch mutation needed to make their canonical action
state truthful first.

The prepared sequence was audited as coordination-only. It replays the detector answer
through its original lifecycle, publishes the current task/review states, claims the
layered task, and preserves a handover; it contains no reviewed-system implementation.

## Decision

Codex may push the prepared coordination-only sequence from
`codex/coordination-publication-v2` directly to `origin/main`, then incorporate that
base into the three task branches with merge commits and publish their pull requests
bottom-up. The authorization does not permit implementation code, task-branch
rewrites, pull-request merges, or unrelated direct-main changes.

## Alternatives considered

- Put the coordination sequence in another pull request — rejected because the live
  queue and task state would remain stale until that PR merged, contradicting the
  repository's explicit coordination lane.
- Leave `origin/main` unchanged — rejected because the dependent PRs would expose
  branch-local task and queue state that another session could not safely discover.

## Consequences

The exact coordination history may now be pushed before the implementation PRs are
opened. The implementation remains review-gated in its task branches, merge order
remains bottom-up, and later shared-main mutations outside this recorded scope require
their own authority.
