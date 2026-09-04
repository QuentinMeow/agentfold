# Cap the restack task at its acceptance criteria and park the classifier line

**Status:** decided
**Date:** 2026-09-04
**Decided-by:** agent (delegated: the owner asked on 2026-09-04 that the handed-off design be reviewed and revised or pushed back as needed; two-way door — nothing is deleted, and the parked line can be reopened as its own task)
**Description:** The restack false-accusation task is fixed by the minimal evidence-validated continuity-edge repair; the 35-amendment classifier design and the v11–v15 production-contract POC line are parked as design history, not gates
**Review-by:** 2027-03-03

## Context

Task `2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion` was filed to
stop the reconciler from blaming a restacked branch for a queue deletion its new base made with
evidence. Its task file localised the root cause to two functions and six acceptance criteria.
Between 2026-08-31 and 2026-09-03 the work grew into a 5,619-line design with 35 dated
correction amendments, four proof-of-concept programs of 26,370 lines, and fifteen revisions of
a "production-contract" prototype, while production code stayed unchanged. On 2026-09-04 a
nine-reviewer design review found: the owner's request never asked for that machinery; the
label "Strategy A" had drifted from the owner's answer about task-claim publication to the name of
the classifier design; the selected classifier contract left the defective code path unchanged;
and revision v15 (7e47b5b) failed all three fresh reviews on concrete defects (a frozen fixture
clock on the public path, an evidence audit bound to one machine's Git binary, a `git rev-parse
HEAD` dependency inside the audited path). An executed reproduction showed a 54-line repair that
removes the false accusation while still reporting a genuine loss and an unevidenced base deletion.

## Decision

The task is capped at its six acceptance criteria. Production gets the minimal repair: each
deletion on the displaced-tip continuity edge is explained from the unique merge base, the real
deletion edge on the new head's side is validated with the existing lifecycle rules, an invalid
inherited deletion is reported naming its commit, and the constant accusation survives only when
the old lineage authored or changed the action or no evidenced resolution exists. Amendments
1–35, the standalone `ref_update` core, the semantic composition plan, and the v11–v15
production-contract line are parked design history: kept in the branch, the run record, and the
v15 worktree, never re-baselined and never required by any acceptance criterion. The queue item
that bound future sessions to a 3/3 acceptance of v15 is resolved by this record.

## Alternatives considered

- Repair v15 and restart its panel at 0/3: rejected — no acceptance criterion needs the
  classifier, its selected contract does not fix the defect, and each prior repair round added
  scope that the next panel blocked.
- Continue the semantic composition and "freeze Strategy A" phases: rejected — agent-derived
  phases with no owner sentence behind them.
- Delete the parked artifacts: rejected — records are immutable and the evidence remains useful.

## Consequences

The false accusation stops on the task's own reproduction; the genuine-loss protection stays;
the task can publish as one pull request. Reopening the classifier line is a new task traced to
a confirmed goal, not a continuation. Two follow-ups are filed separately: any-parent claim
borrowing in `claimed_lifecycle_problem`, and the same missing guard on the continuity mutation
group.
