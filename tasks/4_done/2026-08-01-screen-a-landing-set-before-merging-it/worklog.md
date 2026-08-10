# Worklog — Screen a set of branches for collisions before any of them merges

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — screen-a-landing-set-before-merging-it (claude)

- Claimed the task, moved it to `1_in-progress`, and resolved its pickup request in one
  coordination commit.
- The claim commit was made from a detached worktree at `origin/main`, because the primary
  checkout carried another agent's staged work at the time and committing there would have
  swept it into this coordination commit.
- Built `automation/integrate.py` with the three verbs, tests in
  `automation/tests/test_integrate.py`, a row in `automation/AGENTS.md`, the tool named
  where the rule is read in `handbook/git-workflow.md`, and the ownership registration in
  `automation/run_tests.py`.
- Both traps the task named were real and both were confirmed by running them, not by
  reading. `git merge-tree --write-tree` dies with `unknown rev --write-tree` on the Git
  2.23 that is first on this machine's `PATH`, and the reconciler's
  `validate_range_candidate` accepts a committed two-parent merge as an exact synthetic
  merge of its `--range` base and head.
- One thing the task text did not anticipate: `run_tests.py --staged` reads
  `git diff --cached`, which is empty once the merge is committed. Commit-then-check would
  have turned the per-leg test lane into zero tests every time. The order became merge
  without committing, run the test lane, commit, run the reconciler — recorded in
  `design.md`.
- The end-to-end proof reproduces the incident rather than simulating it: two branches each
  adding twenty-three lines to `docs/AGENTS.md` at opposite ends are individually green and
  merge without a textual conflict, and the merged tree is 61 lines against a 60-line
  budget. `build` caught it with the real reconciler and named the bracketing commits.
- `automation/AGENTS.md` sat at exactly its 60-line budget, so the new row was paid for by
  reflowing one wrapped bullet to two lines. No words were removed.
- The task's `11/11` acceptance number is stale: the tree held twelve discovered test files
  before this branch and thirteen after. Noted in `verification.md` rather than quietly
  restated.

## 2026-08-09 — close-tasks-whose-work-already-merged (claude)

- The work merged to `main` in pull request #68 on 2026-08-03; only the folder never moved,
  so its status has misreported reality since. Moved to `4_done` to match.
- Verified before moving: `verification.md` holds real command output, `automation/integrate.py`
  and its tests are present on `main`, and no live blocking agent action names this task.
