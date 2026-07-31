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

## 2026-07-30 — make the projection state-aware (claude)

- Walked the state machine against `templates/queue/` and the reconciler before choosing
  the split. Three states are an agent's turn: `folding`, `awaiting-artifact`, and
  `waiting` that already carries a concrete response. Everything else — including a
  missing or unrecognised `**Status:**` — stays projected. `design.md` records why this
  errs permissive rather than strict.
- The hard constraint was immutability, and the answer was already in the repository:
  the `**Queue action-entry schema:**` marker plus `handover_action_entry_version_for()`
  resolve a version from a handover's *creation* commit. The rule became **v3**, so
  records admitted under v1 or v2 keep the liveness they were written against.
- Measured before and after rather than asserting it: a sweep re-ran the projection check
  at the creation commit of all 67 handovers reachable from `--all`, once with the old
  module and once with the new one. Identical finding sets. The 8 findings in both runs
  belong to one handover on the unmerged task/2026-07-23-first-class-message-queue
  branch and predate this work — the reconciler at main never reaches that commit.
- The measured win on the live queue is one item of eight: the approved detector-failure
  review that had been re-asked since 2026-07-24. The other seven are genuinely `waiting`
  with no response. The value is that the list is now *trustworthy*, not that it is short.
- Filed the second projection surface as a follow-up rather than folding it in:
  `automation/check_action_projection.py` enumerates the queue by path in exactly the same
  way for pull-request bodies.
- Dead end worth not repeating: `reconcile.py --check --range root:<HEAD>` is not a usable
  way to sweep history — it did not finish in 10 minutes. Driving
  `git_revision_candidate(commit)` directly, one creation commit at a time, is what the
  reconciler's own history recheck does and it completes in about half an hour.
