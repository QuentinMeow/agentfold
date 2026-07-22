# 2_blocked/ — waiting on a human decision

Only tasks stopped on a `message-queue/needs-human/decisions/` item marked
`Blocking: yes`; each `task.md` links its blocker. When the decision lands, the task
moves back to `1_in-progress/`. Lifecycle: `tasks/AGENTS.md`.
