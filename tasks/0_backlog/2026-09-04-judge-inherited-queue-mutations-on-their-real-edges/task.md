# Judge inherited queue mutations on their real edges

**Claimed-by:** unclaimed
**Filed:** 2026-09-04, by claude, from `memory/decisions/2026-09-04-cap-the-restack-task-at-its-acceptance-criteria.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-judge-inherited-queue-mutations-on-their-real-edges.md`

## Goal

The reconciler's displaced-tip check now explains an inherited queue *deletion* from the merge base and validates the real deletion edge, but the sibling *mutation* stream on the same synthetic old-tip-to-new-head edge is still a raw two-tree diff. A base-side identity change that the base's own gate admitted with edge context (a claim edge, a folded human answer, a sanctioned migration) can therefore still be attributed to a restacked branch as a rewritten live action. The same discriminator the deletion path uses closes the gap: one merge base, an old-tip copy unchanged since it, and validation of the real base-side edge.

## Acceptance criteria

- [ ] [derived] WHEN a branch is restacked onto a base that mutated a queue item through its own admitted edge, and the branch never touched `message-queue/`, THE RECONCILER SHALL emit no continuity mutation finding — because the deletion repair leaves this symmetric false accusation in place.
- [ ] [derived] WHEN a force-push genuinely rewrites a live action the old tip carried, THE RECONCILER SHALL still report it, proven by an observed-red mutation of the new guard — because the protection must survive.
- [ ] [derived] `PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1` and `python3 automation/reconcile/reconcile.py --check` pass with real output in `verification.md` — because the root guardrails forbid fabricated results.

## Links

- Decision that named this follow-up: `memory/decisions/2026-09-04-cap-the-restack-task-at-its-acceptance-criteria.md`
- The repair this follows: task `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion`, its 2026-09-04 design amendment
