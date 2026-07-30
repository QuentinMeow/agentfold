# Worklog — input-ownership test selection

## 2026-07-29 — implementation and measurement (claude)

- Established the premise by experiment: with all 292 projected record files corrupted the
  suite passed 11/11, and with the record trees deleted outright 10 of 11 passed, the
  eleventh failing only because the probe recursed into its own projection. Deletion is the
  stronger perturbation because real commits rename and delete records.
- Measured the shipped lane's replay over history: it selects the full suite for every
  commit, so its hit rate is zero.
- Built the ownership table with a coarse group fallback, and made removals and renames of
  non-record paths fall back to full, because two test files assert that specific service
  files exist.
- Replayed the new selection over the last 60 non-merge commits: 52 select no test, 8
  select between one and four, and none fall back to full. That is 13 test-file executions
  against 660 today.
- Recorded the limit honestly: a `reconcile.py` edit still selects the file that is 68-79%
  of the suite, so selection does not help where most of the work actually happens.
