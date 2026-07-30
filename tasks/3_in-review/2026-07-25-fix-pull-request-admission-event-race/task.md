# Make the two admission checks pass on a freshly opened pull request

**Claimed-by:** claude
**Filed:** 2026-07-25, by claude, from the CI failure observed while opening pull request 13 for task 2026-07-25-mine-markdown-cochange-couplings
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Both required admission checks in `.github/workflows/harness.yml` fail on every newly
opened pull request, and they fail for the same reason: on the `opened` event GitHub has
not yet computed the pull request's merge commit, so `merge_commit_sha` arrives empty in
the webhook payload while `refs/pull/<number>/merge` already resolves.

The workflow subscribes to `opened` at lines 5 and 7, so both jobs run on that event.

**Job `authoritative-external-action-projection` (line 91).** Line 134 binds
`ACTION_PROJECTION_EXPECTED_REVISION` to `github.event.pull_request.merge_commit_sha`
with an empty-string fallback. The step at lines 135-147 fetches the merge ref, then at
line 142 runs `test -n "$ACTION_PROJECTION_EXPECTED_REVISION"` under `bash -e`. With an
empty value that test exits 1 and the job dies before the equality check at lines 143-144
is ever reached.

**Job `external-source-release-admission` (line 402).** Line 434 binds
`SOURCE_RELEASE_EXPECTED_CANDIDATE` to the same field, but its fallback is `github.sha`,
which on a `pull_request_target` event is the base-branch tip rather than the merge
commit. The step fetches `refs/pull/<number>/merge`, resolves the real merge commit, and
then at lines 445-446 compares it against that base-sha fallback. The two never match, so
the job fails on a value mismatch rather than on an empty value.

Observed on pull request 13. Workflow run 30176317631, fired by the `opened` event,
recorded `ACTION_PROJECTION_EXPECTED_REVISION:` as empty and
`SOURCE_RELEASE_EXPECTED_CANDIDATE: c32dc63ec1cd010c939acf450380a0f83e43943d`, which is
the tip of `main` and not the merge commit; both jobs exited 1 at the fetch step. Run
30176383251, fired by a later `edited` event on the same unchanged head, passed both.

Re-running a failed run does not help: GitHub replays the original webhook payload, so the
same empty and stale values return. Only a fresh event recomputes them. The workaround
used on pull request 13 was to edit the pull-request body to trigger an `edited` event.

The trigger is not limited to `opened`. Pull request 14 hit the identical failure on a
`synchronize` event, after a push to an already-open pull request, and `edited` cleared it
there too. So the payload is stale whenever the merge commit has not been recomputed yet,
which a push causes as surely as an open does; a repair keyed to the `opened` event alone
would leave the second, more frequent case red.

The consequence is that the two gates which bind pull-request prose and external-source
bindings to an immutable candidate are red on arrival for every pull request, which
trains readers to treat a red required check as normal. Retrying by hand is not a fix,
and neither is dropping the guard: an empty or stale expected revision is exactly the
state in which an unverified candidate could be admitted, so the repair has to fail
closed when the merge ref is genuinely unavailable rather than skip the comparison.

The two jobs also differ in how they fail today, and both behaviours are in scope. The
projection job's fallback is an empty string that its own guard catches; the
source-release job's fallback is a real but wrong revision that no guard distinguishes
from a legitimate one.

## Acceptance criteria

- [ ] A pull request opened fresh from a branch, with no manual event, no re-run, and no
      body edit, completes both `Authoritative action projection from trusted workflow
      code` and `External source release admission` successfully, and the run URL is
      recorded in `verification.md`
- [ ] A push to that already-open pull request completes both checks on the resulting
      `synchronize` run, with no manual event and no re-run, and its run URL is recorded
      in `verification.md` alongside the `opened` one
- [ ] WHEN the payload carries no merge revision, THE WORKFLOW SHALL obtain the candidate
      from a provider source that is authoritative at that moment rather than treating the
      base-branch revision as the candidate
- [ ] WHEN the merge revision is genuinely unavailable — the pull request is unmergeable,
      the merge ref does not resolve, or the provider does not answer — THE WORKFLOW SHALL
      fail the job rather than skip, weaken, or pass the comparison, and `verification.md`
      records a real run demonstrating that closed failure
- [ ] The candidate a passing run admits is the same immutable merge commit the equality
      check binds today; the repair changes when the expected value is known, not what it
      is compared against
- [ ] The source-release job no longer treats `github.sha` as an acceptable expected
      candidate on a `pull_request_target` event, and `verification.md` shows the two
      values differing in a real payload
- [ ] `python3 automation/reconcile/reconcile.py --check` exits 0 and
      `python3 automation/run_tests.py` passes, with both outputs recorded in
      `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt, because
      `.github/workflows/harness.yml` is registered in `automation/core-scope-paths.txt`

## Links

- The workflow holding both jobs: `.github/workflows/harness.yml`
- Registration that makes it a core path: `automation/core-scope-paths.txt`
- The checker both jobs invoke: `automation/check_action_projection.py`
- Provider-boundary rules the jobs implement: `handbook/git-workflow.md`
- The pull request whose opening exposed this: 13, on the task branch for
  2026-07-25-mine-markdown-cochange-couplings
