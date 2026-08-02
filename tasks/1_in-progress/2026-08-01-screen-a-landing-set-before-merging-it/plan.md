# Plan — Screen a set of branches for collisions before any of them merges

- [x] 1. Claim: task in `1_in-progress`, pickup request resolved, plan and worklog present.
- [x] 2. `design.md` records the four choices this task makes — where the conflict screen
      gets its answer, how the reconciler can be run against a merge, where the integration
      happens, and how a failing leg is reported — and carries the completed **Core fit**
      receipt the Git boundary gate enforces.
- [x] 3. `automation/integrate.py` exists with `plan`/`build`/`verify` verbs, the repo's
      argument style, and the exit contract: 0 clean, 1 a real finding, 2 the check could
      not run at all (one line, no traceback).
- [x] 4. `plan` pins trunk and every leg to a full object id, refuses a leg whose recorded
      ref has drifted and a leg the trunk has moved past, screens every pair, and writes a
      manifest under the ignored `tmp/` scratch root.
- [x] 5. `plan`'s screen feature-detects `git merge-tree --write-tree` and falls back to a
      real merge in a scratch worktree; a `--conflict-probe` option forces either path so
      the two matrices can be compared, and forcing an absent capability exits 2.
- [x] 6. `build` merges each leg `--no-ff`, runs the staged test lane against the merge
      before it is committed, **commits** it, then runs the reconciler at the merge
      transition; the full suite runs once at the end.
- [x] 7. `build` stops at the first failing leg and names the commits that bracket the
      failure — the integration head before the merge, the leg tip merged in, and the merge
      commit the gate rejected.
- [x] 8. `verify` re-pins every ref, fails on drift, then asserts the merged tree equals the
      integration head's tree.
- [x] 9. `automation/tests/test_integrate.py` covers pinning, drift refusal, matrix
      equivalence across both probes, the commit-before-reconcile ordering, first-failure
      bracketing, and the exit-code contract; the tool is registered in
      `automation/AGENTS.md`, named where agents read the rule in `handbook/git-workflow.md`,
      and its tests are in the ownership table of `automation/run_tests.py`.
- [x] 10. `verification.md` holds real output: a colliding set reported, a clean set passing,
      both conflict probes agreeing, the full suite, and the reconciler's `--check` run.
