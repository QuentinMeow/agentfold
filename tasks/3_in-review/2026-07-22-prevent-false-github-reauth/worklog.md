# Worklog — Prevent false GitHub reauthentication

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-22 — prevent-false-github-reauth (codex)

- Reproduced the same credential as `inconclusive` inside the Codex sandbox and
  `authenticated` as QuentinMeow under scoped host access; found matching open Codex
  bug `openai/codex#19262` and verified the mechanism against official Codex/GitHub
  documentation.
- Added a portable, secret-safe classifier that distinguishes API success, HTTP 401,
  environment-token overrides, permissions/SSO, missing configuration, and
  infrastructure uncertainty.
- Added Codex PreToolUse, PostToolUse, and Stop hooks plus a user command rule that
  forbids agent-initiated `gh auth login`; installed global instructions and the guard
  beneath `~/.codex` without reading or changing credential files.
- Removed login-first advice from the installed personal GitHub-manager skill and four
  cached GitHub plugin skills, then repaired the manager's Python 3.7 compatibility
  after its existing tests exposed runtime failures in the default shell.
- Added 14 guard tests to the normal pre-commit/CI test runner, retained the 8 service
  tests, and filed the one-time Codex hook trust review.
- Committed and pushed the implementation, then opened stacked draft PR #5 against the
  design branch; the audited remote diff contained 25 files, 1,501 additions, and 15
  deletions before the publication handover.
