---
name: memory-gardener
description: The forgetting pass — re-verify, compact, or delete expired memory; prune old done-tasks and conversations. Use when the reconciler reports overdue Review-by dates, or on an explicit maintenance request.
---

# Memory gardener

Memory that only grows becomes noise (`handbook/principles/design-for-forgetting.md`).
This pass keeps `memory/`, `tasks/4_done/`, and `history/` small enough to stay true.

## Protocol (propose, then apply)

1. **Collect**: run `python3 automation/reconcile/reconcile.py --check` and gather
   `memory-expiry` findings; list `tasks/4_done/` folders older than 90 days and
   `history/conversations/` older than 180 days.
2. **Triage each expired memory entry** — never in bulk, each on its own evidence:
   - **Still true** (verify against current code/docs) → bump `**Review-by:**` +90 days.
   - **True but bloated** → rewrite shorter; merge with any overlapping entry.
   - **Outdated fact/lesson/known-issue** → delete (git history archives it).
   - **Outdated ADR** → never edit it; write a superseding ADR, add
     `**Superseded-by:**` to the old one, bump its date.
   - **Proven repeatedly** (a lesson every session obeys) → promote into the relevant
     `AGENTS.md` and delete the lesson — one home per fact.
3. **Prune old tasks/conversations**: promote any still-valuable learning into
   `memory/` first, then delete the folders. Expect link-check findings: files outside
   the record folders (e.g. `roadmap/current-state.md`) may cite a pruned task —
   update or unlink them in the same commit.
4. **Regenerate**: `reconcile.py --fix-index`; then `--check` must pass.
5. **Report before apply**: in `async`/`pair` mode, or whenever touching more than ~10
   items in any mode, file a human review from `templates/queue/` and stop before the
   destructive boundary. For each proposed action, distinguish keep/compact/delete,
   give a concrete example of what disappears or remains, state the safe unattended
   result (keep the record), and link the full inventory and evidence. Small passes in
   `autonomous` mode apply directly — one commit per category
   (`harness: gardener — expire 3 facts`), never one giant commit.

## Queue discipline

`message-queue/` is canonical for pending human actions and agent work that must
survive the session; reports, tasks, handovers, and external review surfaces only link
those live items. Follow `message-queue/AGENTS.md`: use `blocking-` when named work
cannot proceed now, `future-blocking-` when work may continue only until a stated
date/event/transition (normally the deletion boundary), and `non-blocking-` when it
never stops work and has a safe unattended outcome. File any deferred repair found by
the gardening pass as a needs-agent item rather than leaving it only in the report.
