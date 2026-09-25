# Resolve the machine-record acceptance evidence before completion

**Status:** open
**Filed:** 2026-09-25, by codex, from task 2026-09-25-audit-repository-health-and-next-tasks
**Action:** Resolve the machine-record task's zero-unscoped-findings acceptance criterion against the recorded counterexamples before completing the task.
**Full context:** [Acceptance evidence mismatch](memory/known-issues/2026-09-25-machine-record-acceptance-exceeds-evidence.md)
**Resolution evidence:** `roadmap/current-state.md`
**Blocks at:** transition:complete task:2026-08-18-fold-the-queue-machine-record
**Until then:** Keep the machine-record task in review; its merged implementation and unrelated work remain usable.

## What you need to know

The current predicate returns three independently reproduced fold-shape counterexamples
when used outside its declared scope. The task's historical evidence already recorded
nonzero unscoped results, while its last acceptance checkbox claims zero for every new
predicate. Merged status and the passing ordinary suite do not resolve that contradiction.

## Done when

The task has evidence satisfying its retained acceptance, or a separately justified scope
disposition records why that criterion was changed without inventing owner approval.
The resolution and real verification are durable before this request and its reciprocal
link are removed. Existing human questions stay live independently.
