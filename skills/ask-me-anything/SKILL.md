---
name: ask-me-anything
description: Answer any question about how AgentFold works, why it is designed this way, or where to find something. Use when a human or agent asks "how do I…", "where does … live", "why is … like this", or wants a guided tour.
---

# Ask me anything (about AgentFold)

You are the tour guide. Answer from the repo's own documents, always linking the
source — never answer from memory alone, and never paraphrase at length what a link
can say (`handbook/principles/progressive-disclosure.md`).

## Routing table

| Question is about | Answer from |
|-------------------|-------------|
| What is this repo / where do I start | `README.md` (humans) / root `AGENTS.md` (agents) |
| Why a design is the way it is | `handbook/principles/<principle>.md`, then the ADRs in `memory/decisions/` |
| What has been designed but not accepted or implemented | `docs/designs/` |
| How to ask a human / leave durable agent work | `message-queue/AGENTS.md` + `templates/queue/` |
| How work is tracked | `tasks/AGENTS.md`; worked example in `tasks/4_done/` |
| What happened in past sessions | `history/` handovers |
| What the project knows / has decided | `memory/index.md`, then the linked entries |
| Where the project is heading | `roadmap/desired-state.md` vs `current-state.md` |
| How quality is enforced | `automation/AGENTS.md` + `handbook/principles/systems-over-instructions.md` |
| Git / branches / rollback | `handbook/git-workflow.md` |
| What GitHub issues, comments, and reviews force into the queue | `handbook/github-projection.md` |
| Adopting this in another repo | `handbook/adoption-guide.md` |
| A file format | the matching file in `templates/` |

## Answer contract

1. Lead with the answer in 2–4 plain sentences — assume no prior context.
2. Link every claim to its source file; offer the deep dive, don't inline it.
3. If two documents disagree, say so and file it in
   `message-queue/needs-agent/retries/` — a doc conflict is a broken invariant. Link
   that canonical item from any task, handover, chat, or external report that mentions
   the pending repair.
4. If the answer isn't in any document, say that, answer from reasoning, and propose
   where it should be written down. If the proposal must survive this session, file
   the agent action in the queue rather than leaving it only in the answer.
5. If an answer creates or surfaces a pending human action, link its live queue item.
   The item must briefly explain how the choices or interpretations differ, give a
   concrete example, state the safe result if unattended, and point to the full
   context; copy its schema from `templates/queue/`.

## Queue timing

Delivery prefixes, what each one means, and what evidence a boundary supplies are owned
by `message-queue/AGENTS.md` — read it rather than answering a timing question from
memory. The queue is canonical for all pending human actions and durable cross-session
agent actions; every other channel is only a linked projection.
