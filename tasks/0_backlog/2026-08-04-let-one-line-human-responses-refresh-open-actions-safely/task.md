# Let one-line human responses refresh open actions safely

**Claimed-by:** unclaimed
**Filed:** 2026-08-04, by codex, from commit `a2310ce6f0104c2235ce2ea322102c7022b0f6d5`
**Parent:** 2026-08-03-plan-multi-worktree-safety-remediation
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-one-line-human-responses-refresh-open-actions-safely.md`; `message-queue/needs-agent/requests/non-blocking-track-github-one-line-human-response-open-actions.md`; `message-queue/needs-agent/requests/non-blocking-triage-github-issue-81-one-line-human-response-open-actions.md`

## Goal

Preserve the rule that a human authors exactly one response-line edit while also keeping
the tracked `message-queue/open-actions.md` projection exact and blocking. The ordinary
hooked commit path should add only the canonical generated projection as a system-owned
companion, without leaking unstaged state or widening the response commit to unrelated
paths.

## Acceptance criteria

- [ ] Editing one live response blank and using an ordinary hooked commit succeeds with
      the exact generated open-action projection in the committed tree.
- [ ] Any unrelated authored companion path or hand-written/stale projection is rejected.
- [ ] Generation reads the active candidate index, honors temporary `GIT_INDEX_FILE`
      values, and does not leak unstaged queue edits.
- [ ] Two linked worktrees prepare independent candidates without changing each other's
      index or worktree.
- [ ] The later folding claim remains a separate lifecycle commit, and merge inheritance
      does not misclassify an already-valid isolated response as newly bundled work.
- [ ] Adopters without the queue receive no generated path, unrelated commits cause no
      digest churn, and provider/CI admission still rejects stale candidates.
- [ ] Focused hook, queue-resolution, open-action, full-suite, core-scope, and reconciler
      checks pass with real output recorded.

## Links

- Concrete reproduction: commit `a2310ce6f0104c2235ce2ea322102c7022b0f6d5`
- GitHub projection: https://github.com/QuentinMeow/agentfold/issues/81
- Open-action generator: `automation/reconcile/reconcile.py`
- Human response contract: `message-queue/AGENTS.md`
