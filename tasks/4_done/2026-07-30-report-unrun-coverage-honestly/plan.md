# Plan — parseable reporting for an empty selection

- [x] 1. Print `tests: 0/0 files passed` on the empty-selection path, keeping the existing
      explanation of why nothing was selected, and matching the exact wording the
      non-empty path uses so one parser reads both.
- [x] 2. Extend the skipped-file line so it names where that coverage happens.
- [x] 3. Repair the inert-probe call site left behind by the wrapper removal rename.
- [x] 4. Cover each of the three with a test that fails without it.
- [x] 5. Record the real output of the empty-selection run and the inert probe.
