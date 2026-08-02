# Plan — Redesign every file that asks a human for attention

Ordered so each step is verifiable on its own. Steps 1–6 change one file
(`automation/reconcile/reconcile.py`).

- [x] 1. Reconciler constants and helpers: the renamed projection pair plus its legacy
      alias, the human timing tuple, the boundary-only tuple, the three header fields, the
      700-word budget, the choices-heading aliases, the confidence grammar, the choice
      heading pattern, the banned-field list, and the `Human-attention format: v1`
      activation readers — `python3 -c "import reconcile"` still imports
- [x] 2. `check_queue_schema`: actor-aware timing fields, either projection spelling but
      never both, and the `## Your choices` alias check counting `### ` choices and
      `*Example consequence:*` over the union of alias sections — existing queue tests
      still pass
- [x] 3. New `check_human_attention` registered in `CHECKS`, skipping answered items and
      items written in the pre-rename spelling: exactly three header fields, no machine
      field above the answer line, a graded recommendation naming a shown choice, no raw
      HTML, no `Look-at`, ≤700 words, and no status-token prose contradicting `Status`
- [x] 4. `review_successor_problem` compares boundary tokens for a review written in the
      new spelling, so a changes-requested resolution does not hard-fail once `Until then`
      is gone — and still compares the full timing tuple for one that is not
- [x] 5. Handover entry schema v3: both spellings resolve at creation, the suffix branches
      on the version, the existing queue-v1 precedent keeps working, and the anti-downgrade
      check becomes a monotone version rank
- [x] 6. `**Human-attention format:** v1` is sticky: once a reachable commit carried it,
      removing it while the queue remains is a finding, matching the queue-resolution,
      task-admission, and queue-projection markers
- [x] 7. Templates: `review.md`, `decision.md`, `clarification.md`, and the handover suffix
      line
- [x] 8. Contracts: the shape subsection in `handbook/human-action-guide.md`, and
      `history/AGENTS.md` at entry schema v3 documenting both suffixes
- [x] 9. `message-queue/AGENTS.md` carries `**Human-attention format:** v1` and still fits
      its 60-line budget
- [x] 10. Test fixtures: the two renamed expected strings, a positive test for each new
      `human-attention` finding, a test that reformatting a live item is refused with the
      marker active, and a test that an unanswered legacy item is left alone
- [x] 11. Coordination the rename creates is settled: the code-span repair's immutable
      text is inspected for the old field spellings, and the deferred `Reviewed revision`
      deletion has its own backlog task
- [x] 12. Verification: 0 findings, the full suite green, and an empty
      `git diff 025de49 HEAD -- message-queue/needs-human/`

Added during the work, from what the adversarial runs found:

- [x] 13. The timing and choices schema is selected by the projection spelling an item
      uses, not by whether it has been answered, so answering an item written in the new
      format cannot demand a timing field back that the response has already frozen
- [x] 14. The one-shot migration carve-out and every live-item rewrite it enabled are cut.
      An independent review broke the carve-out while every fence held; `design.md`
      records the exploit. `queue_mutation_problem` ends with no presentation carve-out,
      the seven rewritten files are restored to their baseline bytes, and the migration's
      own tests are replaced by tests that the rewrite is refused
- [x] 15. The three findings that survive the cut are filed as backlog tasks with pickup
      requests: the countersigned migration, the placeholder hole in `has_concrete_value`,
      and the fact that such a migration cannot be reverted
