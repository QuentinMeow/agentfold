# Should a pull request be allowed to merge while its own checks are failing?

**Action:** Decide whether the repository should refuse to merge a pull request whose `reconcile-and-test` check has not passed, and say which of the options below you want.
**Why this matters:** Every safety rule in this repository is currently a suggestion — the checks run, they can go red, and the merge button works anyway.
**If you do nothing:** The checks keep running and keep being ignorable, and a branch that goes red can still land on `main` exactly as one did on 2026-08-01.

## What you need to know

**Today:** Nothing is enforced. There is one rule set on this repository, named
`main-projection`; it is switched off, and even switched on it would only stop branch
deletion and force-pushes. No check is required, so any pull request can be merged at any
time regardless of what the checks say.

**What this would change:** One check — the one that runs the reconciler and the test
suite on every pull request — becomes required, so the merge button is disabled until it
is green.

**What this does not decide:** Nothing about how code is reviewed, nothing about who may
approve a change, and nothing about the other three checks this repository runs. Those
three are deliberately left out below, and the reason is that requiring a check which
sometimes does not run at all would leave pull requests waiting forever for a result that
never arrives.

This is not a hypothetical. On 2026-08-01 a change was merged while its own checks had
been failing for 47 minutes, and the main line went red behind it. Nothing prevented that,
and nothing prevents it happening again today.

I cannot make this change myself. It lives in a settings page on the hosting provider,
outside the repository, and no commit can create it or prove it is still there.

## Differences

The options differ on one thing: whether a red check can be overruled by clicking merge,
and by whom.

### Option A — Require the check, with no way around it
Turn the existing rule set on and mark that one check required, with nobody exempt.
*Example consequence:* A change whose tests fail simply cannot be merged until they pass.
If the check itself breaks — an outage at the hosting provider, say — nothing merges until
it is fixed, including the fix.

### Option B — Require the check, but let yourself bypass it
The same, except you personally can still merge past a red check when you judge it
necessary.
*Example consequence:* You are never locked out of your own repository, and a broken check
is an inconvenience rather than a stoppage. The cost is that the guarantee is now "red
changes do not land unless Quentin decides otherwise", which is weaker but honest.

### Option C — Leave it off
*Example consequence:* Everything continues exactly as it does now. The checks stay useful
as information — an agent still reads them and still repairs what they report — but a
merge is never actually stopped, and the 2026-08-01 failure stays possible.

## Recommendation

**Recommendation:** Option B — it removes the failure that actually happened while leaving
you an exit, and the exit is visible in the record whenever it is used.
**Strongest case against this:** A bypass that exists gets used under time pressure, which
is precisely when a red check is most likely to be right; Option A is the only version
that cannot be talked out of.
**Confidence:** high — I read the rule set through the provider's API and confirmed it is
switched off with no required checks, and I confirmed which check runs unconditionally on
every pull request. I did not test what the merge button actually does once a check is
required, because I cannot change that setting.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will show
you how it read your words before acting.

**Your answer:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-08-01, by claude, from task `2026-08-01-stop-human-answers-from-gating-git-edges`
**Full context:** `handbook/git-workflow.md`; `memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md`
**Resolution evidence:** `roadmap/current-state.md`
**Answer by:** 2026-10-30

The provider ruleset is `main-projection` (id 19582703), `enforcement: disabled`, rules
`deletion` and `non_fast_forward` only. The candidate check is `reconcile-and-test`, whose
`if:` is `github.event_name == 'push' || github.event_name == 'pull_request'`, so it is the
only job that cannot be skipped on a pull request. The other three
(`authoritative-external-action-projection`, `review-state-action-projection`,
`external-source-release-admission`) are conditional on narrower event sets; a required
check that can be skipped stays pending forever, so they are excluded until their
conditions are widened. Do not enable "require branches to be up to date": it serialises
the trunk and invalidates every stacked layer on each parent merge.
