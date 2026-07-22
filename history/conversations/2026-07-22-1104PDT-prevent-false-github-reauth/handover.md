# Handover — prevent false GitHub reauthentication

**Session:** 2026-07-22 11:04–11:29 PDT, codex
**Task:** 2026-07-22-prevent-false-github-reauth
**Mode:** async

## What happened

- Confirmed that the same GitHub credential is inconclusive inside the Codex sandbox
  and authenticated under scoped host access; found the matching open Codex bug.
- Added and globally installed an evidence classifier, Codex instructions, a forbidden
  login command rule, and PreToolUse/PostToolUse/Stop hooks without touching tokens.
- Removed login-first advice from the personal GitHub manager and four cached GitHub
  plugin skills; repaired the manager's existing Python 3.7 failures.
- Added 14 auth-guard canaries to pre-commit and CI, recorded the accepted decision,
  and opened stacked draft PR #5.

## How it works now

A new Codex session loads the global rule that forbids agent-initiated `gh auth login`
and guidance that treats sandbox failures as inconclusive. The classifier permits a
human login recommendation only after authoritative HTTP 401 or confirmed missing
setup. The three hooks are installed but Codex will skip them until their one-time
trust review; the existing account remains authenticated as QuentinMeow.

## Decisions made for you

- [GitHub reauthentication requires external evidence](../../../memory/decisions/2026-07-22-github-reauth-requires-external-evidence.md): use layered instructions, a secret-safe API classifier, a forbidden command rule, and trusted hooks; do not weaken the sandbox or replace keychain storage.

## Needs your attention

- [Codex GitHub auth hook trust](https://github.com/QuentinMeow/agentfold/blob/task/2026-07-22-prevent-false-github-reauth/message-queue/needs-human/reviews/trust-codex-github-auth-guard.md): restart Codex, open `/hooks` in Codex CLI, review the three entries running `~/.codex/github-auth-guard/codex_hook.py`, and trust them once. If you do nothing, the global instruction and forbidden command rule still apply, but the hooks cannot intercept misleading tool output or final advice.
- [Risk-tiered guardrails proposal](https://github.com/QuentinMeow/agentfold/blob/task/2026-07-22-prevent-false-github-reauth/message-queue/needs-human/reviews/risk-tiered-agent-guardrails.md): review the proposed PII/security boundary and the new docs routing contracts. If you do nothing, the design remains proposed and no guardrail implementation begins.
- [Provenance principle wording](https://github.com/QuentinMeow/agentfold/blob/task/2026-07-22-prevent-false-github-reauth/message-queue/needs-human/reviews/provenance-principle-wording.md): decide whether the five instruction-bearing paths and mandatory human review in autonomous mode are the right trust boundary. If you do nothing, the principle stands as written and mechanical enforcement remains backlog work.

## Dead ends

- Repeating `gh auth status` inside the sandbox cannot resolve the failure; it lacks the
  same network/keychain authority as the control.
- Login-first skill text, full Codex access, and plaintext environment tokens were
  rejected as primary fixes because they either repeat the error or weaken security.

## Next steps

Trust the hook once, then review stacked PR #5 before PR #4. After the trust review is
acknowledged, fold the queue item and move the task from in-review to done.

## Deep links

- Task folder: `tasks/3_in-review/2026-07-22-prevent-false-github-reauth/` · Worklog: `tasks/3_in-review/2026-07-22-prevent-false-github-reauth/worklog.md` · Verification: `tasks/3_in-review/2026-07-22-prevent-false-github-reauth/verification.md`
- Pull request: `https://github.com/QuentinMeow/agentfold/pull/5` · Commits: `95c1f3e`, `c9d8f88`, plus this publication handover commit
