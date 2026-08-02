# Worklog — configurable test gates and time budgets

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-27 — file-configurable-test-budget-task (codex)

- Reviewed the current hook and full runner, the existing development-feedback task, recorded
  timing evidence, the configurable guard-mode decision, and the deterministic-filing lesson.
- Chose a budgeted routine lane plus configurable final lane, with explicit critical-scope
  exceptions, exact-evidence reuse, and automatic deduplicated investigation-task filing.
- Filed this focused child task and its pickup request. No implementation was started.

## 2026-07-27 — configurable-test-gates-coordination (codex)

- Audited the live GitHub stack and confirmed draft PR 16 is the only open prerequisite; the
  implementation branch must start from its head and target its task branch.
- Recorded the owner's Option A authorization through the human-action lifecycle, preserving
  the original dirty `main` checkout while publishing the validated coordination commits.
- Claimed the task for codex and removed its pickup request. Independent design review blocked
  the original underspecified contract; implementation starts only from the resolved contract
  covering whole-interval timing, explicit critical bindings, exact tested views, and
  nonblocking regression filing.

## 2026-08-02 — return to backlog, claim abandoned and premise re-measured (claude)

- The `codex` claim of 2026-07-27 was untouched for six days and is cleared. Nothing was
  built: `ls agentfold.toml` reports no such file, and
  `grep -rn "agentfold.toml\|routine gate\|routine_gate\|final_gate" automation/ --include='*.py'`
  matches nothing. `plan.md` stands at 0 of 8.
- A branch of this task's name did exist and merged as pull request 18 (`bf6f726`) on
  2026-07-29, so "no branch was ever pushed" would be wrong. What it carried was not gate
  work: two unrelated test files and a one-line formatting fix to this task's own `design.md`
  Core-fit receipt (backticks removed from the `Thin adapter:` line). No configuration, no
  lane, no budget.
- **The premise decayed while the claim sat.** The task was written against a full suite of
  214.62–221.17 seconds and chose 60 seconds as the routine-gate target against that number.
  Measured today on this host:

  ```
  $ python3 automation/run_tests.py
  [...]
  tests: 12/12 files passed
  test elapsed: 75.67s
  real 75.87
  user 148.45
  sys 153.84
  ```

  Twelve of twelve files pass in 75.87 seconds wall clock, against 148.45s user plus 153.84s
  system — the parallelism the old serial measurement did not have. One run, one host, and
  another agent was committing in the same checkout while it ran, so treat it as the order of
  magnitude rather than a benchmark.
- What that unsettles is the target, not the task. A 60-second budget was a large cut from
  ~215 seconds; from ~76 seconds it is a much smaller one, and whether it is still the right
  goal is exactly what the next claimant must re-derive rather than inherit. The stale
  section in `task.md` is marked rather than rewritten, because the numbers it records were
  real when written and the record of what was believed is worth keeping.
- Returned to `0_backlog` with a fresh `task-pickup` request,
  `message-queue/needs-agent/requests/non-blocking-pick-up-configure-test-gates-and-time-budgets.md`,
  whose Action tells the claimant to re-measure before implementing.

## 2026-08-02 — timing correction (claude, orchestrating session)

- The 75.87s figure above does not reproduce, and the entry immediately below it in this
  worklog should be read with that in mind. A separate agent measured the same suite on the
  same day with nothing else in flight and recorded `121.11s` (2:01.62 wall), and `142.10s`
  on a loaded host. Three same-week measurements of the same command therefore span roughly
  1.9x: 75.87s, 121.11s, 142.10s. None of them is wrong; the spread is the finding.
- The reconciler shows the same problem at smaller scale — measured at 31s wall in that run,
  against the ~5.28s this task's own text assumes.
- What this changes for the claimant: do not re-derive the budget from a single fresh
  measurement either. A target built on one number from this suite is built on noise. Decide
  first what the measurement protocol is — how many runs, on what machine state, and which
  statistic — and record it, because the next agent to question the budget will otherwise
  repeat this exact exchange. The task's own premise that a budget is the right shape of goal
  is worth re-examining against a 1.9x spread.
