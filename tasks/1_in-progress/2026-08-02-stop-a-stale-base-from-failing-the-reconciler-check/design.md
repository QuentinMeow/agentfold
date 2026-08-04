# Design notes — stale-base pull-request admission

**Status:** decided

## Problem

On a `pull_request` event, `actions/checkout` resolves GitHub's mutable merge ref when the
job starts. If the base branch advanced after the event was emitted, the checked-out merge
candidate can have the event head as its second parent and a newer base as its first parent.
The old adapter still passed `event_base...event_head`. The reconciler (the script that
checks every repository invariant) correctly refused that mismatch because checked-out
`HEAD` was neither the range head nor an exact merge of those two endpoints.

The invariant to preserve is stronger than "the candidate contains the pull request's
changes": the candidate must prove, through its own object identity, that it merges this
event's head onto a base that contains this event's base. An unrelated checkout must still
fail before repository policy runs.

## Options considered

### Change the reconciler to accept descendant first parents

Teach `validate_range_candidate` that any two-parent merge whose first parent descends from
the declared range base is valid. This would make a provider race part of the canonical Git
snapshot policy and weaken every caller, including callers that did not resolve a mutable
provider ref.

### Re-fetch the merge ref with a bounded retry

Copy the review-state adapter's five-attempt resolution loop and check out whatever the ref
names last. This is internally inconsistent here: `actions/checkout` has already selected
the immutable candidate, and the earlier core-scope step has already inspected that tree.
Changing the checkout afterward would make two gates judge different candidates.

### Bind the checked-out candidate in the pull-request adapter

Keep the direct-head fast path. Otherwise require exactly two parents, require parent two
to equal the event head, and require parent one to contain the event base. Pass
`actual_parent1...event_head`, so the reconciler independently validates checked-out `HEAD`
as the exact synthetic merge of those two range endpoints and computes scope from the pull
request leg.

## Chosen approach

Bind the already checked-out candidate in `.github/workflows/harness.yml` and leave
`automation/reconcile/reconcile.py` unchanged. This reuses the parent-interrogation approach
already used by the authoritative, source-release, and review-state adapters without
making provider timing canonical policy.

There is no retry in this step. The task's bounded-retry criterion is not applicable because
this boundary never resolves a mutable ref: `actions/checkout` has already pinned `HEAD`.
The literal-block fixture asserts the step contains no polling loop, sleep, pull-ref fetch,
or attempt variable. Malformed candidates and payloads fail immediately.

For example, with event base `B`, advanced base `B2` where `B` is an ancestor of `B2`, event
head `H`, and checked-out candidate `M(B2,H)`, the adapter now emits `B2...H`; the reconciler
accepts `M` only because its parents are exactly `{B2,H}`. A candidate `M(B2,H2)` still
fails because its second parent is not `H`.

## Core fit

**Agent substitution:** pass — the change reads only Git commits and event revisions; it does not inspect the agent, prompt, transcript, or runtime that produced the branch
**Provider substitution:** pass — parent-shape binding is plain Git, while `.github/workflows/harness.yml` remains the replaceable GitHub adapter that supplies its provider's event base and head
**Repository substitution:** pass — any adopted repository can encounter a base advance between a pull-request event and merge-candidate checkout, and no AgentFold content or product service is named
**User-global writes:** none
**Why AgentFold core:** this repairs the correctness of the repository-wide pull-request admission adapter registered in `automation/core-scope-paths.txt`; an overlay cannot fix the candidate/range contract before the canonical gate runs
**Thin adapter:** canonical=automation/reconcile/reconcile.py; optional=yes; policy=none; writes=repo-only

## Undo cost

Reverting the workflow and its fixture restores the stale-base false failure. No schema,
repository data, provider setting, or irreversible migration changes.
