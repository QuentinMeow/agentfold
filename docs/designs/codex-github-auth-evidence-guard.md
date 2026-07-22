# Prevent false GitHub reauthentication advice in sandboxed agents

**Status:** implemented on the current task branch; Codex-global hook activation still
requires the user's one-time trust review.
**Accepted decision:** `memory/decisions/2026-07-22-github-reauth-requires-external-evidence.md`

## Invariant

An agent may say that GitHub reauthentication is required only after an authoritative
control distinguishes credential rejection from inability to test the credential.
Sandbox, network, keychain, permission, and SSO failures must not be collapsed into
“expired token.” Diagnostics must not reveal token material.

## What actually failed

The local control experiment produced opposite results for the same saved account:
`gh auth status` failed in the restricted command environment, while the same status
check and `gh api user` succeeded with scoped host access. The credential remained in
macOS Keychain throughout.

This matches an open Codex bug report in which `gh auth status` reports saved and
environment credentials as invalid inside Codex while the same machine and repository
succeed in a normal terminal. That report explicitly classifies the difference as a
runtime/environment regression rather than token invalidity.

## Research evidence

- [Codex sandbox documentation](https://learn.chatgpt.com/docs/sandboxing) says spawned
  tools such as Git inherit the sandbox's filesystem and network limits. Approval is a
  separate mechanism for crossing that boundary.
- [Codex `AGENTS.md` guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
  supports global user instructions and repository-specific instructions. OpenAI's
  customization guidance recommends codifying repeated mistakes and pairing prose
  with enforcement.
- [Codex hooks](https://learn.chatgpt.com/docs/hooks) can add context or deny shell
  calls before execution, inspect failed shell output afterward, and continue a turn
  when its final answer violates a rule. User and project hooks require one explicit
  trust review, and specialized paths can bypass hooks.
- [Codex command rules](https://learn.chatgpt.com/docs/agent-configuration/rules) can
  forbid an exact command prefix outside the sandbox and include inline match tests.
  The global rule prevents agents from initiating the interactive login flow.
- [`gh auth login`](https://cli.github.com/manual/gh_auth_login) normally stores its
  OAuth token in the operating-system credential store. Environment tokens are meant
  primarily for headless automation.
- [`gh auth status`](https://cli.github.com/manual/gh_auth_status) tests known accounts
  and exits nonzero when it finds an issue, but the command cannot prove *why its own
  execution environment* could not complete a valid test.
- [GitHub CLI environment precedence](https://cli.github.com/manual/gh_help_environment)
  defines the GitHub.com and Enterprise token variables that supersede stored
  credentials; the classifier checks their names but never reads out their values.
- [GitHub token lifecycle](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/token-expiration-and-revocation)
  has concrete expiry and revocation causes; OAuth and personal tokens are revoked
  after one year of non-use, not on a monthly login schedule.
- [openai/codex#19262](https://github.com/openai/codex/issues/19262) is the matching
  primary bug report for false invalid `gh auth status` results inside Codex.

## Breadth of approaches

### Reauthenticate whenever a check fails

Simple, but wrong for DNS, sandbox, keychain, scope, SSO, and bad environment override
failures. It needlessly churns credentials and can revoke older OAuth tokens when the
same application, user, and scope combination accumulates too many tokens.

### Put a long-lived token in `GH_TOKEN`

Works in headless automation but moves the secret out of the keychain and silently
overrides saved `gh` authentication. A stale override can create the exact failure and
cannot be repaired by `gh auth login`. This is appropriate for bounded CI credentials,
not the default local-agent fix.

### Give Codex full access

Likely restores keychain/network access but removes unrelated protections. Official
Codex guidance supports scoped escalation and command rules specifically to avoid
broadly expanding the trust boundary.

### Instructions or a skill only

Cheap and portable. They improve a capable agent but can be missed, truncated, or
overridden by more specific text. The installed personal GitHub skill itself contained
login-first advice, demonstrating that prose can encode the bug.

### Deterministic diagnostic only

The classifier separates successful API authentication, HTTP 401, HTTP 403/SSO,
environment overrides, missing configuration, and inconclusive infrastructure errors.
It is secret-safe and agent-agnostic, but a weak agent can skip it.

### Layered instructions, diagnostic, and Codex hooks

Chosen. Global and repository instructions set the rule; the portable classifier makes
the evidence mechanical; a PreToolUse hook blocks premature login commands, a
PostToolUse hook corrects interpretation of sandboxed status output, and a Stop hook
rejects unsupported login advice before it reaches the human.

## Decision table

| Evidence | Classification | May recommend login? |
|---|---|---|
| `gh api user` returns a login | authenticated | no |
| API returns HTTP 401 and no environment override is active | reauth-required | yes |
| API returns HTTP 401 while `GH_TOKEN`/`GITHUB_TOKEN` is active | invalid-environment-token | no; fix override |
| API returns HTTP 403, SSO, or scope denial | permission-or-sso | no |
| no configured host plus GitHub CLI's no-login response | reauth-required | yes |
| DNS, connection, keychain, sandbox, or ambiguous failure | inconclusive | no; retry with host access |

## Installation and trust

The repository owns the portable skill and scripts. Its installer merges a marked
block into the user's global Codex `AGENTS.md`, installs a command rule that forbids
agent-initiated login, merges three hook entries into `hooks.json`, copies the
classifier/hook beneath Codex home, and hardens the installed personal GitHub-manager
skill plus known login-first prerequisites in installed GitHub plugin skills. It never
touches the token or GitHub CLI credential files. Plugin upgrades can restore vendor
text, so the global instruction, command rule, and trusted Stop hook remain the durable
enforcement layers; rerunning the installer re-hardens the cached skills.

Codex intentionally does not run a new user hook until the human reviews its exact
definition. The installer therefore cannot honestly claim full enforcement until the
user trusts it once in `/hooks`. Subsequent tasks inherit the global instruction after
a new Codex session starts.

## Limits and recovery

- A user can disable an unmanaged hook, and some specialized tool paths can opt out.
- Hosted/cloud agents without the local Codex home receive only repository guidance
  and the portable skill.
- Genuine HTTP 401 and truly missing configuration still permit normal interactive
  authentication; the guard prevents false positives, not recovery.
- If the hook misclassifies a final answer, `/hooks` can disable it while the portable
  diagnostic remains available.
