# Worklog — let a handover project a queue field that contains an inline code span

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-25 — fix-handover-projection-code-span-copy (claude)

- Claimed the task on `main` and removed its completed pickup request in the same
  coordination commit.
- Disproved the incoming diagnosis before changing anything. It read the two-element loop
  over `prose_without_links(entry)` and `prose_without_links(rendered_human_text(entry))`
  as a raw-versus-rendered choice that wrongly demanded both. Both elements run
  `prose_without_links`, so both blank code spans, and the two forms differ only when the
  entry carries raw HTML. Accepting either instead of both was measured as a no-op.
- Repaired the real asymmetry instead: both sides of the copy comparison now normalise
  through `render_inline_code`, matching the adjacent action-label check, which already
  renders code spans via `normalized_action_tokens`. The rendered-HTML guard is untouched.
- Measured the unguarded `needs-agent` tightening rather than deciding it from first
  principles: zero new findings on `--check`, on both CI range forms, and on the maximal
  `root:` sweep, whose 55 pre-existing findings are byte-identical before and after. The
  tightening was taken and pinned with a test.
- Added six regression tests; the three code-span projection tests and the agent-entry
  test fail against the pre-fix checker, while the two rejection tests pass on both sides.
- Committed the blocked session's handover at
  `history/conversations/2026-07-25-1140PDT-fold-edge-graph-decisions-and-ship-stage-0/`,
  projecting all ten live `needs-human/` items in canonical order. The identical file fails
  against the pre-fix checker on entry 2 and passes with the repair, which is the end-to-end
  evidence. Its Dead ends section records that the ritual was blocked, that the gate was
  repaired rather than bypassed, and that the earlier diagnosis was wrong in its mechanism.
- Opened pull request 14 against `main`. Its body declares `No queued action requested.`,
  because the task's only live queue action is a `needs-agent` path and the pull-request
  gate requires `needs-human` paths. Both admission jobs failed within seconds of the
  `opened` event on the already-filed `merge_commit_sha` race, and all four checks passed
  after an `edited` event recomputed the candidate.

## 2026-07-31 — clear-the-stuck-queue-items (claude)

- The task had been pinned at `1_in-progress` since 2026-07-26, not by unfinished work but
  by its `Queue actions` link to a request whose own repair had already merged. The
  deletion gate compared the declared evidence across the deletion edge only, and evidence
  that merged earlier is byte-identical on both sides.
- Task 2026-07-30-admit-evidence-that-landed-earlier widened that comparison. The request
  was deleted and this record's backlink dropped in one commit, with no evidence file in
  the edit and the whole reconciler at 0 findings.
- Audited this task before advancing it rather than assuming completion. `6d4e337` is an
  ancestor of `main` and carries the trailer naming this task; all three `Done when` clauses
  of the deleted request hold on `main` — the repaired comparison, six regression tests
  that pass today, and the blocked handover committed at
  `history/conversations/2026-07-25-1140PDT-fold-edge-graph-decisions-and-ship-stage-0/` in
  `b0d0971`, also an ancestor of `main`. `design.md` carries the complete `## Core fit`
  receipt and every `plan.md` step is checked off.
- Advanced to `3_in-review` and then to `4_done`, one lifecycle edge per commit. The
  transcripts are in task 2026-07-30-clear-the-stuck-queue-items.
