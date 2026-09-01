# Design notes — Stop a restack from being blamed for another branch's deletion

**Status:** decided

## Problem

The rewritten-history check compares the displaced tip `O` directly with the new head
`N`. When a newly selected base `M` legitimately resolved a queue action, that synthetic
`O→N` comparison looks exactly like the task branch deleted the action. The current
continuity path therefore always reports `divergent update discarded a live old-tip
action`, even when the branch never touched the queue.

The protection is real: a force-push must not silently discard a live action from `O`.
The repair may suppress the continuity finding only when immutable Git history proves that
one candidate-side event validly resolved the same inherited occurrence and that the
resulting absence survived to `N`.

The asymmetry was deliberate in its original preservation-only model: the continuity edge
was intentionally a constant finding. There is no durable evidence that the later
other-parent provenance helper was deliberately excluded after legitimate restacks became
a reproduced workflow. It is therefore neither an obvious coding oversight nor a settled
security rule; the executable POCs below establish the narrower replacement contract.

## Options considered

### Rejected alternative — other-parent tree equivalence

Reuse `candidate_paths_match_other_parent` when `N` omits the path. This locates which side
supplied absence, but it is evidence-blind: a valid base resolution and an unclaimed base
deletion have the same tree shape. It would launder P2/S2.

### Rejected alternative — synthetic displaced-tip validation

Call `queue_deletion_problem(path, text, O, N)`. This rejects valid intermediate claims and
can combine a claim reachable only from `O` with unrelated evidence at `N`. The synthetic
edge did not author the deletion and cannot own its authority.

### Rejected alternative — replay, range-diff, or patch identity

Use task-patch replay to infer which lineage authored the missing path. This is useful
diagnosis, not authority: conflict-adjusted replays lose stable patch identity, independent
commits collide, and no-merge histories omit merge-authored queue actions.

### Selected design — C-rooted causal deletion provenance

Treat the unique old/new merge base `C` as the admitted occurrence root, enumerate real
candidate parent edges once, validate the real authority edge with existing queue rules,
and prove that one canonical causal root explains final absence. This is the chosen option.

## Chosen

Implement Option D with production identity and two disjoint event modes. The POC code is
durable design evidence, not code to copy: its subprocess-heavy fixture classifier measured
the correctness boundary, while production must reuse the reconciler's immutable object
readers and caches.

### Inputs and fail-closed boundary

The classifier accepts four full committed OIDs:

- `C`: exactly one `merge-base --all O N` result;
- `O`: displaced old ref tip;
- `M`: selected range base, readable, `C <= M <= N` by ancestry (equality allowed);
- `N`: new committed range head.

Missing/non-commit/unrelated objects, multiple merge bases, unreadable required commits,
trees or blobs, shallow/partial required history, an invalid `M`, or a measured graph budget
overflow return structured `unreadable` or `ambiguous`. They never authorize absence and
must tell the developer to fetch history/objects or simplify the rewrite, rather than accuse
the task of a proven deletion.

The classifier is committed-history-only. The existing staged/index queue checks keep their
current authority; unmerged index stages must continue to fail closed and may not be read as
absence.

### Production identity and occurrence

Use `queue_action_identity`, never the POCs' experimental `Action-ID`:

- ordinary identity is actor, typed leaf, and immutable action text;
- generated retry identity is actor, leaf, check, and subject;
- path is excluded so a permitted one-to-one timing/path move can preserve identity;
- different immutable payload is a different action and is checked independently.

Every snapshot is an `identity → [(path, bytes/state)]` multimap. Zero entries is absence,
one is unambiguous, and more than one fails closed. The existing set-valued identity cache is
not sufficient for this classifier.

Occurrence begins at unique `C`; production does not reopen parents of `C` or invent a new
genealogy schema. The old lineage must carry exactly one unchanged C-rooted occurrence over
every required `C→O` edge. After `C`, deletion/recreation, immutable mutation, transient
duplication, ambiguous rename, or a foreign matching parent breaks continuity.

Human response/binding conflicts need an additional exact-state comparison because action
identity deliberately excludes mutable response fields. A supplier cannot erase a divergent
committed human answer even when its own lifecycle is valid.

### Event mode 1 — direct

A direct child authors the absence. Every direct parent carrying the C-rooted occurrence is
an authority edge and independently passes `queue_deletion_problem` on that real
parent→child edge, including before schema activation. Parents that never carried the
occurrence are neutral, not authority and not suppliers.

Several carrying parent edges may form one direct merge event only for the same child and
canonical root after every edge validates. One invalid carrying edge blocks the whole event;
another parent's claim or evidence cannot be borrowed.

### Event mode 2 — supplier

One earlier real deletion event is the authority root. Every absent merge parent traces by
continuous absence to that same canonical root. Every carrying parent continuously carries
the C-rooted occurrence, and its carrying→merge edge is propagation only: it adopts supplied
absence and may neither pass nor borrow deletion authority. Neutral parents remain explicit.

Nested supplier wrappers inherit the canonical authority root. Multiple wrappers around the
same root merge their complete evidence envelopes; wrapper child OIDs do not create false
competition. Different valid roots, any invalid or ambiguous participating root, or mixed
valid/invalid roots block.

Authority and propagation edge sets are disjoint. A direct event may be the authority root
under later supplier wrappers, but no event may change modes to exploit a carrier's claim.

### Final-absence frontier

Before any sole-valid return, compute every causal root participating at the final absence
frontier. Authorization requires exactly one canonical valid root and no distinct valid,
invalid, or ambiguous competitor. Multiple wrappers of that one root are equivalent; a
separate invalid deletion remains a competitor even when another deletion is valid.

From the selected event through `N`, every descendant result and contributing merge parent
must remain absent. Reintroduction followed by either invalid or valid redeletion stays
ambiguous and retains the complete earlier and later authority/propagation evidence. The
classifier never chooses only the latest event.

### Structured result and human effect

Return `valid`, `invalid`, `none`, `ambiguous`, or `unreadable` with C/O/M/N, identity and
multiplicity, mode, canonical roots, event children, every authority verdict, propagation
edge, neutral/absent parent, full OID, and reason lineage.

| Development cycle | Behavior after this change |
|---|---|
| Ordinary rebase/restack | Silent only for one valid inherited resolution event |
| Invalid base deletion | Blocking; names the real invalid parent→child edge and validator problem |
| Genuine branch action loss | Blocking; says no candidate resolution of the C-rooted occurrence exists |
| Merge-shaped base (S12) | Valid supplier deletion owns authority; carrying→merge is propagation only |
| Complete K-then-D cherry-pick | May validate because the real lifecycle edges survive |
| Deletion-only cherry-pick or squash | Blocking; patch similarity is not queue authority |
| Shallow/partial/missing history | Blocking attribution-unavailable message with fetch guidance |
| Duplicate, competing, or reintroduced occurrence | Blocking ambiguity with participating OIDs |
| Fast-forward or carried live action | Existing clean behavior remains clean |

Remote classification is a post-push advisory under current repository policy. Messages say
the continuity check failed; they do not claim the ref update was prevented. A valid
inherited resolution remains silent by default.

### Bounded implementation

For one divergent `O,N` pair:

1. return immediately on fast-forward;
2. validate C/O/M/N and any graph budget before action authority work;
3. run one `rev-list --parents --topo-order` enumeration for the required post-C graph and
   populate the parent cache;
4. cache queue snapshots by immutable `message-queue` subtree/object OID through the
   existing batch readers;
5. classify all disappeared identities from the shared graph/snapshots, never one recursive
   Git history walk per action;
6. memoize real-edge authority by immutable edge and identity inputs;
7. on budget overflow, return structured ambiguity with zero selected events and no
   heuristic fallback.

The POC's 133-commit/16-action case used one graph enumeration, zero per-action history
walks, and three distinct queue-subtree reads, but still spawned production validator
subprocesses. Production tests must measure and cap those calls; the POC numbers are not a
launch benchmark or ceiling.

## Verification design

Production work is not complete until all of these are captured from the integrated tip:

- S1–S12 plus the 69 production-contract DAG cases that map to production behavior;
- direct two/three-parent positives and invalid-parent negatives;
- supplier, nested wrapper, diamond, mixed-root, human conflict, retry, pickup, timing move,
  cherry-pick/squash-erasure, reintroduction, and final-frontier cases;
- missing/non-commit/unrelated C/O/M/N, multiple bases, shallow history, missing commit/tree/
  blob, ignored replace refs, graph-budget overflow, and missing-object cache recovery;
- existing staged unmerged-index behavior and committed continuity isolation;
- an observed-red production mutation that removes final-frontier competitor handling;
- a 128+ commit/many-action process/cache assertion with one graph enumeration and no
  per-action history walk;
- targeted tests, `python3 automation/run_tests.py`, reconciler, core-fit review, cold clone,
  and the async one-way-door adversarial panel.

The four POC self-tests remain executable design evidence: replay 7/7 (diagnostic only),
edge-witness 29/29, merge-incarnation 37/37, and production-contract 69/69 with 4/4 aliases
and 6/6 observed-red controls. A fresh frontier verifier additionally passed 98/98 exact
comparisons across 49 twice-reconstructed DAGs. None of those results is a claim that the
production call site or full suite already works.

## Non-goals

- no new queue identity field, schema migration, dependency, service, or provider state;
- no ancestry/genealogy rule before `C`;
- no replay, range-diff, patch-id, path similarity, or synthetic-edge authority;
- no squash-stable receipt or squash support;
- no claim that the advisory check prevented a remote push;
- no authorization for criss-cross/multiple-base, partial-history, or over-budget graphs;
- no self-evolving agent authority over evaluators, evidence, credentials, or admission.

## Core fit

**Agent substitution:** pass — the rule consumes only committed repository objects and existing queue authority, so another agent runtime preserves the behavior
**Provider substitution:** not-applicable — no hosted-provider state participates in identity, authority, or attribution
**Repository substitution:** pass — any adopted repository using AgentFold's queue and rewritten-history gate needs the same false-accusation protection
**User-global writes:** none
**Why AgentFold core:** rewritten-history queue preservation and lifecycle authority are reconciler invariants, not local configuration, a product service, private overlay, or separate plugin
**Thin adapter:** none
