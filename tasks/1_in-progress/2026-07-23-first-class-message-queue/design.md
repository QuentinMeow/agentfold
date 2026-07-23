# Design notes — Make the message queue the first-class interaction surface

**Status:** exploring

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

Pending breadth-first audit and adversarial review. The expected direction is Option C
because it addresses both failures: discoverability in filenames and lossless delivery
across PR, chat, task, and agent-session boundaries.

## Core fit (required when changing AgentFold core)

**Agent substitution:** pass — files, links, and deterministic checks work with any agent runtime
**Provider substitution:** not-applicable — the queue contract does not depend on a hosted provider
**Repository substitution:** pass — any adopted repository needs durable human and agent action routing
**User-global writes:** none
**Why AgentFold core:** interaction delivery is a framework lifecycle concern, not personal configuration or product behavior
**Thin adapter:** none
