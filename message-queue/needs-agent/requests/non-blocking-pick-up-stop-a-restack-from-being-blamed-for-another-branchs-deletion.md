# Pick up stopping a restack from being blamed for another branch's deletion

**Status:** open
**Filed:** 2026-08-02, by claude, from an adversarial review of pull request #65 that reproduced it deterministically
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion/task.md`
**Request kind:** task-pickup
**If unanswered:** Restacking a branch onto current `main` keeps producing a blocking finding accusing it of discarding a queue action it never touched, and the only repair is to force-push again — which is how agents learn to disregard a check that is sometimes right.

## What you need to know

`--displaced-tip` is passed on every force-push, and restacking onto a newly merged parent
is what the git workflow calls expected, so this fires on ordinary work. A branch whose only
commit touched `PROBE.md` was restacked over a commit where another agent had properly
resolved a queue item, and the reconciler blamed the restacking branch for discarding it.
Dropping `--displaced-tip` from the same command returns zero findings.

`committed_queue_deletion_events` is a plain two-dot diff between the displaced tip and the
new head, so a deletion inherited from the moved base looks identical to one this branch
made. The non-continuity path guards with `candidate_paths_match_other_parent`; the
continuity path has no equivalent.

The protection itself is real and must survive: a force-push must not be able to quietly
discard a live action. The distinction to draw is between an action the branch discarded and
one the new base resolved legitimately with its own evidence.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
