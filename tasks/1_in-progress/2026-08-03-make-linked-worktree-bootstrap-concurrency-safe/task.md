# Make linked-worktree bootstrap concurrency-safe

**Claimed-by:** sol-high bootstrap implementer
**Filed:** 2026-08-03, by codex, from task `2026-08-03-plan-multi-worktree-safety-remediation` and GitHub issue #74
**Parent:** 2026-08-03-plan-multi-worktree-safety-remediation
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-track-github-issue-74-worktree-bootstrap.md`

## Goal

Separate clone-global Git hook configuration from worktree-local ignored adapter setup so
every linked worktree is ready to use without racing sibling installers on shared Git state.
Preserve real user files and avoid user-global or provider-specific configuration.

## Acceptance criteria

- [ ] A linked worktree bootstrap creates that worktree's ignored `CLAUDE.md` and skill
      adapters, and each adapter points into its own checkout.
- [ ] Worktree-local setup does not rewrite shared `.git/config` when `core.hooksPath` is
      already correct.
- [ ] Six concurrent fresh-worktree bootstraps and twelve concurrent repeated bootstraps
      exit 0 without `config.lock` failures and leave identical valid adapters.
- [ ] Bootstrap never clobbers a real non-symlink adapter path and reports one actionable
      error when safe setup is impossible.
- [ ] The boot contract distinguishes once per common repository from once per worktree.
- [ ] Tests use real linked worktrees and assert both common-dir and local Git-dir behavior.

## Links

- Planning task: `2026-08-03-plan-multi-worktree-safety-remediation`
- GitHub projection: https://github.com/QuentinMeow/agentfold/issues/74
- Installer: `automation/install.py`
