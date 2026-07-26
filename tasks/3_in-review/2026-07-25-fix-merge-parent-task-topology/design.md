# Design notes — stop reading a merge parent edge as a lifecycle step

**Status:** decided

## Problem

`task_topology_problems` in `automation/reconcile/reconcile.py` is a per-edge function:
it receives one parent and one candidate, reads the task records in each tree, and
compares them as a single linear lifecycle step. `queue_revision_edges` feeds it every
parent/candidate pair, so a merge commit with two parents produces two edges, and the
function evaluates each as though it were the task's only predecessor.

For a merge whose incoming branch was cut before a task existed, one of those edges has
the task absent on the parent side and present in a non-backlog status on the merge side.
The `if not prior:` branch reads that as a creation and emits
`new task:<id> was created directly in <status>`, even though the task was filed in
`0_backlog` and claimed correctly on the other parent's lineage.

The constraint is that `queue_revision_edges` must keep yielding every parent edge —
`queue-resolution`, `queue-boundary`, `task-action-origin`, and the handover checks all
depend on per-edge evaluation, and suppressing edges there would drop real coverage
across every one of them. So the repair has to live in how topology interprets an edge,
not in which edges exist.

Three behaviours must survive: a genuine direct-to-non-backlog creation on a
single-parent edge; a merge where no parent carries the task and the merge introduces it
in a non-backlog status; and every sibling rule in the same function — the task-id rename
detection, the duplicate-incarnation guard, the deletion rule, the status-transition
table, and the `adopting` escape.

## Options considered

### Option A — suppress the creation finding when a sibling parent already has the task

The `if not prior:` branch consults the candidate's other parents before it yields. If
any other parent's tree carries a record for the same task id, this edge is not that
task's creation and the finding is skipped. Nothing else in the function changes, and
`prior` keeps its exact per-edge meaning everywhere else.

The file already has the idiom. `candidate_parent_oids` returns every committed parent of
a candidate — `staged_parent_oids()` for the index candidate, `revision_parents` for a
commit — and two existing checks use it for the same purpose:
`task_action_origin_problems` takes its baseline as the maximum count across
`candidate_parent_oids(revision)`, and `candidate_paths_match_other_parent` asks whether
another parent supplied an exact path state.

*Example consequence:* on a single-parent edge `candidate_parent_oids` returns exactly the
edge's own parent, the loop skips it and finds nothing, so linear behaviour is provably
byte-identical. On the root edge it returns nothing, likewise unchanged.

### Option B — make the merge edge's `before` side the union of all parents

`task_topology_problems` computes `before = task_record_paths_at(parent)`. Option B would
replace that, for a merge candidate, with the union of `task_record_paths_at(p)` over
every parent, so both of a merge's edges see the same combined predecessor state.

*Example consequence:* the false positive also disappears, because the parent that filed
the task contributes its `0_backlog` or `1_in-progress` record to the union.

## Chosen

Option A.

`before` is not a free variable. `task_record_paths_at` returns a mapping from task id to
a list of `(status, path)` incarnations, and the very next lines use the length of that
list as the signal for a duplicated task record:
`if len(prior) > 1 or len(current) > 1: continue`, which hands the case to
`task-structure`. Unioning across parents synthesises that duplication out of two
perfectly valid parents. Concretely: a task sitting in `0_backlog` at one parent and
`1_in-progress` at another — two branches, one of which claimed it — produces a
two-element `prior` under Option B, so the whole task is skipped and an illegal merge
result such as `4_done` goes unreported. Under Option A the same merge still yields the
`0_backlog` parent's edge and the `1_in-progress` parent's edge separately, and the
illegal jump is caught on the first of them. Option B also makes `prior[0]` ambiguous
wherever the parents disagree, so `prior_status` and the reported `prior_path` would
depend on parent ordering.

Against the three behaviours that must survive:

- A genuine direct-to-non-backlog creation on a single-parent edge. Option A leaves it
  untouched, because a single-parent candidate has no sibling to consult. Option B also
  leaves it untouched, because there is no union to take.
- A merge where no parent carries the task. Option A finds no sibling record and yields
  the finding on both edges, which the caller's `reported` set collapses to one. Option B
  yields it too, since the union is empty.
- The sibling rules. Option A does not read or write `prior`, `current`, `before`,
  `after`, or the rename set, so all of them are literally unchanged. Option B rewrites
  the input every one of them reads, and the duplicate-incarnation guard turns into a
  silent skip whenever two parents disagree about a task's status.

Option A costs nothing in coverage. Suppression is safe precisely because it is
conditioned on another parent having the record, and every parent that has the record
supplies its own governed edge: `queue_revision_edges` gates on the candidate commit and
then yields all of its parents, so the edge that does carry the task is always present in
the same view. Whatever the merge did to that task — kept its status, advanced it, jumped
it, or dropped it — is validated there by the transition table or the deletion rule.

One pre-existing limit is worth naming rather than widening: if a task's real creation
commit lies outside the admitted range and was never itself checked, neither shape
recovers it. That gap belongs to range selection, not to this function.

## Core fit

**Agent substitution:** pass — the parent list comes from `git rev-list --parents` and the
task records from `git ls-tree`, so no agent runtime contributes to the decision and a
Claude, Codex, or plain-shell session evaluating the same merge gets the same suppression.
**Provider substitution:** pass — merge topology is read from the local object database
rather than a provider API, so a two-parent merge produced by GitHub, GitLab, Gitea, or a
bare `git merge` is interpreted identically; the workflow only supplies the range.
**Repository substitution:** pass — any adopted repository that runs two tasks in
parallel merges a branch cut before the newer task was filed, and today that first merge
turns its correct history into a red required check.
**User-global writes:** none
**Why AgentFold core:** the lifecycle topology rule is stated in `tasks/AGENTS.md` and
enforced only by this reconciler check, which every adopter runs from the pre-commit hook
and from CI; a false positive here blocks correct merges in every clone, so the repair
cannot be local configuration, a product service, a private overlay, or an external
plugin.
**Thin adapter:** none
