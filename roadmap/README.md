# roadmap/ — desired vs. current

Two documents, one discipline, for humans and agents alike:

- `desired-state.md` — where this repo is going: goal entries in priority order, each
  recording who asked for it, when, the owner's words, and whether the owner confirmed it
  (schema: the goal template in `templates/`, mapped by `templates/README.md`).
- `current-state.md` — what is actually true today, with a `**Last-updated:**` date.

The **gap between the two files is the backlog's source**: every task's `## Fit` names the
goal it serves or the clarification asking which goal should; a task that matches no goal
means either the roadmap is stale (add or confirm a goal) or the task is scope creep
(question it).

Update ritual: finishing a task that changes reality updates `current-state.md` in the
same change (the session-handover skill includes this step; the reconciler flags a
current-state older than the newest done task). How `desired-state.md` changes depends on
who is speaking (`memory/decisions/2026-09-04-owner-statements-become-goal-entries.md`):

- An owner statement — in chat, in an answer to a queue item, or in a request document —
  is transcribed directly into a goal entry marked confirmed, because the owner authored
  it; chat is never the only record of it.
- An agent-proposed goal is added as `Confirmed: no` together with a non-blocking
  clarification asking the owner to confirm it.
- Removing or re-prioritising a confirmed goal is a one-way door: file a timing-prefixed
  decision in `message-queue/needs-human/decisions/` first.
