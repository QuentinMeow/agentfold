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
| How to ask the human / file a question | `message-queue/AGENTS.md` + `handbook/decision-guide.md` |
| How work is tracked | `tasks/AGENTS.md`; worked example in `tasks/4_done/` |
| What happened in past sessions | `history/` handovers |
| What the project knows / has decided | `memory/index.md`, then the linked entries |
| Where the project is heading | `roadmap/desired-state.md` vs `current-state.md` |
| How quality is enforced | `automation/AGENTS.md` + `handbook/principles/systems-over-instructions.md` |
| Git / branches / rollback | `handbook/git-workflow.md` |
| Adopting this in another repo | `handbook/adoption-guide.md` |
| A file format | the matching file in `templates/` |

## Answer contract

1. Lead with the answer in 2–4 plain sentences — assume no prior context.
2. Link every claim to its source file; offer the deep dive, don't inline it.
3. If two documents disagree, say so and file it in
   `message-queue/needs-agent/retries/` — a doc conflict is a broken invariant.
4. If the answer isn't in any document, say that, answer from reasoning, and propose
   where it should be written down.
