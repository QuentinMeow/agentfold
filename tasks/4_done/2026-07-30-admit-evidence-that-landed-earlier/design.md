# Design notes — admit resolution evidence that landed earlier

**Status:** decided

## Problem

The rule itself was decided before this task, in the exploration recorded at
docs/designs/queue-resolution-order-independence.md and in the stack plan that task carries.
This file records only the choices the specification left open, and the reason the
implementation resolved each one the way it did.

`resolution_evidence_problem` compares the declared evidence file between the deletion
commit and its immediate parent. The window is one commit wide, so work that merged earlier
reads as unchanged and its item can never be deleted honestly. The naive widening — "the
evidence changed at some point" — was measured to make 14 of 14 live ordinary requests
deletable with no work at all.

## Options considered

### Option A — widen the window to the whole lineage
One condition, no new inputs. Measured at 14 of 14 admitted, including five gates whose
stated precondition is a task still unclaimed in `tasks/0_backlog/`. Rejected upstream.

### Option B — bind the earlier commit to the item's own task link
Keep the deletion-edge comparison exactly as it is and add a second, narrower way to pass:
the evidence moved in a commit the repository already attributes, by `task:<id>` in its own
message, to a task that linked this exact canonical queue path and was already past pickup
at that commit — and never to the task the item's own timing boundary gates.

## Chosen

Option B, as specified. Four implementation choices were left open.

**The finding message is unchanged, byte for byte.** The new rule only removes findings, and
the guarantee this change rests on is that its finding set is a subset of the old one on
every input. A reworded message would break that subset literally — every refused item would
report a finding the old checker never emitted — and `retry_identity_matches` compares
filed retry text. The message stays "resolution evidence was not created or changed in the
deletion commit", which is still exactly true of every path it now names.

**`non-blocking-*` admits nothing.** The fail-closed clause zeroes the admitted set when the
timing field the filename prefix requires carries a concrete value that parses to no
boundary tokens. `blocking-*` requires `Blocks now` and `future-blocking-*` requires
`Blocks at`; both parse to boundary tokens. `non-blocking-*` requires `If unanswered`, which
is prose about an unattended outcome and parses to no boundary at all, and a filename with
no delivery class requires nothing. Both return the empty set outright rather than through
the concrete-value test, so a malformed non-blocking item cannot be admitted where a
well-formed one is refused. This is the conservative reading: it can only refuse more.

**`git log` decides what "changed this path" means.** The specification names git's own
sense, including its merge simplification — a merge counts only when it is TREESAME to no
parent — and that is precisely the default behaviour of `git log <tips> -- <path>`. Writing
a second definition in Python would be a second place for the two to disagree. The `task:`
token pattern is likewise hoisted out of `task_ids_from_change_range` into one constant both
readers share, rather than copied.

**The rule reads no history the base branch forbids it to read.** Reachability comes from
`git log`, which honours grafts and a shallow clone's boundary; commit parents are never
parsed out of raw commit objects, and `parse_raw_git_commit_tree` is untouched.
`UNREAD_TREE_ENTRY` keeps meaning "run the Git query yourself".

Failure is never fatal and never visible. `earlier_resolution_task_ids` answers the empty
set for an unreadable revision, a `GitSnapshotError` from `task_ids_linking_queue_at`, or a
timing value Git cannot parse; `evidence_landed_for_task` answers `False` for a non-zero
`git log`, an empty tip list, or a frame it cannot decode, and its caller catches whatever
is left. Every one of those paths lands back on the deletion-edge verdict the checker
already produced.

### Cost

The change costs Git work only on a deletion, where `resolution_evidence_problem` is
reached, and only for a path the deletion edge did not already change. On a clean tree it
costs nothing. `task_ids_linking_queue_at` now reads each `task.md` straight from the
recursive listing's own object through the `cat-file --batch` reader the base branch added,
instead of asking Git for the same entry a second time per task; that also speeds up the
existing review-cleanup path. Measured spawn counts are in `verification.md`.

## Core fit

**Agent substitution:** pass — the change is inside a stdlib Python checker with no agent
runtime, prompt, or model surface; any agent that could run the reconciler before runs the
same reconciler and reads the same findings.
**Provider substitution:** pass — no provider name, API, or payload is read; the rule asks
Git about the repository the reconciler was already asking about.
**Repository substitution:** pass — any adopted repository that files queue items hits the
same deadlock the moment work merges before its item can be deleted, and the deadlock is
unrepairable there for the same reason it is here: the commit that would fix it is the one
commit that cannot land.
**User-global writes:** none
**Why AgentFold core:** `queue-resolution` is the referee that decides when a canonical
action may disappear, and this changes what that referee accepts as evidence — not any
local setup, product service, or private overlay.
**Thin adapter:** none

## What this does not do

It does not make the gate prove that work happened. It cannot: the checker lives in the same
writable tree as the agents, the hook is one flag from being skipped, and there is one
identity for everyone. What it adds is that a claim must now be consistent with committed
history the agent would have had to forge earlier and elsewhere.

It does not move strictness to filing time, and it does not touch
`resolution_evidence_paths`, including its refusal of a queue-pointing evidence path. A
generic evidence path declared at filing time remains the weak point the design named, and
remains open work.

It does not repair the three stranded `transition:merge` reviews, which fail for a different
reason: Git evidence cannot un-cross a boundary.
