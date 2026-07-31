# Worklog — Let a queue item be resolved by the work that already landed for its task

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-31 — admit-evidence-that-landed-earlier (claude)

- Filed and claimed the task on branch task/2026-07-30-admit-evidence-that-landed-earlier,
  stacked on task/2026-07-30-cache-reconciler-git-object-reads so the `cat-file --batch`
  reader and the tree caches are already available.
- The rule is decided upstream, not explored here: `design.md` records only the choices the
  spec left open and the reasons the implementation resolved them the way it did.
- Shipped the rule, the six threaded call sites, the shared `task:<id>` pattern, the
  `task_ids_linking_queue_at` blob read, and four regression tests. All seven verifications
  in `verification.md` were run and recorded.
- Two findings worth carrying forward. First, the acceptance test is stronger than asked:
  staging the stuck deletion leaves the whole reconciler at `reconcile: 0 finding(s)`, not
  just `queue-resolution`, so the deletion can actually be committed. Second, the
  `task_ids_linking_queue_at` optimisation saves no spawns while the base branch's object
  reader is available — the tree cache already answers those reads. It saves 48 per call
  only on the fallback path where that reader is unavailable, which is where the change
  would otherwise have cost 51 spawns per deletion instead of 3. Both numbers are recorded
  rather than the estimate they replaced.
- Two dead ends not worth repeating: a probe clone under the repository's own `tmp/` is
  still scanned by `agents-budget`, and `git checkout -- .` does not undo a staged deletion,
  so every probe iteration needs `git reset --hard`.
