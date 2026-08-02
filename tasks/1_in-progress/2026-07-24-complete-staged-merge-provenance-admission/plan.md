# Plan — complete staged-merge provenance admission

This task was filed to finish work that was preserved in an unmerged publication stack.
Before writing anything, the first step is to find out whether that work is already on
`main` — a task whose implementation landed by another route is closed by audit, not by
reimplementation. Every step below is that audit.

- [x] 1. Read the four behavioural acceptance criteria against the pickup request's own
      statement of what was left: creation checks selected from the final path set, so an
      add-then-delete or one of two byte-identical parallel additions escapes exact
      creation-snapshot validation.
- [x] 2. Locate on `main` every regression each criterion is claimed to map onto, and read
      what it asserts rather than what it is named.
- [x] 3. Run those regressions and record the real result.
- [x] 4. Prove the duplicate-path regression is not passing on its weakest disjunct: print
      the findings it actually produces and show one of them validates the side branch's
      add against that branch's own queue snapshot, not against the merged tree.
- [x] 5. Probe the two halves of criterion 4 that no named regression reaches — committed-
      range parity for the two post-fork human-response cases, and an unrelated-history
      root imported by `--allow-unrelated-histories` — and record whether the behaviour
      holds.
- [x] 6. Run the complete queue suite, the repository runner, and the reconciler, and record
      their real output.
- [x] 7. Write the criterion-to-evidence map in `verification.md`, including anything the
      audit could not discharge, and close the task on that record.
- [x] 8. File the one coverage gap the audit found as its own backlog task, so a proven hole
      does not survive only inside a closed task's verification record.
