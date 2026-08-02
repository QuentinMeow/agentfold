# Plan — record that a format migration is one-way

The task's own text names its exit condition: it is only worth doing if the migration
proceeds, and is otherwise closed as not-needed with the reason recorded. So the plan is
to test that condition and fold rather than to build.

- [x] 1. Confirm the task really does say it should be closed if the migration does not
      proceed, and that no part of it is separable from that migration.
- [x] 2. Confirm the parent task `2026-08-01-countersign-the-live-human-item-migration`
      really does require its `design.md` to account for the one-way property. If it does
      not, do not fold — report it instead.
- [x] 3. Carry the substance — the symmetry argument, and the two-way choice it forces —
      into the parent's `task.md`, so the parent stops depending on this record.
- [x] 4. Fold this task's own acceptance criteria into the parent criterion they belong to,
      rather than dropping them: the `git revert` reproduction and the fixture exercise are
      now what makes the parent's design choice evidence.
- [x] 5. Close, and record where the substance went.
