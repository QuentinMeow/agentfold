# Worklog — project only the human actions that still await the human

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — file the unresolved-projection task (claude)

- Filed from chat: the owner reported that
  `message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md`
  has been re-asked in every handover since 2026-07-24 even though it carries
  `Status: folding`, `Review outcome: approved`, and a filled `**Your review:**`.
- Confirmed the cause before writing anything: `live_human_queue_paths()`
  (`automation/reconcile/reconcile.py`) filters on path and file mode only, and both
  consumers of that set — `templates/handover.md` and the root `AGENTS.md` chat-reply
  rule — inherit the omission.
