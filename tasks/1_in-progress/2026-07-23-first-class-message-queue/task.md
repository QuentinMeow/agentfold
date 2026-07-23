# Make the message queue the first-class interaction surface

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-23, by codex, from the owner's architecture correction in chat
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md`

## Goal

Make `message-queue/` the canonical durable delivery surface for every human action and
every cross-session agent action. Human-facing asks must explain the difference being
judged, give a small concrete example, and point to the full source context; PRs, chat,
tasks, and handovers may surface those asks but may not invent an unqueued one.
Queue filenames must expose whether action blocks now, blocks a named future boundary,
or never blocks.

## Acceptance criteria

- [x] Every live queue message, except folder documentation, uses exactly one
      `blocking-`, `future-blocking-`, or `non-blocking-` filename prefix with defined
      transition semantics.
- [x] Queue templates give a zero-context reader the distinction, a concrete example,
      the unattended outcome, and a link to complete context.
- [x] Root and leaf contracts make `message-queue/` canonical for human↔agent and
      durable agent↔agent action; no PR, chat, issue, or task-only ask is valid.
- [x] The reconciler rejects invalid queue names, prefix/schema contradictions, and a
      blocked task without a reciprocal live immediately-blocking human or agent item.
- [x] Relevant portable and personal skills cannot generate orphan human-review
      questions and instead surface links to queue items.
- [x] The owner's answers about guard modes and review clarity are folded into durable
      design/decision records through the queue lifecycle.
- [ ] Repository checks and an independent adversarial review pass with real evidence.

## Links

- Guardrail design: `docs/designs/risk-tiered-agent-guardrails.md`
- Existing queue-routing decision:
  `memory/decisions/2026-07-22-queue-folders-named-by-who-acts-next.md`
- Related coordination backlog:
  `tasks/0_backlog/2026-07-22-finalize-coordination-write-rules/task.md`
