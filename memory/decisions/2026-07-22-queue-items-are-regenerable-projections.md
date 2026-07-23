# Queue items are regenerable projections, not sources

**Status:** superseded
**Date:** 2026-07-22
**Decided-by:** human (directed in chat; transcribed by agent — chat leaves no trace)
**Description:** A message-queue item only summarizes and links state that lives elsewhere; it can always be regenerated, so deleting or rewriting one is always safe
**Review-by:** 2027-01-18
**Superseded-by:** `memory/decisions/2026-07-23-unresolved-queue-delivery-state-is-not-regenerable.md`

## Context

The queue rules already made items self-contained, one-screen, and deleted-on-resolve,
but nothing said *why* deletion is always safe or stopped an agent from writing design
content that exists nowhere else into a queue file. The human framed the intended model
in chat: a queue message is like a retryable API call — disposable and regenerable,
because the durable background and artifacts live in the task folder, `memory/`, or the
code, and the message carries only the summary the reader needs to act.

## Decision

A queue item is a projection of durable state that lives elsewhere, plus links to it.
Lose the file, and it can be rewritten from its sources. The one exception: a human
answer written into the file is unique until folded into docs and an ADR — which is why
folding precedes deletion in the resolution ritual. Stated in
`message-queue/AGENTS.md`; writing-side guidance in `handbook/decision-guide.md`.

## Alternatives considered

- Amend `handbook/principles/files-as-messages.md` — principles are near-immutable and
  this is a clarification, not a reversal; the leaf contract is the cheaper right home.
- Leave it implicit — the failure mode (queue files accreting unique content, making
  deletion lossy) is exactly the kind of drift this repo writes rules against.

## Consequences

Agents put durable background in the task's `design.md` or `memory/` and link it from
the queue item. Revisit if a queue ever needs items that legitimately carry unique
state beyond a pending human answer.
