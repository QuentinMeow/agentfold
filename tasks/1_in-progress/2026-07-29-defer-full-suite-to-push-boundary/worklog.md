# Worklog — give the commit gate a routine lane and let the push boundary own completeness

## 2026-07-29 — implementation and measurement (claude)

- Verified the load-bearing premise directly in `.github/workflows/harness.yml`: the trigger
  carries no branch or path filter and the test step is unconditional, so every push already
  runs the complete suite and blocks. The local full suite duplicated it.
- Implemented three lanes selected by a flag, with an environment variable as the only knob.
  No configuration file: `tomllib` exists on neither interpreter here, and a config format
  makes nothing faster.
- Measured the routine lane: a records-only commit's test step is 0.04s and the whole
  pre-commit is 13.33s, entirely reconciler-bound.
- Recorded the strongest objection against this design rather than omitting it: with the
  current selector an `automation/` change selects no test files at all, so the file every
  agent depends on stops being tested locally. That is why this task depends on input
  ownership selection landing first.
