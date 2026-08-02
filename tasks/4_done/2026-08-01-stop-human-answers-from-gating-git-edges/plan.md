# Plan — Stop a human answer from holding any Git edge

Each step lands as its own commit and leaves the tree green under
`reconcile --check`. Two orderings are load-bearing: the `Answer by:` backfill (3)
must precede the grammar (5), because landing the grammar first turns every live
human item red at once; and the migration (4) must be exactly one commit, because
the schema-activation edge is what authorises its timing weakening.

- [x] 1. Record the baseline: the deadlock reproduced, and the negative tests that
      must still refuse, captured before any change.
- [x] 2. Reconciler widenings only — nothing that passes today starts failing.
      `Answer by`/`Re-asked` become lifecycle-mutable, the unstart edge appears,
      `4_done` becomes an agent-work test, the merge-receipt cleanup condition is
      retired, and the bounded human-gating activation edge is added but not armed.
- [x] 3. Backfill `**Answer by:**` on every live `needs-human/` item and add the
      field to the three human queue templates.
- [x] 4. One commit: activate `**Human gating schema:** v1`, rename the four
      merge/complete-bound human items to `non-blocking-*`, swap their boundary
      fields for `If unanswered:`, and update every link.
- [x] 5. The grammar: a `needs-human/` item may bind only `transition:start` on a
      `0_backlog` task or `operation:<name>`; `Answer by` becomes required and
      advisory-stale. Contract files and templates state the new rule.
- [x] 6. The superseding records: five ADRs, two new ones, and the lesson that
      generalises the deadlock-freedom rule.
- [x] 7. The landing procedure and the stacked-branch rule in
      `handbook/git-workflow.md`.
- [x] 8. Rehearse the whole lifecycle in a throwaway clone — done task with a live
      question, late answer, fold, delete — and record the real output.
- [x] 9. `verification.md`, then move to `3_in-review`.
