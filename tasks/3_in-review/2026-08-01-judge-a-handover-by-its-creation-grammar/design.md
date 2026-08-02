# Design notes — judge a handover by its creation grammar

**Status:** decided

## Problem

`handover_action_entry_version_for` returned one number that did two different jobs: it
selected which rejecting clauses apply *and* how the record's suffix must be spelled. It
computed that number as the highest entry version reachable from the candidate, so two
things that have nothing to do with the record's own history could raise it:

- a version **withdrawn** before the record existed. `Queue action-entry schema: v3` was
  activated at `03ec388`, withdrawn at `b4c6627` (the rule moved to its own liveness
  marker, and `HANDOVER_ENTRY_VERSIONS` shrank back to `("v1", "v2")`), then the number was
  reused at `219ae1f` for an unrelated label rename. Every record written after `03ec388`
  descends from a commit that once said v3.
- a version activated in **parallel history**, joined at the merge that admits the record.

Both make an immutable record fail a grammar that did not exist when it was written, and
the only repair the finding names is a byte change that `history/AGENTS.md` forbids. That
is unsatisfiable, so it makes any branch cut before a version bump permanently unmergeable.
`automation/AGENTS.md` and `history/AGENTS.md` both already forbid exactly this.

The parallel join is not junk, though. It exists so an agent cannot escape a newer
*rejecting* grammar by cutting a branch early, and that property must survive.

## Options considered

### Option A — move the label rename off the burned `v3`, and/or respect a withdrawal

Renumbering `219ae1f`'s rename to a fresh `v4` was **rejected on evidence**. Auditing every
handover reachable from `main` against the marker in its own creation snapshot gives 27
`v1`+old-suffix, 26 `v2`+old-suffix, 11 pre-marker, and one `v3`+new-suffix record
(`2026-08-01-1030PDT-stop-human-answers-from-gating-git-edges`, created at `9c0c7e6`).
That record's creation snapshot says `v3` and it uses the new labels; renumbering the rename
would break it. Every author wrote to the marker in their own tree, so the marker at the
record's own commit is the ground truth — which is also the "respect a withdrawal" half of
this option, and it subsumes it: a declared marker already accounts for every activation
*and* withdrawal on that line of history.

### Option B — stop the parallel join from re-versioning an immutable record

Correct, but on its own it is either too weak (drop the join and a branch cut early escapes
v2's rejections) or still broken (keep the join and the record is still respelled).

### Option C — rewrite the record's bytes

Forbidden by `history/AGENTS.md`. Not considered further.

## Chosen

**A and B, split along what a committed record can still satisfy.** One number became two:

- **Rejection floor** — unchanged behaviour, `handover_schema_version_for`. The highest
  version the admission edge raises, including parallel history joined with an activation.
  It selects whether strict entry checking applies at all and which rejecting clauses fire.
  It only ever ratchets *up*, so it can never demand bytes the record lacks, and cutting a
  branch before a rejecting version still cannot escape that version.
- **Written grammar** — new, `handover_creation_contract_version`. The marker in
  `history/AGENTS.md` at the record's own creation commit. It selects one thing: how the
  suffix is spelled. This is the obligation an immutable record can never satisfy after the
  fact, so it is fixed at creation and no later or parallel commit may raise it.

The range path now agrees with the staged path, which already read the creation snapshot,
and with `LEGACY_HUMAN_PROJECTION_FIELDS`, where a queue item's own pre-rename spelling is
already valid forever.

The same split exposed a second contract contradiction: the two v2 rejecting clauses were
gated on `entry_version == "v2"`, so a v3 floor switched them **off** — while
`history/AGENTS.md` says "version 3 keeps both". They now fire at v2 *or later*, which is
what keeps the anti-dodge ratchet turning past a rename. `test_v3_admission_keeps_every_v2_rejection`
and the `("v2", "v3")` case of `test_a_branch_cut_early_cannot_evade_a_later_rejection`
both failed before this change.

**Deliberately out of scope:** `handover_liveness_version_for` still uses the floor. The
same unsatisfiability is possible in principle — retroactive liveness narrowing would ask
an immutable record to *drop* an entry — but no reproduction exists on `main` or in the
PR #44 range, and narrowing liveness governance without evidence would weaken a live check.

## Core fit

**Agent substitution:** pass — the rule is computed from Git history and two Markdown
markers by `reconcile.py`. No agent runtime reads, writes, or influences it; any runtime
that commits a handover gets the same verdict.
**Provider substitution:** not-applicable — nothing here touches a hosting provider. The
merge boundary is passed in as `--range`/`--at-transition` by whatever adapter runs it.
**Repository substitution:** pass — any adopting repository that keeps `history/` accrues
immutable records and eventually bumps a schema version. Without this split, its first
version bump strands every branch cut before it, with no permitted repair.
**User-global writes:** none
**Why AgentFold core:** this is the reconciler's own invariant about its own record
schema — it is the referee, not local config, not a product service, and not something a
plugin could own without owning the check itself.
**Thin adapter:** none
