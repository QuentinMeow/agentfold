# Stop a merge from borrowing a claim across an absence

**Claimed-by:** unclaimed
**Filed:** 2026-09-04, by claude, from `memory/decisions/2026-09-04-cap-the-restack-task-at-its-acceptance-criteria.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-stop-a-merge-from-borrowing-a-claim-across-an-absence.md`

## Goal

`claimed_lifecycle_problem` decides whether a queue item was committed as claimed before it was deleted. On a linear history it stops at the item's absence, so a claim from an earlier incarnation cannot justify a later deletion; at a merge it accepts a claim from any parent, so a claim reachable only through a parent that never carried the deleted incarnation can be borrowed across an absence boundary. This is an ordinary-path defect shared by every caller, found during the 2026-09-04 design review of the restack repair and deliberately left out of that task.

## Acceptance criteria

- [ ] [derived] WHEN a merge deletes a queue item and the only claim in its ancestry belongs to an earlier incarnation reachable through another parent, THE RECONCILER SHALL report the deletion as unclaimed — because a claim must bind the incarnation it deletes.
- [ ] [derived] WHEN the claim and the deletion sit on the same lineage across a merge, THE RECONCILER SHALL still accept the deletion, proven by fixtures for both shapes with one observed-red mutation — because the repair must not refuse a legal merge.
- [ ] [derived] `PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1` and `python3 automation/reconcile/reconcile.py --check` pass with real output in `verification.md` — because the root guardrails forbid fabricated results.

## Links

- Decision that named this follow-up: `memory/decisions/2026-09-04-cap-the-restack-task-at-its-acceptance-criteria.md`
- The repair this follows: task `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion`, its 2026-09-04 design amendment
