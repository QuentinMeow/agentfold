# Design notes — Make the message queue the first-class interaction surface

**Status:** decided

## Problem

PR #4 asked the owner to judge terms such as “assurance profile,” “template-first,”
and several security evidence roles without explaining their differences or linking
each question to its source. Those asks existed only in the PR body after the original
generic queue review had been resolved. Current contracts require surfaced queue items
to appear in replies, but do not require the converse: every human ask to originate as
a queue item.

## Options considered

### Option A — Improve prose only

Tell agents to write clearer questions while leaving PRs and chat as independent action
channels. This is cheap but another agent can still omit context or lose the ask.

### Option B — Prefix queue files only

Add visible delivery prefixes without changing ask ownership. This improves scanning,
but an excellent filename cannot help when the question never enters the queue.

### Option C — Queue-owned actions with channel projections

Make one live queue file own each pending action. Other channels may summarize and link
it, while templates require a distinction, example, unattended outcome, and full-context
pointer. Enforce delivery prefixes and structural contradictions mechanically.

## Chosen

Option C. It addresses both failures: discoverability in filenames and lossless
delivery across PR, chat, task, and agent-session boundaries.

The path encodes three independent properties: who acts next in the actor folder, what
kind of action it is in the leaf folder, and when it blocks in the filename prefix.
`blocking-*` stops a named boundary now; `future-blocking-*` stops only at a named future
date, event, or transition; `non-blocking-*` never stops work and names the safe
unattended outcome. The filename is canonical, so no `Blocking` field can drift.

PRs, issues, chat, tasks, and handovers are projections. They may summarize and link a
live queue item, but cannot originate a pending durable action. A task declares its
live queue actions explicitly. `2_blocked` broadens from human decisions to any
reciprocally linked `blocking-*` human or agent dependency; a task stays in progress
while an active agent is repairing that dependency.

Human messages compare meaningful dispositions, show a concrete example, state the
unattended result, and link the durable source. This structure constrains delivery and
evidence, not how a future agent completes the work.

## Hardening after independent review

The first adversarial pass found that authority also requires conservative parsing and
portable adoption:

- Queue evidence is read from visible CommonMark, never fenced examples or HTML
  comments; angle-bracket link destinations preserve valid paths containing spaces.
- Standard message leaves have specialized schemas, while any repository may add a
  one-level typed leaf that inherits the actor's generic schema.
- Handover projection enforcement activates from a repository-local schema and exact
  legacy folder, not an AgentFold calendar date.
- Unclaimed backlog tasks have reciprocal, explicitly typed non-blocking pickup
  messages; ordinary follow-up requests may still link active tasks.
  Task status enforces start/review/complete boundaries; Git admission names external
  boundaries such as merge and scopes them to the task being admitted.
- A review is unanswerable while its artifact is pending. A waiting review binds to
  exact file bytes or full Git object ids, and the response repeats that revision;
  mutable PR URLs remain navigation only.
- Every newly added handover must exactly project the complete live human queue.
  Existing records remain stable, so later queue resolution does not rewrite history.
- Reconciler retries aggregate by full check/subject identity, use collision-safe names,
  and refresh a marked machine projection without overwriting actor status or notes.

The live queue owns unresolved delivery state even though its background stays
elsewhere. The correcting ADR is
`memory/decisions/2026-07-23-unresolved-queue-delivery-state-is-not-regenerable.md`.

Accepted decision:
`memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`.

## Core fit

**Agent substitution:** pass — files, links, and deterministic checks work with any agent runtime
**Provider substitution:** pass — any provider can forward branch, immutable diff, and reached-transition context into the canonical local reconciler
**Repository substitution:** pass — any adopted repository needs durable human and agent action routing
**User-global writes:** none
**Why AgentFold core:** interaction delivery is a framework lifecycle concern, not personal configuration or product behavior
**Thin adapter:** canonical=automation/reconcile/reconcile.py; optional=yes; policy=none; writes=repo-only

The registered `.github/workflows/harness.yml` adapter only maps GitHub event context
to those canonical arguments; it owns no queue policy.
