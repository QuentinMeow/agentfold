# Gate GitHub reauthentication on external evidence

**Status:** decided
**Date:** 2026-07-22
**Decided-by:** codex, under the owner's explicit request for a permanent prevention mechanism
**Description:** GitHub login may be prescribed only after a host-access API control proves rejection or missing setup; sandbox failures remain inconclusive
**Review-by:** 2027-01-18

## Context

The same keychain-backed account failed `gh auth status` inside Codex's restricted
command environment and passed both status and `gh api user` with scoped host access.
The installed personal GitHub-manager skill nevertheless routed agent failures toward
login. Research and alternatives are in
`docs/designs/codex-github-auth-evidence-guard.md`; implementation evidence is in task
2026-07-22-prevent-false-github-reauth.

## Decision

Reauthentication is an evidence-backed terminal classification, not a generic recovery
step. The portable classifier owns that classification: API success is authenticated;
HTTP 401 without an environment override or confirmed missing setup may require human
login; environment-token rejection, permission/SSO denial, and infrastructure
uncertainty do not.

Repository and global Codex guidance route agents through the classifier. A global
Codex command rule forbids agent-initiated login, while optional trusted hooks correct
sandbox output and reject unsupported final advice. The mechanism never reads out a
token and does not weaken the sandbox or replace keychain storage.

## Alternatives considered

- Periodic or failure-triggered login — rejected because it rotates healthy tokens and
  does not repair environment, SSO, scope, or network failures.
- A long-lived environment token — rejected as the local default because it overrides
  stored credentials and moves the secret out of the keychain.
- Full Codex access — rejected because it removes unrelated protection instead of using
  scoped escalation.
- Instructions or a diagnostic alone — retained as layers but insufficient as the sole
  guard because weak agents can skip prose or tools.

## Consequences

Future agents must spend one scoped control check before asking for authentication.
Genuine recovery remains possible for authoritative HTTP 401 or absent setup, but the
human performs the interactive login in a normal terminal. Codex hook trust is a
one-time human review and can be disabled independently; command rules, instructions,
and the classifier continue to provide defense in depth.
