# Queue folders are named by who acts next, not by urgency

**Status:** superseded
**Superseded-by:** `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`
**Date:** 2026-07-22
**Decided-by:** agent (owner sketched urgency-based names, delegated the call)
**Description:** message-queue/ splits into needs-human/ and needs-agent/; urgency is a Blocking: field, never a folder
**Review-by:** 2027-01-22

## Context

The owner sketched urgency-first naming (`message-queue/blocking/human-decisions/`,
`message-queue/future-blocking/clarifications/`) and asked for the clearest possible
scheme, explicitly delegating revision.

## Decision

Top split by **who acts next** — `needs-human/` vs `needs-agent/` — then by message
kind (`decisions/`, `clarifications/`, `reviews/`, `requests/`, `retries/`). Urgency is
a `**Blocking:**` field inside the file.

## Alternatives considered

- **Urgency-first folders** (`blocking/`, `future-blocking/`): urgency is *mutable* — a
  clarification becomes blocking as work approaches it, forcing a file move that breaks
  every link to it. Who-acts-next is stable for an item's whole life.
- **Direction-based** (`from-human/`, `to-human/`): says who wrote it, not whose move
  it is; a human scanning for "what do I need to do" still has to open files.
- **Single `inbox/`**: the name the owner explicitly rejected — guessable by nobody.

## Consequences

A human opens `needs-human/` and sees exactly their to-do list, worst first is not
guaranteed — sorting by urgency requires reading `Blocking:` fields; acceptable at
queue sizes where a human can skim filenames. Escalation is a field edit, never a move.
