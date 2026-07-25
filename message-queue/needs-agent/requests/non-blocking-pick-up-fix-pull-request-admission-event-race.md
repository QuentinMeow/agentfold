# Pick up the pull-request admission event race fix

**Status:** open
**Filed:** 2026-07-25, by claude, from the CI failure observed while opening pull request 13 for task 2026-07-25-mine-markdown-cochange-couplings
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-07-25-fix-pull-request-admission-event-race/task.md`
**Request kind:** task-pickup
**If unanswered:** Every newly opened pull request keeps showing two failed required admission checks until a later event re-fires them, and each author works around it by hand.

## What you need to know

On the `opened` event GitHub has not yet computed the pull request's merge commit, so
`merge_commit_sha` arrives empty. In `.github/workflows/harness.yml` the projection job
then fails an emptiness guard, and the source-release job compares the real merge ref
against a base-branch fallback that can never equal it. Both jobs are required checks, so
both are red on every fresh pull request.

Re-running the failed run replays the same stale payload and fails again; only a fresh
event fixes it. On pull request 13 the workaround was to edit the body to fire an
`edited` event, after which both jobs passed on the identical head commit. The exact line
numbers, the two differing fallbacks, and the observed run identifiers are recorded in the
task file, so no re-derivation from CI logs is needed.

The repair has to keep the gate closed: an unavailable merge revision must fail the job
rather than skip the comparison, because that is precisely the state in which an
unverified candidate could otherwise be admitted.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
