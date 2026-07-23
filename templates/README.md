# templates/ — every file schema lives here

The single source of truth for file formats. To create any item, **copy its template
and fill the blanks** — never write one from memory, never restate a field list in
another doc (link here instead). To change a format, change the template and the
matching reconciler check in the same commit.

| Template | Creates a file in |
|----------|-------------------|
| `task/` (five files) | `tasks/<status>/<task-id>/` |
| `queue/decision.md` | `message-queue/needs-human/decisions/` |
| `queue/clarification.md` | `message-queue/needs-human/clarifications/` |
| `queue/review.md` | `message-queue/needs-human/reviews/` |
| `queue/request.md` | `message-queue/needs-agent/requests/` |
| `queue/retry.md` | `message-queue/needs-agent/retries/` |
| `handover.md` | `history/conversations/<timestamp>-<slug>/` |
| `memory/fact.md` | `memory/facts/` |
| `memory/adr.md` | `memory/decisions/` |
| `memory/lesson.md` | `memory/lessons/<area>/` |
| `memory/known-issue.md` | `memory/known-issues/` |
| `service/AGENTS.md` | `services/<new-service>/` |

Placeholders look like `<this>`; every `**Key:**` line shown is required unless marked
optional. The reconciler (`automation/reconcile/reconcile.py`) validates required keys
on real files and skips this folder.

Every live queue filename starts with exactly one delivery prefix. `blocking-` means a
named current task, transition, or operation cannot proceed; `future-blocking-` means
work may continue only until a named date, event, or transition; `non-blocking-` means
the message never stops work and records the safe unattended outcome. The filename is
the canonical delivery class. Each queue template shows the one matching timing block
to retain; do not add a second `Blocking` field.

`task/task.md` lists its live dependencies in `Queue actions`. `handover.md` projects
open human queue items in delivery order; it never originates an action.
