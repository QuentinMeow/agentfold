# Design notes — stop reading a merge parent edge as a lifecycle transition

**Status:** decided

## Problem

`task_topology_problems` in `automation/reconcile/reconcile.py` is a per-edge function:
it receives one parent and one candidate, reads the task records in each tree, and
compares them as a single linear lifecycle step. `queue_revision_edges` feeds it every
parent/candidate pair, so a merge commit with two parents produces two edges, and the
function evaluates each as though it were the task's only predecessor.

Task 2026-07-25-fix-merge-parent-task-topology repaired the *creation* half of that: an
edge whose parent predates a task is no creation for it. The *transition* half is the
same mistake one branch further down the function. When a merge's incoming lineage
advanced a task across two or more governed edges, the trunk-side parent still sits at the
old status while the merge tree holds the new one, so the transition table sees a single
illegal jump.

This fires on `main` itself. `main` looks green alone only because with no `MERGE_HEAD`
the reconciler never re-walks history; the moment any branch merges the trunk, PR #41's
merge `84e3524ef36c8aed5734c48248131f6c2b397ce8` is re-audited through both parents. Its
trunk parent `7c2854a1fb3a885423f080f3957d76f132b32b27` records
task:2026-07-25-fix-handover-projection-code-span-copy at `1_in-progress`; its branch
parent `ed3a9ee2d9314cd5dde59348eca1b7e02ccdfe43` records it at `4_done`, reached through
`07de276` (`1_in-progress → 3_in-review`) and `6de7954` (`3_in-review → 4_done`). Both
steps are governed commits, so the history is well-formed and the finding is false. Every
branch that needs to catch up with the trunk is blocked until this is repaired.

The same constraint as the creation repair applies: `queue_revision_edges` must keep
yielding every parent edge, because `queue-resolution`, `queue-boundary`,
`task-action-origin`, and the handover checks all depend on per-edge evaluation. So the
repair lives in how the transition rule interprets an edge, not in which edges exist.

Three behaviours must survive: a genuine illegal jump on a single-parent edge; a merge
that advances a task to a status **no** parent held; and every sibling rule in the same
function — the rename detection, the duplicate-incarnation guard, the deletion rule, the
creation rule, and the `adopting` escape.

## Options considered

### Option A — suppress the jump when a sibling parent already held the resulting status

The transition branch consults the candidate's other parents before it yields. If any
other parent's tree records the same task id at exactly the status the candidate holds,
this edge is not that task's lifecycle step, and the finding is skipped. `prior`,
`current`, `before`, `after`, and the rename set keep their exact per-edge meaning
everywhere else.

This is the shape the creation repair already chose, and the file already has the idiom:
`candidate_parent_oids` returns every committed parent of a candidate
(`staged_parent_oids()` for the index candidate, `revision_parents` for a commit), and
`task_recorded_at_other_parent`, `task_action_origin_problems`, and
`candidate_paths_match_other_parent` all consult it for the same purpose.

*Example consequence:* on a single-parent edge `candidate_parent_oids` returns exactly the
edge's own parent, the loop skips it and finds nothing, so linear behaviour is provably
byte-identical. On the root edge it returns nothing, likewise unchanged.

### Option B — suppress whenever a sibling parent records the task at all

Reuse `task_recorded_at_other_parent` verbatim, the helper the creation branch already
calls, instead of writing a status-aware sibling.

*Example consequence:* the false positive also disappears, and there is one helper instead
of two.

### Option C — make the merge edge's `before` side the union of all parents

Replace `before = task_record_paths_at(parent)`, for a merge candidate, with the union
over every parent, so both of a merge's edges see the same combined predecessor state.

*Example consequence:* the false positive disappears, because the parent that already sat
at `4_done` contributes its record to the union.

## Chosen

Option A.

**Against Option B.** Recording a task is not the same claim as reaching a status. A
merge whose two parents hold a task at `0_backlog` and `1_in-progress`, and whose own tree
holds it at `4_done`, has a sibling record on both edges, so Option B suppresses both and
the illegal advance goes unreported — with no other edge left to catch it, because no
parent ever reached `4_done`. This is not hypothetical reasoning: with the guard
temporarily rewritten to Option B's shape,
`test_task_admission_still_rejects_a_merge_advance_past_a_sibling` fails with an empty
finding list, and `verification.md` records that run. Option A's exact-status match is
what keeps the suppression conditioned on something that actually justifies the result.

**Against Option C.** `before` is not a free variable. `task_record_paths_at` returns a
mapping from task id to a list of `(status, path)` incarnations, and the very next lines
use the length of that list as the duplicate-record signal:
`if len(prior) > 1 or len(current) > 1: continue`, which hands the case to
`task-structure`. Unioning across parents synthesises that duplication out of two
perfectly valid parents — exactly the two-parent shape above — so the whole task is
skipped and the illegal `4_done` goes unreported again. Option C also makes `prior[0]`
ambiguous wherever parents disagree, so `prior_status` and the reported `prior_path` would
depend on parent ordering. The creation repair rejected this same shape for the same
reason.

Against the three behaviours that must survive:

- A genuine illegal jump on a single-parent edge. Option A leaves it untouched, because a
  single-parent candidate has no sibling to consult. Options B and C likewise.
- A merge that advances a task to a status no parent held. Option A finds no sibling at
  that status and yields the finding on every edge, which the caller's `reported` set
  collapses. Option B suppresses it whenever any parent records the task at all; Option C
  suppresses it whenever the parents disagree.
- The sibling rules. Option A does not read or write `prior`, `current`, `before`,
  `after`, or the rename set, so all of them are literally unchanged. Option C rewrites the
  input every one of them reads.

Suppression is safe precisely because it is conditioned on another parent already holding
the resulting status, and that parent reached it through its own governed edges:
`queue_revision_edges` gates on the candidate commit and then yields all of its parents,
so the edge that does carry the status is always present in the same view, where the
transition table validates each step it took.

The new helper mirrors the caller's own duplicate guard — it accepts a sibling only when
that parent records exactly one incarnation of the task — so a parent that itself records
the task in two statuses at once never justifies anything, and `task-structure` keeps
owning that case.

One pre-existing limit is worth naming rather than widening: if a task's real transition
commit lies outside the admitted range and was never itself checked, neither shape recovers
it. That gap belongs to range selection, not to this function.

## Core fit

**Agent substitution:** pass — the parent list comes from `git rev-list --parents` and the
task records from `git ls-tree`, so no agent runtime contributes to the decision and a
Claude, Codex, or plain-shell session evaluating the same merge gets the same suppression.
**Provider substitution:** pass — merge topology is read from the local object database
rather than a provider API, so a two-parent merge produced by GitHub, GitLab, Gitea, or a
bare `git merge` is interpreted identically; the workflow only supplies the range.
**Repository substitution:** pass — any adopted repository whose branch carries a task
through two lifecycle steps before merging hits this the first time another branch merges
the trunk, and today that turns correct, already-governed history into a red required
check on every branch at once.
**User-global writes:** none
**Why AgentFold core:** the lifecycle topology rule is stated in `tasks/AGENTS.md` and
enforced only by this reconciler check, which every adopter runs from the pre-commit hook
and from CI; a false positive here blocks correct merges in every clone, so the repair
cannot be local configuration, a product service, a private overlay, or an external plugin.
**Thin adapter:** none
