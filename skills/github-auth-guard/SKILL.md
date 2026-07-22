---
name: github-auth-guard
description: Diagnose GitHub CLI authentication without confusing sandbox, network, keychain, environment-token, permission, or SSO failures with expired credentials. Use whenever gh authentication fails or an agent considers gh auth login.
---

# GitHub auth guard

Reauthentication is a conclusion, not a generic recovery step. A failed check from a
sandbox cannot establish that the credential itself failed.

## Required workflow

1. Do not print or request a token. Check only whether `GH_TOKEN`, `GITHUB_TOKEN`,
   `GH_ENTERPRISE_TOKEN`, or `GITHUB_ENTERPRISE_TOKEN` is present; values are secret
   and the host-appropriate variables override stored credentials.
2. Run the secret-safe classifier:

   ```bash
   python3 skills/github-auth-guard/scripts/check.py --pretty
   ```

3. Follow its classification:

   | Classification | Meaning | Action |
   |---|---|---|
   | `authenticated` | GitHub accepted the credential | continue |
   | `inconclusive` | sandbox, network, keychain, or unknown failure | retry the same check with scoped host access; never prescribe login |
   | `invalid-environment-token` | an overriding environment token got HTTP 401 | remove or replace the override; login cannot fix it |
   | `permission-or-sso` | GitHub returned an authorization failure | fix permission, scope, or SSO |
   | `reauth-required` | GitHub returned HTTP 401 for stored auth, or no host is configured | a human may authenticate once |

4. In Codex, an inconclusive result requires a sandbox-escalated retry. Pair the
   classifier with a real API control (`gh api user`) rather than repeating only
   `gh auth status`.
5. Suggest or run `gh auth login` only when `safe_to_recommend_login` is `true`.

## Permanent Codex guard

Install user-global guidance and PreToolUse/PostToolUse/Stop hooks with:

```bash
python3 skills/github-auth-guard/scripts/install_codex.py
```

This writes only under the selected Codex home, preserves existing instructions and
hooks, installs a user rule that forbids agent-initiated `gh auth login`, and patches
the installed personal GitHub-manager skill away from login-first advice. Codex
requires the human to review and trust a new hook once in `/hooks`; the hook is skipped
until then, while the command rule remains independently testable.

## Boundaries

- The hook is defense in depth, not a complete security boundary; some specialized
  tool paths may not emit hooks.
- Other agents still get the repository contract and this portable diagnostic.
- Never switch to plaintext token storage or full sandbox access merely to avoid a
  scoped credential-store approval.
