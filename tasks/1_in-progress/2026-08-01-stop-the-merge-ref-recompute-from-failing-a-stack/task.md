# Stop the merge-ref recompute race from failing every stacked pull request

**Claimed-by:** claude (session 2026-08-02, branch task/2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack)
**Filed:** 2026-08-01, by claude, from task `2026-08-01-stop-human-answers-from-gating-git-edges`
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

`review-state-action-projection` in `.github/workflows/harness.yml` asserts
`test "$ACTION_PROJECTION_CANDIDATE_REVISION" = "$ACTION_PROJECTION_EXPECTED_REVISION"`
and exits 1 when they differ. Merging a parent pull request moves its children's base;
GitHub then recomputes `refs/pull/N/merge`, and the two revisions differ for exactly as
long as that takes. The result is that the *characteristic* stacked-pull-request event
fails a check for a reason that has nothing to do with the change.

Make the recompute race re-resolve instead of failing: re-read the merge ref, confirm the
new value still descends from the same head, and only fail when the candidate genuinely
does not match. Failing closed is right when the candidate is unknown; failing closed on a
value that is merely one poll stale is not.

This is the prerequisite for ever requiring `review-state-action-projection` as a merge
check. The companion decision item
`message-queue/needs-human/decisions/non-blocking-turn-on-the-merge-gate-this-repository-already-runs.md`
recommends requiring only `reconcile-and-test` today, and names this race as the reason
the other job is excluded.

## Acceptance criteria

- [ ] A candidate whose merge ref was recomputed while the job ran re-resolves and passes,
      proven by a test that simulates the recompute.
- [ ] A candidate that genuinely does not match the expected revision still fails.
- [ ] The retry is bounded — it never loops indefinitely against a provider that keeps
      returning a moving value.
- [ ] `python3 automation/tests/test_github_action_projection_workflow.py` passes, and
      `python3 automation/run_tests.py` reports 11/11 files passed.

## Links

- `.github/workflows/harness.yml` — `review-state-action-projection`
- `message-queue/needs-human/decisions/non-blocking-turn-on-the-merge-gate-this-repository-already-runs.md`
- `handbook/git-workflow.md` — stacked branches are the normal way to sequence work
