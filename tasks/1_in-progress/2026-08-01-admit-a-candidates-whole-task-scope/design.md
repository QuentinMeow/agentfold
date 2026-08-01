# Design notes — let a candidate carry more than one task

**Status:** decided

## Problem

Two gates require opposite things of the same commit, and six open pull requests sit in
the gap.

`check_queue_task_reciprocity` requires a live queue item declaring `task:<id>` to appear
in that task's `Queue actions`. `inferred_changed_task_id` then refuses any candidate whose
diff maps to more than one `tasks/<status>/<task-id>/` folder, with a hard input error.
Filing a queue item bound to another task therefore has no legal commit.

Classifying the six blocked pull requests showed the plural scope is not one accident:

| PR | Extra scope | Why |
|----|-------------|-----|
| #36 | `2026-07-22-severity-tiers-for-reconciler-findings` | its work shipped that task's criteria, so it checks them off there |
| #41 | three `3_in-review` tasks + one moved to `4_done` | the task's *product* is clearing queue items those tasks link |
| #42 | `2026-07-25-single-source-queue-prefix-rule` | a child task claimed on its parent's branch |
| #45 | `2026-07-23-first-class-message-queue` | the reciprocity backlink for the two items the range files |
| #46 | two `3_in-review` tasks | its own task record exists in no commit on any branch |
| #48 | four new `2026-08-01-*` backlog tasks | follow-ups the task filed for work it deferred |

Only #46 is a branch problem. The other five are shapes the lifecycle prescribes.

The merge boundary fails the same way. `check_active_queue_boundaries` fires
`transition:merge` against every task whose records the candidate touched, so a candidate
that *files* a `future-blocking … transition:merge task:<id>` action — which must, by the
reciprocity rule, also touch that task's record — is judged to have reached a boundary in
the range that created it.

## Options considered

### Option A — bind only the branch's declared task, cross-check membership
A task-named branch binds only the task it names; the inferred set need only contain it. Minimal, and it
mirrors what the reconciler already does for `--branch task/X`.
*Example consequence:* PR #42 carries the child task `single-source-queue-prefix-rule`
whose live human actions would never be projected, because the branch names the parent.
A live ask can hide behind a branch name.

### Option B — bind every task the candidate carries, project the union
Scope is a set; `required_paths` is the union of the scope's live scoped queue actions.
*Example consequence:* PR #41 must list all four live human actions owned by the three
in-review tasks it edits, instead of claiming "No queued action requested."

### Option C — leave the gate and split every branch
*Example consequence:* #41's task exists to clear queue items that live in other tasks'
records; splitting it produces a branch that cannot do its own job. #45 would need the
reciprocity backlink on a separate branch from the item it backlinks, which the reconciler
refuses on both halves.

### Option D — merge boundary: drop the successor rule's timing inheritance
`review_successor_problem` forces a successor's timing fields to match the review it
replaces byte-for-byte.
*Example consequence:* a `changes-requested` answer could be replaced by a successor that
quietly moves its boundary further out, which is the weakening
`message-queue/AGENTS.md` forbids. The rule is right; the boundary reading is wrong.

### Option E — merge boundary: skip an action the range itself filed
*Example consequence:* PR #45's two items were created inside its range and were never
pending before it, so they are not reported; both are still reported at every later
boundary they reach.

## Chosen

**B for scope, E for the boundary.**

B is strictly stronger than what it replaces: the old rule projected one task's actions,
the new one projects every task in the candidate's scope, so nothing a reviewer used to be
shown is now hidden. A task-named branch must still be *in* the scope, which keeps the
anti-mislabel guarantee that `test_cli_task_branch_rejects_conflicting_candidate_scope`
already asserts — and which is what still, correctly, refuses PR #46.

E is bounded twice. It applies only when a real `BASE...HEAD` range exists, and it matches
on `queue_action_identity` rather than path, so the permitted
`non-blocking` → `future-blocking` → `blocking` escalation is still the same pending action
and still reaches its boundary. It also applies only to an *unanswered* action: an action
carrying a committed human response is the boundary's receipt, and whether that receipt
still covers the candidate is exactly what the boundary validates.

The residue is stated rather than hidden: a merged candidate can now file an unresolved
future blocker naming a boundary it crosses. The item stays live and visible, the task
lifecycle still refuses `1_in-progress` under a live `blocking-*`, and the next boundary
reports it. Nothing disappears; it is only not reported by the range that wrote it.

Not fixed here, and deliberately: a `task:<id>` boundary still activates for a non-task
branch that merely edits `<id>`'s record. That is over-broad, but it is repairable — resolve
or reclassify the action — where the filing case had no exit at all. Narrowing it means
deciding what "task X's merge" is, which is a decision, not a gate patch.

## Core fit

**Agent substitution:** pass — both gates are stdlib Python reading Git and Markdown; no
agent runtime, model, or vendor tool appears in the rule, the inputs, or the output.
**Provider substitution:** pass — the scope comes from the trusted base/candidate range and
commit tags, which every forge exposes; the GitHub workflow is an unchanged thin caller.
**Repository substitution:** pass — any adopting repository whose tasks link queue items
hits the same contradiction the first time one task's item names another task, and the same
deadlock the first time it files a `transition:*` action through a pull request.
**User-global writes:** none
**Why AgentFold core:** the contradiction is between two tracked core checks and their
contract in `automation/AGENTS.md`. It cannot be repaired in local config, in a service, or
in a provider adapter, because both halves are repository invariants.
**Thin adapter:** none
