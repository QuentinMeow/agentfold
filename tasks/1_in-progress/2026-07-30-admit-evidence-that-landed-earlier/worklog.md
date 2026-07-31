# Worklog — Let a queue item be resolved by the work that already landed for its task

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-31 — admit-evidence-that-landed-earlier (claude)

- Filed and claimed the task on branch task/2026-07-30-admit-evidence-that-landed-earlier,
  stacked on task/2026-07-30-cache-reconciler-git-object-reads so the `cat-file --batch`
  reader and the tree caches are already available.
- The rule is decided upstream, not explored here: `design.md` records only the choices the
  spec left open and the reasons the implementation resolved them the way it did.
