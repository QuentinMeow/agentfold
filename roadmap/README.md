# roadmap/ — desired vs. current

Two documents, one discipline, for humans and agents alike:

- `desired-state.md` — where this repo is going: the target picture, in priority order.
- `current-state.md` — what is actually true today, with a `**Last-updated:**` date.

The **gap between the two files is the backlog's source**: new tasks should trace to a
desired-state line; a task that matches no line means either the roadmap is stale
(update it) or the task is scope creep (question it).

Update ritual: finishing a task that changes reality updates `current-state.md` in the
same change (the session-handover skill includes this step; the reconciler flags a
current-state older than the newest done task). Desired-state changes are one-way
doors — file a timing-prefixed decision in
`message-queue/needs-human/decisions/`. A direct owner request is transcribed into that
item before it is folded; chat is never the only decision record.
