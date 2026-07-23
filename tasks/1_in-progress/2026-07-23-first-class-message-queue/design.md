# Design notes — Make the message queue the first-class interaction surface

**Status:** chosen

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

Accepted decision:
`memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`.

## Core fit (required when changing AgentFold core)

**Agent substitution:** pass — files, links, and deterministic checks work with any agent runtime
**Provider substitution:** not-applicable — the queue contract does not depend on a hosted provider
**Repository substitution:** pass — any adopted repository needs durable human and agent action routing
**User-global writes:** none
**Why AgentFold core:** interaction delivery is a framework lifecycle concern, not personal configuration or product behavior
**Thin adapter:** none
