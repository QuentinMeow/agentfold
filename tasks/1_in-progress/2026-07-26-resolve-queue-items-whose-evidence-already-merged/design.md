# Design notes — Let a queue item resolve when its resolution evidence landed earlier

**Status:** decided

## Problem

Ordinary agent requests required every declared resolution-evidence file to change in the
same edge that deleted the request. That rejected an honest workflow in which the requested
repair landed after the action was filed but before its status-only claim. The repair must
admit that history without letting an old action, another merge parent, a deleted incarnation,
or a later reversion supply favorable bytes.

This widening applies only to ordinary `message-queue/needs-agent/requests/`. Task pickups retain their
atomic task-move receipt. Generated and manual retries, human endpoints, reviews, and custom
typed leaves retain their existing control paths and deletion-edge evidence rules.

## Options considered

### Option A — Keep deletion-edge evidence only

This is simple and strongly bound to one edge, but permanently traps an action after its
repair has already merged. Rewriting the evidence merely to make deletion possible would be
ceremony without new evidence.

### Option B — Baseline evidence at the claim commit

This admits work after a claim, but still rejects the live case where evidence landed before
the claim. It also makes claim timing, rather than action creation, define what work can count.

### Option C — Unique-incarnation creation baseline with surviving final bytes

Follow the current immutable action identity backward over the complete Git DAG. Exact-path
predecessors and unambiguous same-identity paths that disappear on an edge are both followed
for every merge parent. Convergent histories deduplicate to one creation snapshot; zero or
multiple roots, incomplete/shallow ancestry, ambiguous paths, and Git read failures fail
closed. Deletion/recreation begins a new incarnation and cannot borrow the old claim or
baseline.

At the unique creation commit, each declared repository-local evidence path is baselined.
Absence is a valid baseline; a non-regular baseline is not. Every path must be a readable
regular file whose bytes differ from that baseline at both the deletion event and the final
admitted range head or staged index. This rejects unchanged evidence, same-commit filing and
evidence, changes made before filing, deletion, non-regular replacement, and any reversion to
the baseline. The independent committed status-only `open` to `in-repair` claim remains
mandatory.

## Chosen

Option C is the narrowest rule that admits the measured live case while preserving a durable
lower bound: the final repository must contain bytes that were not already present when the
current action was filed. The field uses a closed list grammar of backticked paths or Markdown
links separated by commas or semicolons; one malformed, external, queue-local, absolute, or
parent-traversing entry rejects the entire ordinary-request resolution.

This is byte-level evidence, not semantic proof. A later unrelated different-byte edit can
look like the requested repair. Conversely, a distinct later action that legitimately restores
the first action's creation bytes within the same audited range will false-block the first
action. That fail-closed tradeoff prevents delete-then-revert laundering. A future durable,
action-specific completion receipt could distinguish those histories; this task does not add
a new queue schema or receipt type.

## Core fit

**Agent substitution:** pass — the rule consumes repository files and Git history, not an agent-runtime identity or private state
**Provider substitution:** pass — staged and committed candidates use provider-neutral Git objects and paths
**Repository substitution:** pass — any adopted repository can accumulate an ordinary action whose implementation lands before its later claim
**User-global writes:** none
**Why AgentFold core:** queue resolution and its fail-closed Git evidence are canonical harness admission behavior, not product code, local configuration, or a private overlay
**Thin adapter:** none
