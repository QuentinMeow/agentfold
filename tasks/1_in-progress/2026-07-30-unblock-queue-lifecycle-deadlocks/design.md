# Design notes — give claimed agent queue items and generated retries a legal way out

**Status:** decided

## Problem

Two reproduced defects in `automation/reconcile/reconcile.py` leave the repository with
no legal move, and each one feeds the other.

`claim_identity` froze `Resolution evidence` across a committed `open` -> `in-repair`
claim, so an agent who claimed first and worked the evidence out second had no exit at
all. `immutable_action_text` additionally treated the field as immutable for every agent
item, so the field could not even be established while the item was live.

Separately, `stale-task` is emitted by the reconciler but was never a key in `CHECKS`.
Three different mechanisms look an id up there — retry clearance
(`generated_retry_clear`), deletion certification (`queue_deletion_problem`), and retry
garbage collection — so its generated retry could never be cleared, never be collected,
and, because retries are filed `blocking-*` with `**Blocks now:** transition:merge` and
no `task:` token, it then blocked every pull request forever.

The choices this task had to make: how far to loosen the evidence field without making a
claim receipt transferable, how to register a second check id on one function without
double-reporting its findings, and whether garbage collection should widen to any check
name or stay tied to what deletion can certify.

## Options considered

### Option A — Drop `Resolution evidence` from `claim_identity` only
The minimal repair. It unblocks every reconciler-generated retry, whose identity is the
generated `(check, subject)` tuple rather than its action text. *Example consequence:* an
ordinary agent request filed without the field stays undeletable from birth, because
`immutable_action_text` still rejects adding it while the item is live.

### Option B — Re-establish a claim after an evidence-only edit
Teach `claimed_lifecycle_problem` to accept a claim whose only later change was the
evidence field. *Example consequence:* the same deadlock is reachable one step earlier —
an evidence edit made before the claim rather than after it still trips the live-mutation
check — so the special case buys a narrower fix for the same cost.

### Option C — Make the agent's own predeclaration agent-mutable (chosen)
Treat `Resolution evidence` as owned by whoever must act on the item: mutable for
`needs-agent`, frozen for `needs-human` exactly as before. *Example consequence:* an
agent may correct a predeclaration it owns, and no human-side rule changes at all.

### Option D — Garbage-collect any reconciler-owned retry whose finding is absent
Widen collection to every check name, registered or not. *Example consequence:* a
`queue-resolution` retry would be deleted even though its own checker reads the deletion
being judged, so it can never certify that deletion — collection would replace a stale
retry with an uncertified deletion, which is a worse finding than the one it cleared.

### Option E — Rename the `stale-task` finding to an id already in `CHECKS`
A one-word change at the emission site. *Example consequence:* it breaks the rule that
check ids stay stable because retry filenames embed them
(`memory/lessons/automation/deterministic-finding-keys.md`), and two backlog task records
already name `stale-task` as a check id.

## Chosen

**C, plus registering `stale-task` in `CHECKS`, plus keeping collection tied to what
deletion certifies.**

`Resolution evidence` moved out of `claim_identity`'s agent key set and into the mutable
set of `immutable_action_text` for `needs-agent` only. The invariant that had to survive —
a claim receipt cannot be carried onto a different action — is untouched, because what
*defines* an action (`Action`, `Full context`, `Request kind`, and for a generated retry
its `Check`/`Subject` tuple) all stay immutable, and the lineage rules that stop a new
item borrowing an old receipt are unchanged. What completion must prove is also unchanged:
`resolution_evidence_problem` still requires the declared non-queue paths to change in the
deletion commit, and `queue-schema` still requires a concrete non-queue path on every
ordinary agent item. The freedom gained is exactly the missing one — the actor may
establish or correct its own predeclaration while the item is live.

`CHECKS` becomes a map from check id to the function that emits findings carrying that id,
which allows one function to answer to several ids; the runner deduplicates by function
identity so nothing is reported twice. `ReconcileRegistryTests`-style coverage now holds
every id the source emits to that map, so this class of defect cannot be reintroduced
silently — which is the durable fix, rather than widening collection to paper over it.

Garbage collection keeps the `queue-resolution` exclusion for the reason above, but the
predicate is now the named `generated_retry_collectable` with the reasoning attached, so
the next reader does not have to rediscover why one id is excluded and another is not.

Because a `queue-resolution` retry legitimately survives collection, `retry_text` now
predeclares a `**Resolution evidence:**` line so its manual exit is discoverable in the
item itself; `refresh_retry_text` only ever adds that line and never rewrites a concrete
value an agent put there. Finally, `--file-retries` recovers a deleted retry's committed
text before refiling a still-live finding, so an agent's rejection reason and claimed
status survive the one path that used to discard them.

## Core fit

**Agent substitution:** pass — the change is entirely inside the repository's own Python
reconciler and its file formats. No agent runtime is named, and any runtime that runs
`python3 automation/reconcile/reconcile.py` observes identical behavior.
**Provider substitution:** not-applicable — no provider API, credential, or hosted service
is involved; the check reads only repository files and local Git history.
**Repository substitution:** pass — every adopted repository inherits the same deadlock.
Any adopter whose agent claims a queue item before working out its evidence, or whose
reconciler files a retry for an unregistered check id, is blocked from merging with no
legal move. The repair is a property of the harness contract, not of this repository's
content.
**User-global writes:** none
**Why AgentFold core:** the queue lifecycle and the reconciler check registry are core
harness mechanisms defined by `message-queue/AGENTS.md` and `automation/AGENTS.md`. This
is not local configuration, product code, a private overlay, or a plugin: it restores the
root guardrail that nothing blocks silently and that every finding has a legal fix.
**Thin adapter:** none
