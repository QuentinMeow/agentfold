# Design notes — Stop a restack from being blamed for another branch's deletion

**Status:** decided

## Problem

`check_queue_resolution` (the reconciler's check that a force-push does not discard a live
queue action) built one synthetic edge from the displaced tip to the new head and blamed every
path present on the old tip and absent on the new head on the force-push, with a constant
message. A branch cut while action A was live, then restacked onto a base where another branch
had resolved A with a committed claim and changed evidence, was refused although its only
commit touched `PROBE.md`. The protection had to survive: a force-push that genuinely loses an
action stays refused, and a base deletion without its own evidence stays visible.

## Options considered

### Option A — evidence-validated continuity repair (chosen)
Explain each such path from real history using only existing helpers: require one merge base
`C` of old tip and new head; require the old tip's tree entry to equal `C`'s (the old lineage
never authored or changed the action, else keep the constant finding); walk every real parent
edge in `C..N` without the activation skip; skip edges where a merge merely adopted another
parent's absence (`candidate_paths_match_other_parent`); validate each real deletion edge with
`queue_deletion_problem` and report an invalid one by its commit; follow identity-preserving
timing renames; stay silent only when one validated edge deleted the same
`queue_action_identity`. *Example consequence:* the task's reproduction passes; a base that
deleted the item without a claim is reported as "inherited deletion <commit> lacks its own
lifecycle evidence" with the fix aimed at the base.

### Option B — other-parent tree equivalence alone
Reuse `candidate_paths_match_other_parent` on the synthetic edge. Rejected: it is evidence-blind,
so a valid base resolution and an unclaimed base deletion look the same and a bad deletion would
launder through a restack. Option A keeps the guard and adds the evidence check it lacked.

### Option C — a standalone provenance classifier ("Strategy A/U")
Immutable old/new endpoints, supplier and direct event modes, identity multimaps, receipts,
counters, and a separate command. Rejected on 2026-09-04: none of its 35 amendments served an
acceptance criterion, its selected contract explicitly left the `--displaced-tip` path unchanged,
and its fifteenth prototype revision failed three fresh reviews on concrete defects. The full
history is preserved under the annotated tags
`archive/2026-09-04-restack-provenance-design-history` and
`archive/2026-09-04-production-contract-poc-v15`, never on `main`.

## Chosen

Option A, as `continuity_deletion_problem` called from the continuity branch of
`check_queue_resolution`, with twelve `continuity` tests. Two deliberate differences from Option
C are accepted: a byte-identical delete-and-recreate on the old lineage, and a reintroduction
followed by a valid re-deletion, are silent, because the queue contract treats an evidenced
real-edge deletion of the same action text as a resolution.

**Was the missing guard deliberate?** The constant finding and `committed_queue_deletion_events`
both entered in `91e0ad2` (2026-07-23, task `2026-07-23-first-class-message-queue`) with no
rationale in the message (`git log -S'divergent update discarded a live old-tip action' --
automation/reconcile/reconcile.py`). The guard `candidate_paths_match_other_parent` arrived a
day later inside merge `d7eefcee` (`git log --all -m -S'def candidate_paths_match_other_parent'`
lists it against both of that merge's parents and no other non-merge commit). No decision
record, test, or comment excluded the guard from the continuity path. Reading: the continuity
edge was deliberately a raw preservation check with no parent set to consult, and the guard's
absence there is an omission, not a decision.

**Follow-ups filed, not widened into this task:** the continuity *mutation* stream still lacks
the same discriminator (`2026-09-04-judge-inherited-queue-mutations-on-their-real-edges`), and
`claimed_lifecycle_problem` can borrow a claim across an absence boundary at a merge
(`2026-09-04-stop-a-merge-from-borrowing-a-claim-across-an-absence`).

## Core fit

**Agent substitution:** pass — the rule reads committed repository objects and the existing queue authority only, so another agent runtime preserves the behaviour
**Provider substitution:** not-applicable — no hosted-provider state participates in identity, authority, or attribution
**Repository substitution:** pass — any adopted repository using AgentFold's queue and rewritten-history gate needs the same false-accusation protection
**User-global writes:** none
**Why AgentFold core:** rewritten-history queue preservation and lifecycle authority are reconciler invariants, not local configuration, a product service, private overlay, or separate plugin
**Thin adapter:** none
