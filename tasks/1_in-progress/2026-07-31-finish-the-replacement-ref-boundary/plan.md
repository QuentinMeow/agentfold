# Plan — Finish the replacement-ref boundary the reconciler is halfway through building

Small verifiable steps, each with a named artifact or check. Checked off as completed.

- [ ] 1. Claim: task in `1_in-progress` with `**Claimed-by:**` set, pickup request and its
      reciprocal `Queue actions` link deleted, `plan.md`/`worklog.md` present,
      `reconcile.py --check` reporting 0 findings.
- [ ] 2. Inventory every bare Git invocation left on `main` (an `ast` scan of
      `reconcile.py`), and separate object reads from index/worktree-only commands.
- [ ] 3. Reproduce first: add the six `test_replace_ref_cannot_*` regressions to
      `automation/tests/test_reconcile_queue.py` and run them against the UNMODIFIED
      `reconcile.py`; capture the real failing transcript.
- [ ] 4. Harden the object-read boundary: `RAW_GIT`, the persistent
      `git cat-file --batch` reader, `git_object_kind`, the HEAD/tree snapshots, the
      staged `git diff --cached` readers, `git log`/`git show`/`ls-tree` history reads.
- [ ] 5. Remove the `replace_objects=True` escape from `git_merge_base_result` and
      `git_ancestry_probe` so no caller can opt back into replacement objects.
- [ ] 6. Add `test_git_object_reads_bypass_replacements_except_stable_allowlist` with an
      allowlist derived from main's own index/worktree-only commands.
- [ ] 7. Re-run the six regressions and the guard against the hardened tree; capture the
      real passing transcript.
- [ ] 8. Record `verification.md` (real before/after output only) and complete the
      `## Core fit` receipt in `design.md`.
- [ ] 9. Full suite green: `python3 automation/run_tests.py` (11 files) plus
      `reconcile.py --check`.
- [ ] 10. Append the session entry to `worklog.md` and `git mv` the task to
      `tasks/3_in-review/`.
