# Stop the reconciler's untracked-file scans from reporting findings under `tmp/`

**Claimed-by:** unclaimed
**Filed:** 2026-07-30, by claude, from two agents independently bricking their checkout
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-exclude-scratch-paths-from-checks.md`

## Goal

Root `AGENTS.md` designates git-ignored `tmp/` as scratch: "throwaway files go under
git-ignored `tmp/`, never the repo root." But `reconcile.py --check` walks the live
working tree (not just the Git index) to catch untracked-but-present content before it
is staged, and that walk does not exclude git-ignored paths. A scratch `AGENTS.md` copy
or a scratch clone left under `tmp/` gets reported as a repository-content finding
(`agents-budget` is the reported case), and because the pre-commit hook runs `--check`
over the whole repo and one finding blocks every commit, a stray scratch file bricks the
checkout — for a directory the contract itself calls scratch.

The fix must ask Git what is ignored rather than special-case `tmp/` in every affected
check, and must not weaken checks for anything actually tracked: a tracked file must
still be checked even at a path that also matches an ignore rule.

## Acceptance criteria

- [ ] WHEN an untracked file under git-ignored `tmp/` would otherwise trip a
      filesystem-walking check (`agents-budget` and others), THE SYSTEM SHALL report no
      finding for it.
- [ ] WHEN a tracked file sits at a path that also matches a `.gitignore` rule, THE
      SYSTEM SHALL still check it exactly as before.
- [ ] THE SYSTEM SHALL determine "ignored" by asking Git once per reconciler invocation
      (no per-candidate-file process spawn), consistent with the existing Git
      index/HEAD snapshot cache.
- [ ] Every filesystem-walking check that scans the live working tree for untracked
      content (not just `check_agents_budget`) SHALL share one exclusion primitive
      instead of each carrying its own special case.
- [ ] A regression test in `automation/tests/` SHALL cover a git-ignored scratch file
      producing no finding, and a tracked file at an ignored-looking path still
      producing one.

## Links

- `automation/reconcile/reconcile.py`
- `AGENTS.md`
