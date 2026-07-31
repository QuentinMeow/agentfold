# Plan — make the reconciler report its own failures honestly

Small verifiable steps, each with a named artifact or check. Check off as completed.

- [ ] 1. Reproduce all four audit defects on an unmodified tree and record the real
      output (traceback, `EXIT=1`, `TypeError`, `0 finding(s)`, clock-driven findings)
- [ ] 2. Route both `repo_text` decodes through `decode_utf8_artifact` so an unreadable
      file becomes one named `GitSnapshotError`
- [ ] 3. Stream findings in `reconcile()` and catch broad `Exception` in `main()`,
      exiting 2 with one line naming the file or the check
- [ ] 4. Guard `check_roadmap_fresh` against `parse_date` returning `None` for an
      impossible date, mirroring the non-git branch
- [ ] 5. Replace the worktree existence gates at `check_mode_valid`,
      `check_stale_queue`, `check_roadmap_fresh`, and `check_memory_index` with
      index-backed gates, after checking each one reproduces
- [ ] 6. Add one regression test per defect and per fixed gate site; full suite green
- [ ] 7. Update `automation/AGENTS.md` and record real output in `verification.md`
