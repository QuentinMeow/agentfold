# Trust the Codex GitHub authentication guard hook once

**Status:** waiting
**Filed:** 2026-07-22, by codex, from task 2026-07-22-prevent-false-github-reauth
**Look-at:** restart Codex, run `/hooks` in Codex CLI, review the three entries that execute `~/.codex/github-auth-guard/codex_hook.py`, then trust them
**Why-you-might-care:** trust activates the Stop hook that mechanically prevents future agents from sending unsupported GitHub reauthentication advice
**If-you-do-nothing:** the global instruction and forbidden command rule still apply after restart, but Codex skips the untrusted PreToolUse/PostToolUse/Stop hooks

**Resolution:** ______ <human: anything here counts as acknowledged>
