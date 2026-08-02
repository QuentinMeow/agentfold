# The merge gate stays advisory while the repository is immature

**Status:** decided
**Date:** 2026-08-02
**Decided-by:** owner (Quentin, in chat, transcribed verbatim before this record was written)
**Description:** No status check is required to merge; a red check informs but never stops a merge, because the repository is early and its development cycle is mostly agents, and the owner will require `reconcile-and-test` once he judges the repository stable
**Review-by:** 2027-02-02

## Context

Every safety mechanism this repository builds is enforced by `automation/reconcile/reconcile.py`
and its sibling gates, which run in CI on every pull request. None of them is a *required*
status check. The provider ruleset `main-projection` exists but is `enforcement: disabled`,
and carries only `deletion` and `non_fast_forward` rules. So a pull request may be merged
while its own checks are red.

That is not theoretical. On 2026-08-01 an agent merged a pull request whose checks had been
failing for 47 minutes. `main` went red at that commit and then reported green again 35
seconds later without anything being fixed — push-mode CI examines `before...head`, and two
later merges moved the window past the broken commit. The commit remains in history; only
the evidence disappeared.

The owner was shown three options: require the check with no bypass, require it with a
personal bypass, or leave it off. The agent recommended the middle option.

## Decision

Leave it off. Merging stays possible with a red check.

The owner's stated reason, transcribed verbatim from chat:

> "for task 1 let's keep it option C (i.e. allow merge even when CI is red). The reason is
> that this repo isn't yet mature and we want fast development cycle (mainly AI agents). I
> will switch to option B when I think this repo is stable."

This overrules the agent recommendation, which is the owner's prerogative and the reason the
question was asked rather than decided.

## Consequences

- Checks remain **information**, not gates. An agent still reads them and still repairs what
  they report; nothing mechanically prevents a merge.
- The 2026-08-01 failure mode stays reachable: a red change can land, and `main` can report
  green afterwards without a fix. Agents must therefore treat a green trunk as evidence about
  the last push window only, never as proof the trunk is sound. The standing mitigation is to
  verify the *merged result* before landing, not the branch alone
  (`memory/lessons/automation/green-branches-can-merge-to-red.md`).
- This is a recorded trade with a stated exit, not an oversight. When the owner judges the
  repository stable, the intended next state is Option B — `reconcile-and-test` required with
  a personal bypass. Nothing in the tree can detect or prove that switch, because it lives in
  a provider settings page.
- Requiring the other three checks stays out of scope: each is conditional on a narrower event
  set, and a required check that can be skipped stays pending forever.
