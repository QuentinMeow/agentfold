# Make the message queue the first-class interaction surface

**Claimed-by:** codex
**Mode:** async
**Filed:** 2026-07-23, by codex, from the owner's architecture correction in chat
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/future-blocking-continue-first-class-message-queue-review.md`; `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`; `message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md`; `message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md`

## Goal

Make `message-queue/` the canonical durable delivery surface for every human action and
every cross-session agent action. Human-facing asks must explain the difference being
judged, give a small concrete example, and point to the full source context; PRs, chat,
tasks, and handovers may surface those asks but may not invent an unqueued one.
Queue filenames must expose whether action blocks now, blocks a named future boundary,
or never blocks.

After the first human review, redesign the human side as an action-first decision
interface rather than a metadata record. Every actionable file must distinguish what
is true today from what is proposed, compare meaningful choices and consequences,
state an evidence-backed agent recommendation, explain the no-response outcome, and
keep references and tracking details after the decision content.

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
- [x] The full repository test runner passes with real evidence in `verification.md`.
- [x] [After the PR is linked and status becomes waiting, review the queue-ownership invariant, timing prefixes, and enforcement before merge.](../../../message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md)
      The first review requested a human-UX redesign; its exact response and revision
      binding remain preserved in the folding receipt.
- [x] Only `waiting` files appear under “Needs your attention”; not-ready and answered
      records clearly request no action.
- [x] Decision, clarification, and review templates put the human task first, separate
      current from proposed behavior, compare choices symmetrically, give a justified
      recommendation after the comparison, and require no hash or lifecycle editing.
- [x] Every actionable `waiting` human-review file uses the new presentation while its
      target, evidence, lineage, response, and unresolved judgment remain fixed. The
      activation edge permits only deterministic neutral wording and a proven
      post-merge reframe of the same accept/repair/rollback outcomes; the answered
      detector-failure receipt remains byte-for-byte unchanged.
- [ ] [After the repair is published, review whether every human-attention file states the task first, separates current from proposed behavior, explains choices and consequences, gives a justified recommendation, and keeps references and machine records out of the way.](../../../message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md)
      A fresh final independent adversarial review also completes before merge.

## Links

- Guardrail design: `docs/designs/risk-tiered-agent-guardrails.md`
- Existing queue-routing decision:
  `memory/decisions/2026-07-22-queue-folders-named-by-who-acts-next.md`
- Related coordination backlog:
  task `2026-07-22-finalize-coordination-write-rules`
