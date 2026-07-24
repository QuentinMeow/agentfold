# May Codex push the stacked-review coordination commits directly to main?

**Status:** folding
**Blocking:** yes — operation:publish-stacked-review-prs is stopped
**Filed:** 2026-07-24, by codex, from the stacked-publication session
**Action:** Approve or decline pushing the coordination-only commit sequence directly to origin/main before Codex publishes the three dependent pull requests.
**Full context:** [Git workflow](handbook/git-workflow.md)
**Why-you-might-care:** The repository requires task claims, queue lifecycle, owner decisions, and handovers on main immediately, while the instruction to create sequential PRs did not explicitly authorize a shared-branch push.
**If-you-do-nothing:** The implementation branches and repairs remain preserved, but Codex does not publish the stack with stale canonical task and queue state.
**Resolution evidence:** `roadmap/current-state.md`

## What you need to know

The local sequence contains no implementation code. It publishes PR #7's review task
state, replays the detector response through its original status edges, admits and
claims the isolation task before moving it to review, claims the layered-workspace
task, and assigns publication of its six preserved follow-ups.

Every edge is separate because PR #7's joined-history checks validate lifecycle, not
only the final tree. The repository's Git workflow assigns these records to main
instead of a reviewed-system branch, so direct push authority is required.

## Differences

- **Approve:** publish only the live coordination sequence to main; implementation
  remains in the three bottom-up PR layers.
- **Decline:** leave origin/main unchanged and stop while a different coordination
  strategy is designed and reviewed.

## Options

### Option A — Approve direct coordination push

Codex pushes the lifecycle-only commits to origin/main. It then incorporates that
base through merge commits, without rebasing or rewriting the task branches.

*Example consequence:* PR #7 remains the first implementation PR while all three
tasks and their pending review boundaries are discoverable from main.

### Option B — Decline

Codex preserves every local and remote task branch but does not open the new dependent
PRs.

*Example consequence:* Existing PR #7 remains unchanged and the two new layers remain
unpublished.

## Recommendation

Option A, because it follows the repository's explicit live-coordination lane without
publishing reviewed-system implementation outside PRs.

**Your answer:** Approve direct coordination push
