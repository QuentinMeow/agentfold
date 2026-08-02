# Worklog — Redesign every file that asks a human for attention

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-31 — human-action format redesign (claude)

- Claimed the task and moved it to `1_in-progress`; claimed the live redesign request
  `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`
  `open` → `in-repair` in the same coordination commit.
- Baseline is branch harness/2026-07-31-fold-answered-queue-review at `025de49`, where
  `python3 automation/reconcile/reconcile.py --check` reports 0 findings.
- Landed the mechanism: the `human-attention` check, the rename with its permanent legacy
  alias, and handover entry schema v3.
- The adversarial run found a defect the reviewed spec would have shipped. The spec keys
  the timing schema on whether an item carries a response, so answering an item written in
  the new format flips it back to the pre-rename tuple and the reconciler demands
  `Until then` back — which `queue_mutation_problem` forbids after a response. The item
  would have been unfixable in both directions. Keyed on the projection spelling instead;
  pinned by `test_answering_a_migrated_item_keeps_its_own_schema`, which fails against the
  spec's rule and passes against the shipped one.
- Also built the spec's one-shot migration carve-out and rewrote all seven unanswered live
  items with it. That is the part that did not survive review — see the next entry.
- The code-span repair the spec asked about has already landed on this base —
  `render_inline_code` normalises the projection side — so no successor was filed and its
  immutable `Action` text was not touched. Both field spellings stay valid forever, so
  the repair it asks for is unchanged.
- Filed task `2026-08-01-derive-the-reviewed-revision-field` for the deferred field
  deletion, with its own pickup request and its own review requirement.
- Left the redesign request and the promised re-review live. The request resolves when
  this work merges; the re-review is still `awaiting-artifact` and is published, bound to
  an exact revision, at the merge boundary — not here.

## 2026-08-01 — land the safe variant after DO NOT SHIP (claude)

- An independent adversarial review returned DO NOT SHIP on the migration carve-out and
  broke it while every fence held: seventeen frozen fields byte-identical, both
  path-frozen fields identical, both projected sentences prefix-clean, `0 finding(s)` —
  and the migration still changed the question, inverted a scope limit the owner had set,
  deleted a choice, flipped the recommendation, and raised the stated confidence. The
  fences guard field labels; the ask is the title, the context, the choices, and the
  recommendation. That cannot be closed by freezing more fields, so the carve-out is cut
  rather than tightened. Recorded in `design.md`.
- Cut `human_attention_presentation_migration`, `PRESENTATION_FROZEN_FIELDS`,
  `PRESENTATION_FROZEN_PATH_FIELDS`, the parent-marker clause, and the boundary-only
  timing relaxation that rode on that edge. `queue_mutation_problem` now has no
  presentation carve-out; reformatting a live item is refused with the marker active
  exactly as it is without it, pinned by
  `test_reformatting_a_live_item_is_refused_with_or_without_the_marker`.
- Deleted the dead `candidate_parent_revisions`, a byte-for-byte duplicate of
  `candidate_parent_oids`, plus two other now-unreferenced helpers.
- Rebuilt the branch from the claim commit rather than committing a revert. A revert is
  itself a live-item rewrite on the staged edge, so the reconciler reports seven
  `queue-resolution` findings against it; only history without the migration commit is
  clean. The two coordination commits `a7e9541` and `062ad01` are preserved unchanged.
- Restored every file under `message-queue/needs-human/` to its `025de49` bytes, including
  the leaf `README.md`: it describes the eight files that were not migrated, so rewriting
  it moved into the countersigned-migration task.
- Gated every presentation check on the item's own projection spelling as well as the
  repository marker, so an existing live ask is neither rewritten nor newly rejected.
- Fixed two findings the review raised beyond the carve-out. `review_successor_problem`
  had started comparing boundary tokens for every human review, which drops the
  `Until then` and `If unanswered` comparisons entirely for a legacy item — an
  unconditional loosening. It is now scoped to reviews written in the new spelling, and
  `test_legacy_review_successor_is_still_compared_on_its_timing_prose` fails against the
  loosened version. `**Human-attention format:** v1` gained the activation-persistence
  guard the three other schema markers already had.
- Deleted the migration's own tests, including
  `test_presentation_migration_refuses_a_marked_second_merge_parent`, which set
  `MERGE_HEAD` to `HEAD` so the parents deduplicated to one and the clause under test was
  never exercised. Nothing it covered survives.
- Filed the three findings that outlive this task as backlog tasks with pickup requests:
  the countersigned migration, the placeholder hole in `has_concrete_value` (verified:
  "none" reads as unanswered, and every response-protection check keys on that
  predicate), and the fact that such a migration cannot be reverted.

## 2026-08-01 — merge onto main (claude)

- Merged the task work onto main at `d1feea8`, main as the first parent. Transcripts in
  `verification.md`.
- The substantive merge was in the handover projection machinery, where this task and
  main's `2026-07-30-project-only-unresolved-human-actions` changed the same code for
  different reasons. This task added action-entry schema **v3**, which renames the two
  rendered suffix labels. main split the single version namespace into two: entry schema
  for projection *syntax*, and a new **Queue liveness schema** for *which* human actions
  a projection contains. The two are orthogonal, so both are kept —
  `HANDOVER_ENTRY_VERSIONS` gains `v3`, main's parameterised `handover_schema_version`
  serves both namespaces, and `history/AGENTS.md` declares both markers.
- `entry_schema_rank` was dropped rather than merged. main's `entry_version_at_least`
  already ranks by tuple position and is the helper the shared code path calls, so
  keeping a second ranking function would have meant two answers to one question. Its
  test now asserts the same monotonicity, including `v3`, through that helper.
- `history/AGENTS.md` is on the 60-line leaf budget and the union of the two paragraphs
  did not fit. The three lines came out of a restatement rather than a rule: handover
  immutability was stated twice, mid-paragraph and again in the freeze sentence, and now
  reads once.
- The three queue templates conflicted the other way. This task rewrote them around the
  nine-point checklist; main had just removed the restated prefix list from them in
  favour of a pointer to `message-queue/AGENTS.md`. Kept this task's structure with
  main's pointer — reinstating the restatement would undo a change main merged on purpose.
- The merge is taken from the task's own lineage rather than from an earlier integration
  tip that had already merged an older main. That earlier tip left main and the branch
  with two merge bases, and `queue-resolution` resolves a merge parent's boundary with a
  single `git merge-base`; it picked the older base and read an unrelated pickup request's
  ordinary claim-and-delete as an unresolved deletion. Merging the task lineage directly
  gives one unambiguous base and the same tree, and the merge boundary reports 0 blocking
  findings.
- Full suite 11/11 files, reconciler 0 blocking findings.
