# Design notes — Prevent false GitHub reauthentication

**Status:** decided

## Problem

The same keychain-backed credential can look invalid inside an agent sandbox and valid
with host access. An instruction-only fix is insufficient because the installed
GitHub-manager skill itself contained login-first advice. The complete research and
choice space are in `docs/designs/codex-github-auth-evidence-guard.md`.

## Options considered

### Option A — Periodic or failure-triggered login

Rejected: it conflates execution-environment failure with credential rejection,
rotates tokens unnecessarily, and does not fix a bad environment-token override.

### Option B — Full access or plaintext environment token

Rejected as the default: it weakens unrelated sandbox/keychain protections or moves a
long-lived secret into process state.

### Option C — Instructions plus a diagnostic

Necessary and portable, but a weak agent can skip either layer.

### Option D — Layered global/repo guidance, diagnostic, rule, and hooks

Chosen. The API control owns the classification; instructions route capable agents;
the user rule forbids agent-initiated login; hooks correct tool interpretation and
reject unsupported final advice. Each layer fails independently and normal human
recovery remains available after authoritative HTTP 401 or confirmed missing setup.

## Chosen

Implement Option D without touching GitHub credentials. Treat hook trust as a
human-visible one-time review, not something the installer bypasses. Keep the
classifier agent-agnostic and install Codex-specific adapters only under Codex home.
The accepted decision is
`memory/decisions/2026-07-22-github-reauth-requires-external-evidence.md`.
