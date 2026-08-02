# Design notes — report work back to the owner

**Status:** decided

## Problem

An agent could finish a task, move it to `3_in-review`, write a handover, and stop. The
branch stayed on the machine it was built on, and the owner learned nothing until they went
looking. Two separate gaps caused that, and both were in the same ritual.

The first is publication: the end-of-session ritual listed six things to write and never
said to push or to open a pull request. The second is reporting: the ritual required the
final reply to repeat the owner's open queue items, but said nothing about telling them what
changed, what an agent decided on their behalf, or what those decisions would cost to undo.

The owner's account of the result: *"Every time I have to ask what do I need to do, and I
have to ask what's this and what's that."*

## Options considered

### Option A — Add publish and report as ritual steps
Two steps at the end of the existing ritual, each pointing at the file that owns its shape.
*Example consequence:* the session that finishes a task ends with a pull request the owner
can open and a reply they can act on; if either is missing, the ritual was not completed and
the handover says so.

### Option B — Make a check enforce it
Have the reconciler refuse a task's move to `3_in-review` without a pushed branch.
*Example consequence:* an agent working offline, or one whose push is legitimately deferred,
cannot record honest progress; and the check cannot see chat at all, so half the gap stays
unenforceable anyway. The proxy is weaker than the rule.

### Option C — Leave publication to the human
*Example consequence:* the owner keeps discovering finished branches by running
`git branch -a`, which is exactly the state this task exists to end.

## Chosen

Option A. Publication is now step 8 of the ritual and reporting is step 9, both in
`skills/session-handover/SKILL.md` and summarised in the root `AGENTS.md`.

`handbook/git-workflow.md` gains the rule that makes step 8 actionable: a task branches from
`main` unless it needs something that exists only on another unmerged branch, in which case
it stacks on that branch and says so in the first thing in its body. The rule is stated as a
two-row table because the decision has exactly two inputs and agents were previously
inferring it from a sentence about conflict avoidance.

The reply originates nothing. Every item in its "what you owe" section is a projection of a
queue file that already exists, which is the same rule the handover follows — so the reply
cannot become a second action ledger.

## Why this is not enforced mechanically

The one honest proxy — "a task in `3_in-review` has a pushed branch" — punishes legitimate
states and still cannot see whether a reply was written or whether it was any good. A check
that can be satisfied without achieving the goal trains agents to satisfy the check. Whether
any of this should become machine-checked is a judgment for the owner, and it is filed as a
decision rather than assumed either way.

## Core fit

**Agent substitution:** pass — both new steps are prose in an agent-agnostic skill and the
root contract; neither names a runtime or a tool.
**Provider substitution:** pass — the ritual says "open its pull request", and which provider
serves that role is the adapter's business. `templates/pull-request.md` is provider-neutral;
only its GitHub projection is not.
**Repository substitution:** pass — every adopted repository whose agents work unattended has
the same gap between finishing and telling.
**User-global writes:** none
**Why AgentFold core:** the harness's stated contract in `async` mode is "never block
silently, never proceed silently". Finishing work without publishing or reporting it is
proceeding silently, so closing that gap is the mode's own definition, not a preference.
**Thin adapter:** none
