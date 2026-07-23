# Is sensitive-data recovery correctly separated from prevention and exceptions?

**Status:** waiting
**Filed:** 2026-07-23, by codex, from task `2026-07-23-first-class-message-queue`
**Action:** Confirm the incident-recovery boundary and sequence, or identify a missing recovery obligation.
**Full context:** `docs/designs/risk-tiered-agent-guardrails.md`
**Blocks at:** transition:start task:2026-07-22-universal-guard-mode-configuration
**Until then:** The proposal remains documentation only; unrelated work may continue.
**Look-at:** `docs/designs/risk-tiered-agent-guardrails.md`, “Exceptions and recovery”
**Why-you-might-care:** Deleting one Git file does not undo credential or private-data disclosure across remote copies and logs.
**If-you-do-nothing:** Guardrail implementation waits at its start boundary; the current recovery sequence remains a proposal.

## Context

Prevention decides whether content may cross a boundary; an exception authorizes a
narrow crossing before it happens. Recovery begins after data may already have escaped
and therefore cannot retroactively make the guard successful.

## Differences

- **Credential recovery:** revoke or rotate first, then clean history and add a
  regression fixture.
- **Private-data recovery:** contain access and inventory every exposure surface before
  coordinated deletion or history rewriting.
- **Normal retry:** appropriate only when disclosure has not occurred and the candidate
  can be repaired locally.

## Example

After an API key reaches a remote branch, deleting the file in a new commit is not
enough. Rotate the key, then inspect clones, forks, CI logs, artifacts, mirrors, and host
caches; rewrite history only as one part of containment.

**Your review:** ______
