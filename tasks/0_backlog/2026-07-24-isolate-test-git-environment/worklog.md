# Worklog — isolate repository tests from Git hook state

## 2026-07-24 — layered-workspace-research (codex)

- A pre-commit run in a linked worktree moved `main` through synthetic test commits,
  set `core.bare=true`, injected the test identity, and replaced the linked-worktree
  index. The active task branch itself stayed intact.
- Reflog and remote-tracking evidence identified `acc23b6289f5ca66744718af379aba0468be93e2`
  as the exact prior `main`; recovery used compare-and-swap ref repair, exact config
  cleanup, and index-only reconstruction, preserving the human-answer transcription.
- Root cause traced to Git-local hook variables inherited by test subprocesses in
  `automation/run_tests.py`; no production fix was written before the regression.

## 2026-07-24 — test-runner-isolation-repair (codex)

- Claimed the main-side blocking repair, preserved the recovered task records, and
  reran the focused regression before implementation. Two tests failed because the
  isolation boundary did not exist; the preserved test also needed its final
  Python 3.7-compatible mock-call assertion.
- Added one canonical boundary in `automation/run_tests.py`: discover Git's complete
  local-variable list, fail closed on discovery error, remove every name from a copied
  environment, and pass that environment to each test process.
- Consolidated the repair on the layered workspace branch because the older isolation
  branch could not see the queue record that lives on `main`; no check was bypassed.
- Admitted the recovered records through the current backlog schema before making the
  claim durable; the earlier linked-worktree files had never been committed.
