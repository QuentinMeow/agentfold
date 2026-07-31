# Plan — clear the four stuck queue items against real repository state

- [ ] 1. Claim the task, move it to `1_in-progress`, and resolve its pickup request in one
      coordination commit on branch task/2026-07-30-clear-the-stuck-queue-items.
- [ ] 2. Confirm from Git that the code-span repair really merged: the trailer commit, its
      ancestry on `main`, and the item's own `Done when` clauses.
- [ ] 3. Delete the merged code-span repair request together with its reciprocal
      `Queue actions` backlink in one commit, with the reconciler green and no evidence file
      staged.
- [ ] 4. Audit task 2026-07-25-fix-handover-projection-code-span-copy against its own
      acceptance criteria and merged commit; advance it to `3_in-review`, then to `4_done`,
      one lifecycle edge per commit, only if that audit passes.
- [ ] 5. Measure the three stranded merge reviews: ancestry of each bound range, what the
      deletion path reports, and what a `--at-transition merge` replay reports.
- [ ] 6. Record the diagnosis in `design.md` with the options that were rejected and why.
- [ ] 7. File one canonical `message-queue/needs-human/decisions/` item for the three, link it
      reciprocally from all three task records, and append a worklog entry to each.
- [ ] 8. Record real `--check` and full-suite output in `verification.md` and update
      `roadmap/current-state.md` where reality changed.
