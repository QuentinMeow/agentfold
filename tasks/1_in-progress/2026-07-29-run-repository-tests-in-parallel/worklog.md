# Worklog — parallel test shards

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — fast-local-test-feedback continuation (claude)

- Claimed from the backlog after PRs 20, 21 and 22 merged, which removed the shell
  wrapper, cut reconciler Git spawns, and added input-ownership selection.
- Re-measured the complete suite on merged main: 198.57s wall, 81.70s user, 102.63s sys.
  System time still exceeds user time, so the suite remains bound by process creation.
- Why this task still matters after the selector merged: input-ownership selection makes
  a records-only commit cost 0.02s, but a change to `automation/reconcile/reconcile.py`
  still selects `automation/tests/test_reconcile_queue.py`, which is 68-79% of the suite.
  Selection is already correct for that case; the selected unit is simply too large. That
  is the population parallel sharding serves.
