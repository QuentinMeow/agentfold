# Bind task-branch pushes to observed remote tips

**Claimed-by:** unclaimed
**Filed:** 2026-08-03, by codex, from task `2026-08-03-plan-multi-worktree-safety-remediation` and GitHub issue #76
**Parent:** 2026-08-03-plan-multi-worktree-safety-remediation
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-bind-task-branch-pushes-to-observed-tips.md`; `message-queue/needs-agent/requests/non-blocking-track-github-issue-76-explicit-lease.md`

## Goal

Replace ambiguous bare `--force-with-lease` publication guidance with a provider-neutral
task-branch publisher bound to the exact remote object ID observed during planning. A
sibling worktree refreshing shared remote-tracking refs must never widen that lease.

## Acceptance criteria

- [ ] Restack publication supplies `--force-with-lease=refs/heads/<branch>:<expected-oid>`
      or an equivalent explicit expected-OID transaction.
- [ ] The expected OID is captured before rewriting and is not refreshed immediately before
      push or after rejection.
- [ ] Default-branch targets, deletion targets, zero-OID leases, and malformed task branch
      names are refused before any network mutation.
- [ ] A rejected lease reports the observed conflict and never retries automatically.
- [ ] A disposable-remote test proves an intervening sibling update remains intact even
      after another worktree fetches it.
- [ ] Documentation names the exact observation that supplies the expected OID.

## Links

- Planning task: `2026-08-03-plan-multi-worktree-safety-remediation`
- GitHub projection: https://github.com/QuentinMeow/agentfold/issues/76
- Publication rules: `handbook/git-workflow.md`
