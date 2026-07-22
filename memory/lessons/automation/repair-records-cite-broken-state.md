# Consistency checks must exempt files whose job is describing broken state

**Description:** Link-checking the retry queue creates retries-about-retries — repair records legitimately cite dead paths
**Area:** automation
**Last-confirmed:** 2026-07-22
**Review-by:** 2027-01-22

## Failure

During bootstrap verification: a conversation folder missing its handover was deleted
as the fix, the auto-filed retry item still backticked the now-dead path, the link
check flagged the retry item itself, and the next `--file-retries` run filed a retry
about the retry.

## Root cause

A validity check applied to records whose *content is by definition about invalid
state* — repair items (dead subjects), and equally ADRs and history (past paths).

## Rule

Every consistency check declares its exemptions for state-describing record folders:
link-check skips `message-queue/needs-agent/retries/`, `memory/decisions/`,
`history/`, and `templates/`. When adding a check, ask: can a file be *correct* while
violating this? Those folders get exempted up front.
