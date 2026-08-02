# Plan — Finish the replacement-ref boundary the reconciler is halfway through building

Small verifiable steps, each with a named artifact or check. Checked off as completed.

- [x] 1. Claim: task in `1_in-progress` with `**Claimed-by:**` set, pickup request and its
      reciprocal `Queue actions` link deleted, `plan.md`/`worklog.md` present,
      `reconcile.py --check` reporting 0 findings.
- [x] 2. Inventory every bare Git invocation left on `main` (an `ast` scan of
      `reconcile.py`), and separate object reads from index/worktree-only commands.
- [x] 3. Reproduce first: add the six `test_replace_ref_cannot_*` regressions to
      `automation/tests/test_reconcile_queue.py` and run them against the UNMODIFIED
      `reconcile.py`; capture the real failing transcript.
- [x] 4. Harden the object-read boundary: `RAW_GIT`, the persistent
      `git cat-file --batch` reader, `git_object_kind`, the HEAD/tree snapshots, the
      staged `git diff --cached` readers, `git log`/`git show`/`ls-tree` history reads.
- [x] 5. Remove the `replace_objects=True` escape from `git_merge_base_result` and
      `git_ancestry_probe` so no caller can opt back into replacement objects.
- [x] 6. Add `test_git_object_reads_bypass_replacements_except_stable_allowlist` with an
      allowlist derived from main's own index/worktree-only commands.
- [x] 7. Re-run the six regressions and the guard against the hardened tree; capture the
      real passing transcript.
- [x] 8. Record `verification.md` (real before/after output only) and complete the
      `## Core fit` receipt in `design.md`.
- [x] 9. Full suite green: `python3 automation/run_tests.py` (11 files) plus
      `reconcile.py --check`.
- [x] 10. Append the session entry to `worklog.md` and `git mv` the task to
      `tasks/3_in-review/`.

Added after adversarial review found the boundary unfinished and the guard leaky:

- [x] 11. Reproduce the review's four findings first: the six spellings that slip past the
      list-literal guard, the blob-as-commit and stale-review exploits in
      `check_core_scope.py`, the staged-lane exploit in `run_tests.py`, and the ordinary
      starred list the guard wrongly rejects. Capture every real transcript.
- [x] 12. Harden `check_core_scope.py` at its `git` helper plus its two direct spawns,
      `run_tests.py` at the staged diff, `check_action_projection.py` at its `git_output`
      helper, and the merge/push adapters in `.github/workflows/harness.yml`.
- [x] 13. Replace the guard with a call-site scan over all four gates: fold every spawn's
      argument list to constant tokens, resolve the program, report what cannot be read,
      and apply the starred rule in argument position only.
- [x] 14. Register `automation/check_core_scope.py` and `automation/run_tests.py` in
      `INPUT_TEST_OWNERS` for `test_reconcile_queue.py`, which now reads them.
- [x] 15. Add a regression per closed spelling, per new exploit, and for the workflow;
      prove each fails against the pre-fix bytes at `4ffa8e3`.
- [x] 16. Correct the overclaim in `design.md` and the guard docstring, extend the
      `task.md` acceptance criteria to the sibling gates, and extend `verification.md`
      including its elision disclosure.
