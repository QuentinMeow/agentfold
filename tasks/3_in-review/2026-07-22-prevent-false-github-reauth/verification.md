# Verification — Prevent false GitHub reauthentication

**Verified:** 2026-07-22 by codex

Only commands actually run and their real output are recorded below.

## Repository tests

```
$ python3 automation/run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
PASS skills/github-auth-guard/tests/test_check.py
PASS skills/github-auth-guard/tests/test_codex_hook.py
PASS skills/github-auth-guard/tests/test_install_codex.py
tests: 5/5 files passed
```

The three guard files ran 7, 6, and 1 tests respectively; all passed.

## Sandbox classification

```
$ python3 skills/github-auth-guard/scripts/check.py --pretty
"classification": "inconclusive"
"configured_host": true
"safe_to_recommend_login": false
exit: 2
```

## Host-access control

The identical command was run with scoped sandbox escalation:

```
$ python3 skills/github-auth-guard/scripts/check.py --pretty
"classification": "authenticated"
"login": "QuentinMeow"
"safe_to_recommend_login": false
exit: 0
```

## Codex command rule

```
$ codex execpolicy check --pretty --rules ~/.codex/rules/github-auth-guard.rules -- gh auth login
"matchedPrefix": ["gh", "auth", "login"]
"decision": "forbidden"

$ codex execpolicy check --pretty --rules ~/.codex/rules/github-auth-guard.rules -- gh auth status
"matchedRules": []
```

## Installed hook canaries

```
$ <PreToolUse payload for: gh auth login> | ~/.codex/github-auth-guard/codex_hook.py
"permissionDecision": "deny"
"Diagnostic classification: inconclusive"

$ <Stop payload recommending: gh auth login> | ~/.codex/github-auth-guard/codex_hook.py
"decision": "block"
"Remove the unsupported GitHub login recommendation"
```

## Existing global GitHub-manager tests

```
$ python3 -m unittest discover -s ~/.codex/skills/global-github-manager/tests -p 'test_*.py'
........
----------------------------------------------------------------------
Ran 8 tests in 0.082s

OK
```

## Review verdicts

- Local security/correctness review: pass — no command reads or prints token values;
  ambiguous failures fail closed as inconclusive, while normal human recovery remains.
- Codex hook activation: pending one-time human trust review in `/hooks`; command rules
  and global instructions are installed independently.
