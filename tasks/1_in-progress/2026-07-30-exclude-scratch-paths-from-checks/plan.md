# Plan — exclude scratch paths from the reconciler's filesystem walks

- [x] 1. Reproduce: copy a real `AGENTS.md` (or any file over budget) into `tmp/`,
      confirm `reconcile.py --check` reports an `agents-budget` finding for it, and
      record the real output.
- [x] 2. Find every filesystem-walking check (not just `check_agents_budget`) that scans
      the working tree for untracked content, by grepping for `rglob`/`iterdir`/`glob`
      and reading each call site's git-vs-no-git gating.
- [x] 3. Add one cached, Git-backed "is this path ignored" primitive
      (`path_is_git_ignored`, backed by a single `git ls-files --others --ignored
      --exclude-standard --directory -z` call cached like the existing index/HEAD
      snapshots) and apply it only to each site's untracked/filesystem half.
- [x] 4. Confirm the fix does not weaken checks on tracked content: a tracked file at a
      path that also matches an ignore rule must still be checked.
- [x] 5. Add a regression test in `automation/tests/test_reconcile_queue.py` covering
      both directions.
- [x] 6. Run the full test suite and `reconcile.py --check` clean before committing.
