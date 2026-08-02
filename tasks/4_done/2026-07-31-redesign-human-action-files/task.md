# Redesign every file that asks a human for attention

**Claimed-by:** claude
**Filed:** 2026-07-31, by claude, from the live redesign request — `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

The owner rejected the current human-attention format: the English is broken, past and
current and proposed behavior are indistinguishable, choices are ambiguous, and
parser-style labels, excessive metadata, and duplicate links obscure the decision. This
task lands the decided action-first format — an ask-first three-field header, a
`Today` / `What this would change` / `What this does not decide` context block, explicit
choices with per-choice example consequences, an evidence-backed recommendation with its
own counter-case and a graded confidence, and every machine field moved below the answer
line — and enforces it in `automation/reconcile/reconcile.py`.

It does not touch a single live item. Migrating the eight files already in
`message-queue/needs-human/` was attempted, reviewed, and cut: see `design.md`. Every new
ask is written in the new format; the existing files keep the schema they were written
under and age out as they resolve, and the countersigned migration they would need is
filed as task `2026-08-01-countersign-the-live-human-item-migration`.

An earlier attempt is design input, not a merge candidate: it rewrote
`automation/markdown_semantics.py` by 1,849 lines to reason about rendered prose and was
blocked three times by its own adversarial panel. This task enforces structure only and
leaves `automation/markdown_semantics.py` untouched.

## Acceptance criteria

- [x] `templates/queue/review.md`, `templates/queue/decision.md`, and
      `templates/queue/clarification.md` describe one action-first format with exactly
      three fields above the first heading and all bookkeeping below the answer line
- [x] `handbook/human-action-guide.md` states the shape of a human-attention file once,
      and says a person is never asked to copy a hash, a revision, or any offered
      vocabulary
- [x] The reconciler gains a `human-attention` check that rejects a fourth header field,
      any machine field above the answer line, a missing or ungraded recommendation, a
      recommendation naming a choice that was never shown, raw HTML, a resurrected
      `Look-at`, more than 700 words above the answer line, and state-dependent prose
      that contradicts `Status`
- [x] `Why-you-might-care` and `If-you-do-nothing` are renamed to `Why this matters` and
      `If you do nothing`, with a permanent legacy alias and a `Queue action-entry
      schema: v3` handover suffix, so no record created under v1/v2 is retroactively
      invalidated
- [x] No file under `message-queue/needs-human/` changes at all:
      `git diff 025de49 HEAD -- message-queue/needs-human/` is empty, proved in
      `verification.md`
- [x] `queue_mutation_problem` carries no presentation carve-out: reformatting a live
      item is refused with the format marker active exactly as it is without it, pinned
      by a test
- [x] Every new presentation check is inert for an item written in the pre-rename
      spelling, so an existing live ask is neither rewritten nor newly rejected
- [x] `**Human-attention format:** v1` cannot be removed once activated while the queue
      remains, matching the three existing schema markers
- [x] `review_successor_problem` compares boundary tokens only for a review written in
      the new spelling, and still compares the full timing tuple for one that is not
- [x] `python3 automation/reconcile/reconcile.py --check` reports 0 findings and
      `python3 automation/run_tests.py` passes every file, with both real outputs in
      `verification.md`
- [x] `design.md` carries a complete `## Core fit` receipt, because
      `automation/reconcile/reconcile.py` is a core path

## Links

- The request this repairs: `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`
- The promised follow-up judgment: `message-queue/needs-human/reviews/non-blocking-rereview-human-action-files.md`
  (filed under the pre-rename name `future-blocking-rereview-human-action-files.md`, which
  never existed on disk; the live item carries the `non-blocking-` prefix)
- What a human action must achieve: `handbook/human-action-guide.md`
- The queue contract and its lifecycle: `message-queue/AGENTS.md`
- Why the queue owns pending actions: `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`
- Migrating the eight existing asks: task `2026-08-01-countersign-the-live-human-item-migration`
- Why such a migration is one-way: task `2026-08-01-record-that-a-format-migration-is-one-way`
- The placeholder hole this found: task `2026-08-01-stop-reading-none-as-an-unanswered-field`
- The deferred field deletion: task `2026-08-01-derive-the-reviewed-revision-field`
