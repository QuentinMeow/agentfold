# Worklog — fold the machine record on new human queue items

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-18 — fold-the-queue-machine-record (claude)

- Filed the task in `0_backlog` with its canonical pickup request, then claimed it in one
  coordination commit — `Claimed-by` set, the folder moved to `1_in-progress`, `plan.md`
  and this worklog added, and the pickup request deleted — and branched
  `task/2026-08-18-fold-the-queue-machine-record` from `main` at `fc8c0af`.
- Baseline re-measured before touching anything: `automation/run_tests.py` 15/15 files,
  exit 0; `reconcile.py --check` 0 blocking findings. `automation/tests/test_reconcile_queue.py`
  carried one uncommitted repair from a concurrent session (`getattr(ast, "Str", None)`,
  for Python 3.12+ removing `ast.Str`); it was adopted unchanged, never re-spelled.
- Implemented the sanctioned fold, the region-based `record-swallow` predicate,
  `fold-shape`, `queue-frozen-skeleton`, the narrowed raw-HTML rule with its
  `parsed ⊆ rendered` companions, `--fix-queue-fold`, the advisory `queue-render`, and
  the `.gitattributes` whitespace opt-out. Real output in `verification.md`.
- Surprise worth not repeating: the specification's tracked-file count (618) was measured
  at an older commit. The real denominator at `fc8c0af` is 623, and the live-item count is
  64 rather than 66. Every number in `verification.md` was re-derived here rather than
  copied from the specification.
- Second surprise: `record-swallow` does not fire on the attack where a fold swallows the
  answer line, because that attack destroys the very landmark the region's lower half is
  defined by. `fold-shape` refuses it. Recorded in `design.md` rather than papered over.
