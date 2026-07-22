# Prevent agents from prescribing false GitHub reauthentication

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-22, by codex, from chat after draft PR #4 publication
**Parent:** none

## Goal

Make “run `gh auth login`” a last-resort conclusion backed by an authoritative
probe, never an inference from a sandboxed `gh auth status` failure. Ship a portable
diagnostic for any agent, plus persistent Codex guidance and hooks, without weakening
the sandbox, exposing tokens, or replacing secure keychain storage with plaintext.

## Acceptance criteria

- [ ] WHEN a GitHub check cannot access the network or credential store, THE SYSTEM
      SHALL classify the result as inconclusive and SHALL NOT prescribe login.
- [ ] WHEN GitHub accepts the current credential, THE SYSTEM SHALL report the active
      account without printing the token.
- [ ] WHEN a Codex agent attempts `gh auth login` without confirmed invalid credentials,
      THE SYSTEM SHALL block the command and direct the agent to the diagnostic.
- [ ] Persistent Codex and repository guidance SHALL require an escalated control check
      before claiming expiry or asking the human to authenticate.
- [ ] The existing personal GitHub-manager skill SHALL no longer recommend login merely
      because an agent lacks access to keychain-backed authentication.
- [ ] Automated tests and a real authenticated check SHALL pass without exposing a
      credential.

## Links

- OpenAI Codex issue `openai/codex#19262` — sandboxed `gh auth status` false invalid
- OpenAI Codex sandbox, hooks, and `AGENTS.md` documentation
- GitHub CLI authentication and token-expiration documentation
