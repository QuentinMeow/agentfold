# Plan — generate one ordered list of every open action

Steps 1 through 4 name files that do not exist yet, so they are written without path
backticks; the link check is right to reject a citation that resolves to nothing.

- [ ] 1. Register the digest as a queue root document, so the queue's location, naming,
      schema, and staleness checks keep ignoring it instead of reporting it as a malformed
      item.
- [ ] 2. Add the generator to `automation/reconcile/reconcile.py`: read every live queue
      item, order them, collapse repeated pickups, render bullets with folded consequence
      lines. Output depends on the queue files only — no date, no revision, no host state.
- [ ] 3. Add the check and its `CHECKS` entry, blocking, mirroring `check_memory_index`,
      with a fix line naming the regeneration command.
- [ ] 4. Add the regeneration flag and wire it into the argument parser.
- [ ] 5. Add a focused test file under `automation/tests/`: ordering across both actors and
      all three timing prefixes, pickup collapsing, per-item fields, idempotence, the
      staleness finding and its clearing, and the absent-queue no-op an adopter needs.
- [ ] 6. Register the new test file's inputs in the ownership table of
      `automation/run_tests.py` if it requires it, and confirm `--staged` still selects the
      right tests.
- [ ] 7. Generate the real digest and render it through GitHub's own Markdown API, to prove
      the nested folds survive rather than assuming they do.
- [ ] 8. Document it where agents read: one row in `automation/AGENTS.md`, one line in
      `message-queue/AGENTS.md`, and the repo map entry in the root `AGENTS.md`.
- [ ] 9. Write `verification.md` from real output, run the full reconciler and the full test
      suite, commit, push, and open the pull request.
