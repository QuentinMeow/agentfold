# Plan — judge a handover by its creation grammar

- [x] 1. Reproduce both failures on the unmodified tree and keep the real transcripts:
      the PR #44 merge probe (9 blocking) and a `main` range containing `b98621f`
      (9 blocking).
- [x] 2. Establish the ground truth: for every handover reachable from `main`, compare the
      marker its own creation snapshot declared against the suffix spelling it uses.
- [x] 3. Write the failing tests first — a withdrawn version, a parallel version bump, and
      a v3 admission that must keep v2's rejections — and record that they fail.
- [x] 4. Split the one governing version in two: an admission-edge rejection floor
      (unchanged, anti-dodge) and a creation-snapshot spelling grammar (new).
- [x] 5. Make the v2 rejecting clauses fire at v2 *or later*, so a version bump cannot
      silently switch them off.
- [x] 6. Add the anti-dodge preservation test: a branch cut before a rejecting grammar
      activated still cannot evade it.
- [x] 7. Correct `history/AGENTS.md` and `automation/AGENTS.md` prose within their
      60-line budgets; file the superseded rule as a new decision record.
- [x] 8. Re-run both reproductions, `--check`, and the full suite; record real output in
      `verification.md`.
