# Plan — Redesign every file that asks a human for attention

Ordered so each step is verifiable on its own. Steps 1–6 change one file
(`automation/reconcile/reconcile.py`); step 10 is the single atomic migration commit that
activates the format repo-wide.

- [ ] 1. Reconciler constants and helpers: the renamed projection pair plus its legacy
      alias, the human timing tuple, the boundary-only tuple, the three header fields, the
      700-word budget, the choices-heading aliases, the confidence grammar, the choice
      heading pattern, the banned-field list, and the `Human-attention format: v1`
      activation readers — `python3 -c "import reconcile"` still imports
- [ ] 2. `check_queue_schema`: actor-aware timing fields, either projection spelling but
      never both, and the `## Your choices` alias check counting `### ` choices and
      `*Example consequence:*` over the union of alias sections — existing queue tests
      still pass
- [ ] 3. New `check_human_attention` registered in `CHECKS`, skipping answered items:
      exactly three header fields, no machine field above the answer line, a graded
      recommendation naming a shown choice, no raw HTML, no `Look-at`, ≤700 words, and no
      status-token prose contradicting `Status`
- [ ] 4. `review_successor_problem` compares boundary tokens instead of the timing tuple,
      so a changes-requested resolution does not hard-fail once `Until then` is gone
- [ ] 5. Handover entry schema v3: both spellings resolve at creation, the suffix branches
      on the version, the existing queue-v1 precedent keeps working, and the anti-downgrade
      check becomes a monotone version rank
- [ ] 6. The migration carve-out in `queue_mutation_problem`: one-shot activation gate with
      no parent already carrying the marker, same-path, refuses any answered item, 17
      frozen fields, 2 path-frozen fields, append-only projected sentences, and
      boundary-only timing comparison on that edge
- [ ] 7. Templates: `review.md`, `decision.md`, `clarification.md`, and the handover suffix
      line
- [ ] 8. Contracts: the shape subsection in `handbook/human-action-guide.md`, the
      copy-the-hash rule removed from `message-queue/needs-human/reviews/README.md`, and
      `history/AGENTS.md` at entry schema v3 documenting both suffixes
- [ ] 9. `message-queue/AGENTS.md` carries `**Human-attention format:** v1` and still fits
      its 60-line budget
- [ ] 10. One atomic migration commit: the marker plus all seven unanswered live items in
      the new format; the answered item is not in it and stays byte-identical
- [ ] 11. Test fixtures: the two renamed expected strings, plus positive tests for each new
      `human-attention` finding and for the carve-out's fences
- [ ] 12. Coordination the rename creates is settled: the code-span repair's immutable
      text is inspected for the old field spellings, and the deferred `Reviewed revision`
      deletion has its own backlog task
- [ ] 13. Verification: 0 findings, the full suite green, the byte-exactness proof, and
      every adversarial mutation re-run with its real output
