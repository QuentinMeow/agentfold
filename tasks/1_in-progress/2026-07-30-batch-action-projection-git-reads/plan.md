# Plan — read each repository view once per action-projection run

- [ ] 1. Record the measured spawn attribution so the chosen target is the measured one,
      not the one a prior record guessed at — `design.md` holds the counts.
- [ ] 2. Add a per-run snapshot that reads one repository view once: the index for a
      working-tree run, the candidate tree for a revision run.
- [ ] 3. Serve `candidate_record` from the snapshot, preserving the exact-path match and
      the multiple-record verdict.
- [ ] 4. Serve `candidate_paths` from the snapshot with literal directory-prefix
      semantics.
- [ ] 5. Fill blob sizes for the snapshot in one batched read so `tracked_regular_file`
      stops spawning per object.
- [ ] 6. Reset the snapshot at every entry point so no run answers from another run's
      view, with a test that fails if it does.
- [ ] 7. Re-measure spawns and module wall time, then record both in `verification.md`
      with the complete suite result.
