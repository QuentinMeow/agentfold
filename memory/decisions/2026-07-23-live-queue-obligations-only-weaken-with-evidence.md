# Live queue obligations only weaken with boundary or provider evidence

**Status:** decided
**Date:** 2026-07-23
**Decided-by:** agent (delegated two-way-door lifecycle hardening after independent adversarial review)
**Description:** Live timing only escalates, future boundaries survive renames, and a provider source's final binding remains until trusted release evidence
**Review-by:** 2027-02-28

## Context

The queue-first lifecycle allowed a live item to change timing whenever its filename
and timing fields changed together. It also allowed a source-bound item to disappear
after ordinary completion evidence without asking whether the provider still exposed
the exact source. Two adversarial examples turned those conveniences into bypasses:
an approved future review could become `non-blocking-*` before deletion, and a live
comment could lose its only queue binding on a push that did not replay provider state.
A candidate-local two-parent commit could also imitate the merge receipt expected after
a future review.

The actor/kind/timing model remains decided in
`memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`; this decision
defines what evidence permits a live obligation to weaken.

## Decision

A live timing identity is monotonic:
`non-blocking` → `future-blocking` → `blocking`. To weaken timing, resolve the original
under its existing lifecycle and create a distinct authorized replacement; do not
relabel the live identity. Any concrete human response freezes timing. Deletion follows
the item's lineage, so a historical future boundary survives a later escalation.

A future merge receipt authorizes cleanup only when its exact two-parent merge already
exists in the trusted adapter-supplied target base. Candidate-local topology and a root
range do not prove prior admission. No-range local hooks remain a convenience check;
the protected exact-range adapter owns hard assurance.

For a versioned `External source`, removing the final live binding requires a closed
current/released classification from trusted provider state at the exact base/candidate
boundary. Current or unavailable state blocks. An edit or supersession releases the old
identity only when the candidate already binds the provider's current replacement;
deletion, artifact closure, dismissal, or thread resolution may release without a
replacement. The provider-neutral gate consumes opaque classifications; thin adapters
own provider lookup semantics.

## Alternatives considered

- Allow arbitrary timing renames — useful for correction, but lets an agent erase a
  future dependency without human or boundary evidence.
- Trust any two-parent commit in candidate history — Git-first, but cannot distinguish
  a local imitation from a merge already admitted to the target.
- Replay provider state only on later provider events — eventually detects an orphan,
  but admits the deletion first and leaves the default branch invalid meanwhile.
- Reject every source-bound deletion forever — safe but turns the live queue into an
  archive and prevents normal cleanup after a provider releases the source.

## Consequences

Correction uses a new identity instead of weakening a live one. Provider adapters gain
one narrow responsibility: classify every disappearing source identity, failing closed
when lookup is unavailable. Protected required checks or pre-receive enforcement are
still necessary because a post-push failure cannot undo a direct write. The core
remains provider-neutral and future agents may replace the adapter without changing the
queue schema.
