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
   `memory/` first, then delete the folders.
4. **Regenerate**: `reconcile.py --fix-index`; then `--check` must pass.
5. **Report before apply**: in `async`/`pair` mode, or whenever touching more than ~10
   items in any mode, present the deletion list as a
   `message-queue/needs-human/reviews/` item and stop; apply next session if no
   objection. Small passes in `autonomous` mode apply directly — one commit per
   category (`harness: gardener — expire 3 facts`), never one giant commit.
