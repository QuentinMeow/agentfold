# Should AgentFold turn on GitHub-enforced final tests, or keep them manual?

**Status:** waiting
**Filed:** 2026-07-27, by codex, from task `2026-07-27-configure-test-gates-and-time-budgets`
**Action:** Decide whether GitHub should automatically block a merge until the complete tests pass. Choose Option A to turn that protection on, or Option B to keep the final test as a manual check.
**Full context:** `handbook/testing-gates.md`
**Why-you-might-care:** Option A prevents a pull request from merging into `main` when the complete tests are missing, failing, or no longer match the code to be merged. Option B relies on a maintainer to run and check those tests.
**If-you-do-nothing:** Keep the complete final test manual. Do not say that GitHub enforces it automatically.
**Resolution evidence:** `memory/decisions/2026-07-27-github-hard-test-gate-activation.md`

**Blocks at:** transition:activate-github-hard-pull-request-gate
**Until then:** The implementation may be completed and merged, but no GitHub rule may rely on this status and no one may claim that the pull-request gate is automatically enforced.

## What you need to know

This choice controls what happens when someone tries to merge a pull request.

- With Option A, GitHub refuses to merge until the complete tests pass for the exact code that
  would enter `main`.
- With Option B, a maintainer runs and checks the complete tests, but GitHub does not stop the
  merge if that step is missed.

The test runner is ready, but GitHub has not yet been configured to enforce its result. Until
the one-time setup below is completed and checked, a green workflow or local test result does
not prove that GitHub will block an unsafe merge.

## Differences

Option A adds an automatic stop inside GitHub and requires one-time setup. Option B needs no
new GitHub setup, but it depends on a maintainer remembering to run and check the final test.

## Your options

### Option A — Set up and activate the GitHub gate

Choose this if you want GitHub to block unsafe merges automatically. The one-time setup is:

1. Create a private GitHub App whose only job is to report whether this final test passed.
   Install it only on the QuentinMeow/agentfold repository. Give it
   `Commit statuses: read/write` and the automatic `Metadata: read` permission. Do not give it
   write access to checks, repository contents, pull requests, Actions, workflows, deployments,
   or issues.
2. Create a protected place for the App credentials. GitHub calls this an *environment*; name
   it `agentfold-trusted-publisher` and allow only the exact `main` branch to use it, with no
   tag pattern. Store the App client ID there as `AGENTFOLD_PUBLISHER_CLIENT_ID` and its private
   key as `AGENTFOLD_PUBLISHER_PRIVATE_KEY`. Pull-request test code does not receive that key.
3. After the supplied workflow is present on `main`, open a temporary pull request and run the
   complete test. Confirm that the private App reports `AgentFold trusted hard final gate` for
   the exact version GitHub would merge.
4. Protect `main` so that it requires pull requests, requires branches to be current, and
   requires that named result from the private App. Allow no direct pushes, force pushes,
   deletion, or bypasses. Keep merge queues disabled because this workflow does not cover that
   separate merge path.

*Example consequence:* After setup, a pull request cannot merge when the complete tests fail,
when the result is missing, or when `main` has changed since the result was produced.

### Option B — Keep final tests manual

Choose this if you prefer not to do the GitHub setup. Do not create the App, protected
environment, or new merge rule. Continue to run the complete final test deliberately before
important merges, and do not say that GitHub enforces it automatically.

*Example consequence:* The complete test remains available, but GitHub will not prevent a merge
when its result is missing or failing.

## Recommendation

Option A. It turns the complete test into an automatic merge safeguard while limiting the
private App to reporting that one result.

**Your answer:** ______
