# Plan the multi-worktree safety remediation

**Claimed-by:** unclaimed
**Filed:** 2026-08-03, by codex, from `history/conversations/2026-08-03-0730PDT-audit-multi-worktree-safety/handover.md`
**Parent:** none
**Repository scope:** records-only
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-plan-multi-worktree-safety-remediation.md`

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

## Links

- Audit handover: `history/conversations/2026-08-03-0730PDT-audit-multi-worktree-safety/handover.md`
- Coordination rules: `handbook/git-workflow.md`
- GitHub projection: `handbook/github-projection.md`
