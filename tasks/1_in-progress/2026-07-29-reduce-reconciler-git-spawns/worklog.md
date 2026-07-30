# Worklog — spawn fewer Git processes in the reconciler and its fixtures

## 2026-07-29 — implementation and measurement (claude)

- Counted spawns exactly: 9,981 in the long-pole test file, 33.5 per test. After the
  change, 7,045 and 23.6 per test. `git show` fell 1344 to 33 and fixture `init`+`config`
  687 to 7.
- Full suite measured 219.42s to 166.04s under one lock in the same quiet window. The
  production reconciler improved too: 307 spawns to 214, about 13% less wall time.
- Attribution surprised the prior: interleaving base, Lever 1 only, and both levers inside
  a single hold gave 91.31s, 90.91s and 73.08s. **Lever 2 delivered the whole measurable
  win; the fixture hoist did not register at file scale**, even though it is genuinely
  23ms per test cheaper in isolation. It is reported as a wash, not a win.
- A first before/after pair taken 30 minutes apart under the lock said −63%. It was wrong:
  the same base code measured 91s later in the same lock, with CPU time doubling too. Only
  variants interleaved inside a single hold are comparable on this machine.
- The suite caught a real defect that direct runs did not: a guard test asserted
  `git log --format=%an`, which fails under the runner because it exports the real
  `GIT_AUTHOR_NAME`. Running a test file directly is not equivalent to what the gate runs.
