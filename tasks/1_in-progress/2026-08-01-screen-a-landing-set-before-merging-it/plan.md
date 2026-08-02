# Plan — Screen a set of branches for collisions before any of them merges

- [ ] 1. Claim: task in `1_in-progress`, pickup request resolved, plan and worklog present.
- [ ] 2. `design.md` records the three choices this task makes — where the manifest lives,
      how the conflict screen degrades on old Git, and how a failing leg is reported —
      and carries the completed **Core fit** receipt the Git boundary gate enforces.
- [ ] 3. A new integrate script under `automation/` exists with `plan`/`build`/`verify`
      verbs, the repo's argument style, and the exit contract: 0 clean, 1 a real finding,
      2 the check could not run at all (one line, no traceback).
- [ ] 4. `plan` pins trunk and every leg to a full object id, refuses a leg whose recorded
      ref has drifted, screens every pair, and writes a manifest under the ignored `tmp/`
      scratch root.
- [ ] 5. `plan`'s screen feature-detects `git merge-tree --write-tree` and falls back to a
      real merge in a scratch worktree; a `--conflict-probe` option forces either path so
      the two matrices can be compared.
- [ ] 6. `build` merges each leg `--no-ff`, **commits** it, then runs the reconciler at the
      merge transition and the staged test lane; the full suite runs once at the end.
- [ ] 7. `build` stops at the first failing leg and names the two commits that bracket the
      failure — the integration head before the merge and the merge commit itself.
- [ ] 8. `verify` re-pins every ref, fails on drift, then asserts the merged tree equals the
      integration head's tree.
- [ ] 9. A new test file under `automation/tests/` covers pinning, drift refusal, matrix
      equivalence across both probes, the commit-before-reconcile ordering, first-failure
      bracketing, and the exit-code contract; the tool is registered in
      `automation/AGENTS.md` and its tests in the ownership table of `automation/run_tests.py`.
- [ ] 10. `verification.md` holds real output: a colliding set reported, a clean set passing,
      both conflict probes agreeing, the full suite, and `automation/reconcile/reconcile.py --check`.
