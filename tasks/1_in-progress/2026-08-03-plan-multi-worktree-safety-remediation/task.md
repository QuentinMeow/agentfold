# Plan the multi-worktree safety remediation

**Claimed-by:** codex (planner)
**Filed:** 2026-08-03, by codex, from `history/conversations/2026-08-03-0730PDT-audit-multi-worktree-safety/handover.md`
**Parent:** none
**Repository scope:** records-only
**Queue actions:** none

## Goal

Turn the multi-worktree safety audit into a minimal set of independently reviewable core
fixes. This parent task owns the decomposition, GitHub issue projections, dependency order,
and publication map; each behavior change remains in its own child task and pull request.

## Acceptance criteria

- [ ] Every confirmed audit finding maps to an existing task, a newly filed child task, or
      an explicitly deferred GitHub issue with a safe unattended outcome.
- [ ] Each new GitHub issue links a canonical repository action and carries the provider
      source binding required by `handbook/github-projection.md`.
- [ ] Every implementation pull request includes its task, plan, design, worklog, and real
      verification evidence.
- [ ] The dependency order keeps independent fixes parallel and makes any stack explicit.
- [ ] No fix depends on an unreviewed direct write to the default branch.
- [ ] The durable design covers task claim, independent and overlapping edits,
      shared-state refresh, pause/takeover, process/worktree/machine loss, prerequisite and
      stacked changes, combined integration failure, merge, and cleanup with one disposable
      acceptance scenario per cycle.
- [ ] The architecture assigns one authority and one recovery ceiling to durable work
      intent, Git change sets, live session observations, and integration runs; no
      external product or derived viewer silently becomes a second source of truth.
- [ ] The verification plan separates deterministic gates, fault-injection scenarios,
      held-out agent evaluation, independent refutation, shadow operation, canary
      promotion, and rollback, and every new check requires observed-red evidence.

## Fit

**Serves:** G9 — Several coding agents develop this repository in parallel, see each other's tasks, resume after an interruption, and stop later pull requests from re-resolving the same refactor conflict
**Today:** the development cycles are designed (pull request #94), but none of the five acceptance experiments from the owner's request document has run and no operations manual exists.
**Fit:** aligned — the task decomposes the owner's 2026-08-31 request into independently reviewable core fixes, which is the design half of G9.

## Links

- Audit handover: `history/conversations/2026-08-03-0730PDT-audit-multi-worktree-safety/handover.md`
- Coordination rules: `handbook/git-workflow.md`
- GitHub projection: `handbook/github-projection.md`
