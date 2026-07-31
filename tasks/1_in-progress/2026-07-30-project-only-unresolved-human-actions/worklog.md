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
- Tightened the split once more before finishing: `folding` alone no longer resolves an
  item; `folding` **plus** the committed response does. A claim edge cannot add a
  response, so a `folding` item carrying none contradicts itself, and a self-contradictory
  item keeps its owner's attention. This changed nothing on the live queue and made the
  predicate one sentence shorter.
- The hard constraint was immutability, and the mechanism was already in the repository:
  a schema marker in `history/AGENTS.md` plus a resolver that reads it from a handover's
  *creation* commit. The rule ships under a new `**Queue liveness schema:** v1` marker, so
  records written before it keep the liveness they were admitted under.
- Measured before and after rather than asserting it: a sweep re-ran the projection check
  at the creation commit of all 67 handovers reachable from `--all`, once with the old
  module and once with the new one.
- **The measurement earned its cost.** The first attempt versioned the rule as
  `Queue action-entry schema: v3`, and the sweep came back 8 findings before, 6 after —
  one handover's verdict had changed. The cause: the unmerged branch
  task/2026-07-23-first-class-message-queue already declares `action-entry schema v3`
  for its own meaning, and `main` had been treating that value as unrecognised. Teaching
  `main` a meaning for `v3` retroactively redefined that branch's records. It went greener
  by luck; a record projecting a resolved action would have gone red. Moving the rule to
  its own marker restored that commit to its original 8 findings, verified directly by
  running the pre-change and post-change modules side by side at that exact commit.
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
