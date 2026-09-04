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

### Inputs, adapter, and fail-closed boundary

Keep `--range` byte-for-byte compatible for every existing consumer. The rewritten-history
classifier adds `--displaced-tip O` plus an explicit, full lowercase-hex
`--candidate-base M`; `M` is valid only with `O` and a non-root full range. Fast-forward
updates return before resolving `M`. A divergent update that has no disappeared old
identity also needs no `M`.

The classifier accepts four full committed OIDs:

- `C`: exactly one `merge-base --all O N` result;
- `O`: displaced old ref tip;
- `M`: selected range base, readable, `C <= M <= N` by ancestry (equality allowed);
- `N`: new committed range head.

Missing/non-commit/unrelated objects, multiple merge bases, unreadable required commits,
trees or blobs, shallow/partial required history, an invalid `M`, or a measured graph budget
overflow return one structured incomplete result, exit 2, zero Findings, and zero retry/fix
mutation. This transactional preflight happens before any check result is yielded or any
writer is invoked. It tells the developer to fetch exact history/objects or simplify the
rewrite; it never accuses the task of a proven deletion.

The core is committed-history-only, provider-neutral, offline, and runs object reads with
lazy fetch and replace refs disabled. The GitHub workflow remains a thin adapter:

- pull-request synchronize events use the event's immutable base SHA as `M`;
- a push event may query the GitHub API only when exactly one open same-repository PR has
  the matching head ref, exact head SHA `N`, and matching base repository;
- the adapter explicitly fetches the exact `O` and base SHA when absent, re-queries the PR,
  and verifies that the immutable snapshot did not race;
- it derives `M` as the unique local `merge-base --all(base,N)` and never fetches or
  invents `M` itself;
- zero/multiple/closed/forked/raced/mismatched PRs, API failure, or a base retarget make
  attribution unavailable. `O`, `N`, `HEAD`, a default branch, or a moving ref are never
  fallbacks for `M`.

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
committed human answer even when its own lifecycle is valid. The `O` anchor includes every
concrete response and every concrete review target/revision even while unanswered, plus the
reviewed revision and terminal outcome. The candidate may fill an `O`-pending field, but all
concrete candidate parents must unify; a concrete candidate parent cannot be replaced by a
different concrete value.

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

Every valid real deletion root also issues a complete, versioned support certificate. The
certificate binds the action identity/path/blob, every real authority edge, the exact raw
non-action tree delta, unchanged declared dependencies, and typed production obligations.
The currently admitted obligation leaves are ordinary agent evidence, terminal human or
review binding, generated retry checker plus subject, and task-pickup state. Unsupported
review successor/reask/boundary shapes fail closed until production can certify them.

At each supplier adoption, every closest absent-source wrapper must agree on the root
certificate and current support projection, and the adoption child must copy every support
entry exactly. Typed obligations are re-evaluated at the source and child. The adoption
edge stays propagation-only and cannot author support drift. Source-lineage evolution in a
separate earlier commit is allowed; adoption-authored change, evidence rollback, conflicting
sources, or an incomplete obligation blocks. Nested wrappers carry every prior support
check, so a later exact restoration cannot heal an invalid intermediate adoption. Canonical
certificate and parent inputs are ordered independently of Git parent order.

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
edge, support certificate/check, neutral/absent parent, full OID, and reason lineage.

Structural incompleteness produces no Finding. After a complete traversal, each disappeared
production identity with no unique valid explanation produces exactly one stable Finding.
The subject is `message-queue/action-identities/<digest>`, where the digest is a
domain-separated canonical encoding of the authoritative full identity tuple; the tuple,
not the digest, remains authority. A digest collision between different tuples is
incomplete/exit 2. Diagnostics use a bounded lexicographic representative real path and
never dump action text. Ordinary `M...N` queue checks remain intact; only the synthetic
displaced-continuity duplicate is suppressed after valid attribution. Existing legacy
path-subject retries remain frozen and require no migration or rewrite.

| Development cycle | Behavior after this change |
|---|---|
| Ordinary rebase/restack | Silent only for one valid inherited resolution event |
| Invalid base deletion | Blocking; names the real invalid parent→child edge and validator problem |
| Genuine branch action loss | Blocking; says no candidate resolution of the C-rooted occurrence exists |
| Merge-shaped base (S12) | Valid supplier deletion owns authority; carrying→merge is propagation only |
| Complete K-then-D cherry-pick | May validate because the real lifecycle edges survive |
| Deletion-only cherry-pick or squash | Blocking; patch similarity is not queue authority |
| Shallow/partial/missing history | Blocking attribution-unavailable message with fetch guidance |
| Divergent disappearance without exact `M` | Exit 2; recover the exact base, no retry is filed |
| PR close, race, retarget, or no exact PR | Attribution unavailable; no guessed fallback |
| Duplicate, competing, or reintroduced occurrence | Blocking ambiguity with participating OIDs |
| Budget overflow | Exit 2 naming the counter/cap; zero Findings and zero mutation |
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

The first production ceilings are deterministic safety limits, not throughput targets:

- 4,096 graph commits and 8,192 parent edges;
- 2,048 production identities;
- 65,536 snapshot entries and 32 MiB of unique snapshot bytes;
- 512 authority validations and 262,144 identity-history edge checks;
- explicit additional ceilings for support paths, flattened-tree entries, obligation
  replays, certificate bytes, and Git child processes, measured before implementation is
  admitted.

Charge a counter before the protected work. Exactly-at-limit is allowed; limit-plus-one
aborts the transaction. Enumerate the graph once, share graph/object/snapshot caches across
all actions, reuse the parent map in production validators, and perform zero unmetered
per-action history walks. The 133-commit fixture's 135 Git processes are an acceptance
observation, not runtime authority: 129 are imported production parent queries that the
implementation must eliminate or explicitly budget.

The POC's 133-commit/16-action case used one graph enumeration, zero per-action history
walks, and three distinct queue-subtree reads, but still spawned production validator
subprocesses. Production tests must measure and cap those calls; the POC numbers are not a
launch benchmark or ceiling.

## Verification design

The final POC candidate is commit `8e7469c45aab7f7f8c5b3e9138102691ce508682`
(tree `5729051989d822be87c55bfb8d5ce06fbd1cd79c`). Its canonical evidence artifact is
`sha256:9e158d2908ca224d703179125a9bd08a0d64c2bfd5246143677720e1ff9d96cc`.
Three independent fresh-context verifiers unanimously accepted it: semantic/DAG,
evidence-forgery, and production-composition/performance. Two independent replays across
different roots, seeds, locales, and time zones produced byte-identical 154-row streams;
136/136 scenarios, 4/4 aliases, 16/16 damaged-mode controls, and all 28 evidence attacks
passed. The composition verifier proved that the five intentionally POC-blind cases are
caught 5/5 by the existing ordinary `M...N` production checks.

Production work is not complete until all of these are captured from the integrated tip:

- S1–S12 plus all 136 production-contract DAG cases that map to production behavior;
- direct two/three-parent positives and invalid-parent negatives;
- supplier, nested wrapper, diamond, mixed-root, human conflict, retry, pickup, timing move,
  cherry-pick/squash-erasure, reintroduction, and final-frontier cases;
- missing/non-commit/unrelated C/O/M/N, multiple bases, shallow history, missing commit/tree/
  blob, ignored replace refs, graph-budget overflow, and missing-object cache recovery;
- existing staged unmerged-index behavior and committed continuity isolation;
- exact/limit-plus-one tests for every graph, object, identity, authority, certificate,
  support-path, replay, byte, and process budget with transactional zero-result assertions;
- GitHub adapter tests for exact PR match, explicit fetch, re-query race, forks, multiple or
  missing PRs, base retarget, same-ref base fast-forward, and no-fallback behavior;
- stable one-Finding-per-identity projection, canonical tuple bytes, collision fail-closed,
  bounded diagnostics, and legacy path-subject retry coexistence;
- PCX21 staged-versus-committed parity and PCX22 unmerged-index ambiguity;
- an observed-red production mutation that removes final-frontier competitor handling;
- a 128+ commit/many-action process/cache assertion with one graph enumeration and no
  per-action history walk;
- targeted tests, `python3 automation/run_tests.py`, reconciler, core-fit review, cold clone,
  and the async one-way-door adversarial panel.

The four POC self-tests remain executable design evidence: replay 7/7 (diagnostic only),
edge-witness 29/29, merge-incarnation 37/37, and production-contract 136/136 with 4/4
aliases and 16/16 observed-red controls. None of those results is a claim that the
production call site, GitHub adapter, staged behavior, or full suite already works.

## Non-goals

- no new queue identity field, schema migration, dependency, service, or provider state;
- no ancestry/genealogy rule before `C`;
- no replay, range-diff, patch-id, path similarity, or synthetic-edge authority;
- no squash-stable receipt or squash support;
- no claim that the advisory check prevented a remote push;
- no authorization for criss-cross/multiple-base, partial-history, or over-budget graphs;
- no self-evolving agent authority over evaluators, evidence, credentials, or admission.
- no GitHub/provider state in core and no guessed candidate base;
- no automatic base-retarget attribution without a later independently proven causal rule;
- no production support for supplier review successor/reask/boundary leaves until their
  complete typed obligations and budgets have observed-red coverage.

## Core fit

**Agent substitution:** pass — the rule consumes only committed repository objects and existing queue authority, so another agent runtime preserves the behavior
**Provider substitution:** not-applicable — no hosted-provider state participates in identity, authority, or attribution
**Repository substitution:** pass — any adopted repository using AgentFold's queue and rewritten-history gate needs the same false-accusation protection
**User-global writes:** none
**Why AgentFold core:** rewritten-history queue preservation and lifecycle authority are reconciler invariants, not local configuration, a product service, private overlay, or separate plugin
**Thin adapter:** none

---

## 2026-09-01 amendment — O/N-only bounded provenance

**Amendment status:** supersedes every `M`, `--candidate-base`, current-PR/API, `M...N`
provenance, four-endpoint result, adapter, workflow, budget, verification, non-goal, and
core-fit statement above. The earlier text is preserved as rejected design history. The
direct/supplier authority, production identity, support-certificate, and full-root rules
remain only where this amendment does not replace them.

### Why the prior decision was reopened

One-way-door review found two concrete failures. A live PR base can advance or be retargeted,
and pre-PR pushes, closed/reopened or multiple PRs, forks, API lag, and reruns do not provide
one stable current PR. More importantly, a supplied `M` can hide an invalid deletion root
that still reaches `N`. Provider state cannot authorize a historical ref replacement.

The review also supplied a correct restack whose carrying merge had an outside-`C` parent
already free of the identity. The prior universal ancestor scan reopened that parent's old
history and falsely blocked. Later fresh attackers found the same boundary leak in event
enumeration, outside collisions and absent arms ignored for persisted identities, post-hoc
rather than pre-work budgets, buffered graph output, locale-dependent evidence, and open raw
grammar. Each defect was reproduced red before repair; evidence schemas v2, v3, and v4 are
preserved and permanently burned.

### Selected contract

The selected classifier accepts only immutable old/new ref endpoints `O,N`, returns early
for a fast-forward, derives exactly one `C = merge-base --all(O,N)`, enumerates the bounded
intrinsic `C..N` graph once, and validates real parent edges with existing queue authority.
It suppresses continuity only when one canonical valid causal resolution, with no valid,
invalid, ambiguous, duplicate, foreign, or reintroduced competitor, reaches `N`.

This proves “one valid `C`-rooted causal resolution reaches `N`.” It does not claim whether
the task branch or a newly selected base authored it.

### Orthogonal CLI inputs

1. `--range B...N` binds the ordinary candidate range and retains every existing queue
   mutation, deletion, schema, staged/index, and retry check.
2. `--ref-update O N` atomically binds one exact ref replacement and activates continuity
   provenance.

When both are present, the range head must equal `N`. `B` never enters provenance and `O`
never replaces the ordinary range base. Remove the old standalone `--displaced-tip`
continuity shape. Add no `--candidate-base`, compatibility alias, live-ref, reflog, HEAD,
default-branch, or provider fallback; backward compatibility is intentionally not required.

Both endpoints are non-zero full OIDs for the repository's object format and name readable
commits. A fast-forward `O <= N` returns clean before graph or action work. Only divergence
requires unique `C`. Zero endpoints mean ref creation/deletion, so adapters run ordinary
checks only and do not invent continuity inputs.

Missing/non-commit/unrelated endpoints, zero or multiple merge bases, shallow/partial
required history, malformed or unreadable commit/tree/blob data, disabled-object lookup
failure, or budget overflow returns one structured incomplete result, exit 2, and zero
Finding or mutation. Lazy fetch and replace refs remain disabled. Staged/index checks retain
their authority; an unmerged index may not be read as committed absence.

### Transaction boundary

Continuity classification is an immutable read-only preflight:

1. parse and cross-check the paired endpoints;
2. resolve exact `O,N` and derive `C` when required;
3. classify the complete bounded graph into one immutable result;
4. only then allow ordinary checks and writers to project output.

The preflight runs before `run_checks()` yields any Finding and before `--file-retries`,
`--fix-index`, `--fix-open-actions`, `--fix-queue-fold`, or another writer changes bytes.
Incomplete behavior emits bounded diagnostics only: no Finding summary, no retry
filing/clearing, and byte-identical worktree, index, memory index, open-actions, and queue
fold. `check_queue_resolution` consumes the finished result; it does not traverse history.

### Intrinsic graph and outside boundary

Enumerate `Desc(C) ∩ Anc(N)` once with parent records in topological/reverse order. Stream
and pre-charge stdout bytes, peak line bytes, commit tokens, and parent tokens; on overflow,
malformed/truncated output, or child failure, terminate and reap the process and publish no
partial graph.

An immediate non-`C`-rooted parent is a boundary snapshot only:

- zero exact occurrences is neutral;
- one matching occurrence is an outside collision;
- more than one is a duplicate collision;
- unreadable state is incomplete.

A neutral boundary parent's ancestors are outside the proof and remain unread. Only
intrinsic commits are event children. One parent map seeds every production parent consumer,
so production performs zero additional graph-parent subprocess queries. The POC's
133-commit fixture records 129 imported production queries specifically to expose this
integration gap.

### Shared edge-aware occurrence proof

Continue using `queue_action_identity` and an `identity → [(path, bytes/state)]` multimap.
Both disappeared and still-live `N` identities use the same proof from `C`: every intrinsic
carrying edge passes production mutation/frozen-state rules; a merge has exactly one valid
source plus compatible carriers. An outside carrier, duplicate, intrinsic absent arm followed
by a live child, deletion/recreation, immutable mutation, or conflicting human/review
binding breaks continuity. Parent order cannot change the verdict or evidence roles.

The earlier direct and supplier definitions remain. Direct authority belongs to every real
carrying parent→absent child edge and every such edge validates independently. Supplier
wrappers propagate one earlier canonical real deletion root and may not borrow authority.
Support certificates continue to bind real authority edges, exact support projection, and
typed obligations; adoption-authored drift, rollback, conflict, incomplete obligation, or a
later restoration after an invalid wrapper blocks.

### Full `N` frontier

The final frontier is fixed at `N`, never `M`. An all-absent merge unions every intrinsic
parent's complete causal-root set. Authorization requires exactly one canonical valid root
and no other valid, invalid, or ambiguous competitor. A valid root plus an unauthorized root
is blocking even when the valid deletion happened first.

Reintroduction followed by valid or invalid redeletion retains every earlier and later root
and blocks. A live `N` occurrence reached across an intrinsic absent arm is a
delete/recreate break. The classifier never chooses only the latest event.

### Result and ordinary-check composition

Return `valid`, `invalid`, `none`, `ambiguous`, or `unreadable` with `C/O/N`, endpoint roles,
identity/multiplicity, carry proofs, direct/supplier mode, causal roots, event children,
authority/propagation evidence, support certificates/checks, neutral/absent parents, typed
reason codes, resource counters, full OIDs, and bounded diagnostics. Exclude provider state,
`B`, `M`, PR number, moving refs, and localized stderr.

After complete traversal, emit one stable Finding per disappeared identity lacking a unique
valid explanation. Keep the domain-separated identity digest, collision fail-closed rule,
bounded representative path, no action-text dump, and frozen legacy retry coexistence from
the prior design.

Ordinary `B...N` checks remain enabled. The POC intentionally leaves two shapes clean—a
candidate duplicate/live survivor and a regression restored before later valid deletion—
because ordinary production checks report the real invalid mutation edges. Removing or
narrowing those checks reopens proven gaps.

### Exact production budget profile

Charge before the protected read, allocation, traversal, subprocess, or serialization.
Exactly-at-limit succeeds; limit-plus-one raises one budget exception before more work,
terminates/reaps a live child, discards local caches/results, and returns incomplete.

| Dimension | Limit |
|---|---:|
| Graph commits | 4,096 |
| Graph parent tokens/edges | 8,192 |
| Graph stdout bytes | 16 MiB |
| Peak graph line bytes | 1 MiB |
| Git child processes | 512 |
| Batch-reader restarts/fallbacks | 8 |
| Distinct object reads | 65,536 |
| Unique object payload bytes | 32 MiB |
| Peak object payload bytes | 4 MiB |
| Distinct queue subtree OIDs | 4,096 |
| Queue snapshot entries | 65,536 |
| Queue path bytes | 4 MiB |
| Queue blob bytes | 32 MiB |
| Flattened tree entries | 131,072 |
| Flattened path bytes | 8 MiB |
| Production identities | 2,048 |
| Occurrences per identity | 16 |
| Identity-edge/carry transitions | 262,144 |
| Causal roots | 65,536 total / 512 per identity |
| Authority validations | 512 |
| Support certificates | 512 |
| Dynamic support traversal paths | 65,536 |
| Discovered support paths | 8,192 |
| Support path bytes | 1 MiB |
| Certificate delta/projection rows | 65,536 |
| Certificate anchors/obligations | 8,192 each |
| Certificate serialized bytes | 32 MiB total / 4 MiB peak |
| Diagnostic bytes | 256 KiB |

The implementation may lower a limit after measurement but may not raise or omit one
without amending this design and its exact/limit-plus-one evidence. Object size is admitted
from the batch header before payload read; tree entry/name/path counters precede decode and
cache insertion; dynamic support traversal precedes matching/discovery; certificate
candidates, rows, anchors, obligations, and encoded size precede construction and hashing.
The preflight size calculation is itself bounded.

### GitHub adapter and common cycles

GitHub transports immutable endpoints and never authorizes provenance or queries the PR API.

The adapter behavior by development cycle is:

- A new branch push has zero `before`, so only ordinary checks run and no `O` is invented.
- A fast-forward push supplies `O=event.before` and `N=event.after`; core returns early.
- A force-push supplies the same exact pair before, during, or after a PR; PR state is
  irrelevant.
- A branch deletion has `deleted=true` and zero `after`, so continuity is absent and
  `github.sha` is not interpreted as `N`.
- Non-branch ref updates remain outside continuity until a tag policy exists.
- PR open, edit, and reopen events have no old/new head pair, so only ordinary `B...N`
  checks run.
- PR synchronize supplies top-level `before/after`; consistency requires
  `after == pull_request.head.sha`.
- Base advance or retarget affects ordinary checks only and never supplies O/N/C.
- Multiple PRs may repeat the identical O/N audit while retaining separate ordinary ranges.
- A stale rerun retains the original event pair rather than reading a current ref.
- Missing exact objects are fetched by their event OID; failure is coverage-unavailable
  exit 2.
- Fork synchronize remains unprivileged and uses exact head-repository objects when
  available; otherwise it is coverage-unavailable.
- A force-push performed while a fork PR is closed and later reopened has no trustworthy
  displaced pair at the base repository and remains an explicit coverage gap.
- Provider API outage or race does not affect provenance because no API call participates.

For push, `N` is `github.event.after`; `github.sha` is only a non-deletion consistency
observation because branch deletion assigns it the default-branch tip. PR synchronize
fails incomplete on missing top-level endpoints, `after != head.sha`, checkout `HEAD != N`,
or exact fetch failure. Never use `pull_request_target` to execute fork code or gain
credentials. Canary real same-repository and fork payloads before release.

Remote checks remain post-push advisory. They say classification failed, not that the ref
update was prevented.

### Human workflow

For a normal restack: fetch the current base, rewrite the task branch, inspect commits, push
with an exact lease, and let the push event classify its immutable O/N. A valid inherited
resolution is silent. A completed invalid/ambiguous result is repaired by dropping/rebasing
invalid history, restoring the action, or completing its lifecycle—not by pushing again.
Incomplete asks for exact objects/history or a simpler rewrite and files no retry.

Local diagnosis uses the same paired contract:

```sh
python3 automation/reconcile/reconcile.py --check \
  --at-transition merge \
  --branch task/<task-id> \
  --range <B>...<N> \
  --ref-update <O> <N>
```

A repository pre-push prevention hook is outside this task. The existing exact-lease backlog
task owns arbitrary/multiple-ref atomic handling and binding
`--force-with-lease=<ref>:<O>`; observing O without the lease cannot prevent a later remote
advance.

### Implementation ownership

1. Core runtime owns `automation/reconcile/reconcile.py` and, if needed, one module under
   `automation/reconcile/`: preflight, graph, multimap, authority, budgets, immutable result.
2. Core tests own `automation/tests/test_reconcile_queue.py`, including its current workflow
   source assertion and every DAG/transaction/budget/damaged-control case.
3. GitHub adapter owns `.github/workflows/harness.yml` and
   `automation/tests/test_github_action_projection_workflow.py`.
4. Human contract owns `handbook/git-workflow.md`, `message-queue/AGENTS.md`, and
   `automation/AGENTS.md` if its CLI contract changes.

Task records retain one integration owner. Local pre-push/lease work is a separate task/PR.

### Accepted POC and production gates

The accepted POC is `d12b799a2fa27b05a5ee2af1b422131856296b41`, tree
`0f5b8f3c840055bf66f7c59e2493a72e948d5163`, evidence
`sha256:dce421f2a526ffdb023a24ab57ffee48b545ac3f5f7270b080e6dd2e84f71058`.
Two fresh roots with different hash seeds, an installed French locale, and different time
zones produced byte-identical 204-row streams: 167/167 scenarios, 34/34 damaged-mode
controls, and 4/4 aliases. The auditor rejected 68/68 grammar, association, locale,
history, byte, and regeneration attacks. Three final independent verifiers unanimously
accepted semantic/DAG behavior, evidence mechanics, and execution-budget/ordinary-check
composition.

Production completion requires all mapped semantic families; the exact neutral-boundary,
persisted-collision/absent-arm, mixed-root, reintroduction, supplier, binding, retry/pickup,
move and squash/cherry-pick cases; fast-forward/zero/no-or-multiple-base/object-fault cases;
every exact/limit-plus-one budget; child terminate/reap and zero partial cache/result;
writer combinations with earlier Findings and byte-identical state on incomplete preflight;
one graph enumeration, zero extra parent queries, and bounded 128+ commit performance; all
five ordinary-range seams; push/PR endpoint matrices and real same-repository/fork canaries;
PCX-21/22 staged behavior; targeted/full/reconciler/cold-clone tests; core-fit review; and a
fresh immutable-revision adversarial panel.

### Amended non-goals

- no new queue identity field, schema migration, dependency, service, or provider state;
- no traversal before `C` or behind a neutral outside boundary;
- no replay, range-diff, patch-id, path similarity, synthetic authority, or squash receipt;
- no selected base `M`, PR API, current-ref fallback, or base-vs-task authorship claim;
- no automatic closed-fork coverage, tag policy, or local pre-push hook;
- no claim that an advisory check prevented a push;
- no self-evolving agent authority over evaluator, credential, evidence, or admission;
- no supplier review successor/reask/boundary support before typed obligations and budgets
  have observed-red coverage.

### Amended core fit

**Agent substitution:** pass — the rule consumes committed Git objects and repository queue authority, so another agent runtime preserves it
**Provider substitution:** pass — any CI/provider or local caller that supplies immutable O/N preserves the core result; provider state is not authority
**Repository substitution:** pass — any adopted repository using AgentFold's queue and rewritten-history gate needs the same false-accusation and real-loss protection
**User-global writes:** none
**Why AgentFold core:** rewritten-history continuity and queue lifecycle authority are reconciler invariants, not local configuration, a service, private overlay, or separate plugin
**Thin adapter:** canonical=.github/workflows/harness.yml; optional=yes; policy=none; writes=repo-only

## 2026-09-01 correction amendment — two-sided proof and trusted transport

The five-lens review of `09b9e08cfbe127ebdb886a5a4438c0ba3391e1ce`
rejected that revision four votes to one. This correction supersedes the amended graph,
Finding projection, CLI composition, budget, GitHub-adapter, production-gate, and human
workflow paragraphs above. The O/N-only causal model and the accepted POC remain selected;
production work is still unopened.

### Two-sided graph and one-sided authority

The bounded graph is the union `(C..O) ∪ (C..N)`, plus the `C` snapshot. One streaming
`rev-list --parents --topo-order O N ^C` child supplies every intrinsic parent record and
each commit is marked old-side, new-side, or shared. Both sides share one aggregate budget.
The old side proves that each identity present at `O` has one continuous occurrence from
`C` to `O`; endpoint byte equality alone is not continuity. Old-side deletion/recreation,
binding removal/restoration, hidden-byte restoration, collision, or unreadable history is
a failed proof.

Only new-side children can be resolution events or causal roots. Only `N` is the final
frontier. Old-side commits cannot authorize, compete with, or suppress a new-side root;
they establish the integrity of the displaced endpoint. Immediate parents outside the
union remain boundary snapshots, and their ancestors remain unread. The one streamed map
serves every parent consumer, so additional parent subprocess queries have a hard limit of
zero.

Every identity at `O` receives one complete proof, whether it disappears or remains at
`N`. A disappeared identity without exactly one valid explanation produces one stable
Finding. A persisted identity with an invalid, ambiguous, duplicate, outside-collision,
absent-arm, delete/recreate, mutation, or binding proof also produces one stable Finding.
The Finding key is the domain-separated old identity. One canonically sorted typed-reason
tuple carries every failure family, so one identity produces one Finding even when its
evidence contains several failing edges or families.
Ordinary `B...N` checks remain independent and may report their own different invariant.

### Closed CLI and checkout composition

`--ref-update` has exactly one grammar: one occurrence followed by exactly two non-zero
full object-format OIDs, and accompanied by one non-root `--range B...N`. Duplicate
occurrences, a partial pair, zero OIDs, `root:N`, a range head other than `N`, an unknown
old `--displaced-tip` option, and an unreadable/non-commit endpoint are exit 2 before any
snapshot, Finding, or writer. There is no standalone or compatibility mode.

Read-only CI may have either `HEAD == N` or an exact two-parent synthetic merge candidate
whose second parent is `N` and whose first parent contains the event base. The ordinary
reconciler range remains `B...N`; candidate-policy checks may separately use the
candidate-headed range. Candidate binding failure is incomplete. A ref-update invocation
with any writer flag additionally requires `HEAD == N`, preventing historical provenance
from mutating an unrelated checkout. Parser/help, duplicate-option, retired-option,
N-not-HEAD, synthetic-candidate, and every-writer cases are production admission tests.

Argument parsing and the minimal ref-update preflight occur before the global Git snapshot
cache starts. On divergence, the complete bounded continuity result is committed to a
transaction-local immutable value before the global index, HEAD path list, ignore list,
ordinary Findings, output, retry state, generated indexes, open-actions, or queue fold is
read or changed. Incomplete classification publishes only one bounded stable diagnostic
and exit 2. Every writer combination, including an invocation that would otherwise have
earlier Findings, proves byte-identical worktree and index state on incomplete preflight.

### Closed historical interface and result bounds

Historical authority is refactored onto the same budget object, streamed graph, bounded
object reader, tree walker, snapshot cache, and typed obligation evaluator as occurrence
proof. It cannot recursively invoke Git history, buffer `git log` or `ls-tree -r`, or enter
an arbitrary registered checker. Generated-retry authority calls a bounded historical
checker interface; helper inputs, outputs, records, nodes, invocations, and obligation
replays are charged before work. A live child is terminated and reaped on every refusal.

The following rows extend the earlier production table and make it exhaustive. A later
implementation may lower a number, but every retained counter has an exact and a
limit-plus-one test before the design can be amended upward.

| Additional dimension | Limit |
|---|---:|
| Graph lines / commit tokens | 4,096 / 4,096 |
| Merge-base stdout / peak line bytes | 64 KiB / 4 KiB |
| Merge-base lines / tokens | 64 / 64 |
| Shallow-probe stdout / peak line bytes | 64 / 16 |
| Shallow-probe lines / tokens | 2 / 2 |
| Git stderr bytes across children | 256 KiB |
| Object-header bytes | 4 MiB |
| Object-cache hits | 262,144 |
| Raw tree-entry name bytes | 8 MiB |
| Graph stream chunks / peak chunk bytes | 65,536 / 1 MiB |
| Whole-graph buffered bytes | 0 |
| Queue snapshot requests / cache hits | 262,144 / 262,144 |
| Queue subtree reads | 4,096 |
| Identity derivations / mutation checks | 262,144 / 262,144 |
| Production helper calls | 16,384 |
| Production helper input / output bytes | 8 MiB / 16 MiB |
| Production helper output records | 262,144 |
| Historical helper nodes | 4,096 |
| Additional parent subprocess queries | 0 |
| Historical checker invocations | 8,192 |
| Support-adoption checks / obligation replays | 8,192 / 65,536 |
| Carry-proof nodes / edges | 262,144 / 262,144 |
| Immutable result rows / references | 262,144 / 524,288 |
| Immutable retained result bytes | 32 MiB total / 1 MiB per row |
| Result serialization bytes / peak chunk | 32 MiB / 1 MiB |

Rows and references use deduplicated proof IDs rather than copied aggregate structures.
Each row, reference, payload, cache entry, and serialization chunk is pre-charged before
allocation or retention. Result overflow discards the result and transaction-local caches,
publishes no partial Finding or evidence, and records only the bounded incomplete
diagnostic. Exact/+1 gates cover both graph arms, every table row here and above, the
historical generated-retry path, result retention, serialization, and child cleanup.

### GitHub event matrix and trust boundary

Push continuity applies only when `github.event.ref` is a `refs/heads/*` branch and uses
the payload's exact `before` and `after`; `github.ref_name` and `github.sha` are observations,
not endpoint authority. Creation has zero `before` and real `after`: ordinary checks run
against `after` and continuity is omitted. Deletion has `deleted=true` and zero `after`:
deleted-ref candidate checking is skipped, the zero value is cross-checked, and repository
tests may still run against the default-branch checkout without naming it as the deleted
branch. Fast-forward and divergent pushes use the exact non-zero pair.

PR synchronize continuity uses trusted base-repository workflow code under
`pull_request_target` only as a data inspector. It never checks out, imports, or executes
candidate code. The event's top-level `before/after`, `pull_request.head.sha`, head
repository identity, and branch identity are mandatory and cross-checked; missing or
contradictory fields are coverage-unavailable exit 2. Exact O/N objects are fetched only
from the event-named GitHub repository into an isolated object directory, then parsed by
the trusted base reconciler. The candidate-controlled `pull_request` lane remains useful
for repository tests but is not continuity authority.

The trusted lane has read-only permissions, `persist-credentials: false`, no secrets,
quoted environment transport, GitHub-host/repository-identity validation, no mutable ref
fallback, and an adapter timeout. A transport POC must select and demonstrate a numeric
pack-input and temporary-disk limit that refuses before unbounded unpack or object
admission; core object budgets do not substitute for that network boundary. The adapter
implementation stays gated until that POC is observed red at limit-plus-one. Candidate
objects are data even when a fork supplies them, and `pull_request_target` never executes
candidate repository code.

GitHub documents conflicting behavior for fork payload fields, so fork support remains
unverified until live canaries pass. Same-repository, fork, and conflicted-fork synchronize
canaries each record the fixture repository, event/run URL, trigger action, raw field
presence, exact O/N, expected classification/exit, observed classification/exit, cleanup,
and immutable evidence digest. The fixture procedure creates O, rewrites to N, captures
the event, asserts `after == head.sha`, and tests one unavailable old O as exit 2. The
conflicted-fork case proves that the trusted lane runs without executing fork code. The
canary scripts and fixture README own setup, assertions, and cleanup so the gate is
rerunnable rather than prose.

The executable surface is
`python3 automation/canaries/github_ref_update.py <provision|capture|assert|cleanup>
--fixture automation/canaries/github-ref-update-fixture.json --run-id <id>`.
The checked-in fixture names one writable base repository, one separately owned fork, the
base branch, and the deterministic `refs/heads/agentfold-canary-<run-id>` prefix; missing
or identical repository identities fail before provisioning. `provision` prints and
records the created refs/PRs and O/N pairs, `capture` downloads event artifacts by run ID,
`assert` expects same-repository and fork synchronize classification at the recorded pair,
conflicted-fork trusted-lane execution, unavailable-old-O exit 2, read-only permissions,
and no candidate checkout, and `cleanup` deletes only identities in that signed run
manifest. The evidence artifact is the canonicalized manifest plus payload-field digest,
run URLs, exact command output, and cleanup result. Production admission requires all four
commands to exit 0; an absent fixture, credential, event, or artifact is unverified rather
than skipped.

A fork update made while the PR is closed remains uncovered because no synchronize event
exists; reopening does not reconstruct the displaced pair. A provider that omits the
required fork payload also remains coverage-unavailable. Base advance or retarget is
ordinary-only and does not itself guarantee a new PR workflow run. A remote continuity
check cannot prevent or undo a push; once configured as a required check it can block the
subsequent merge.

### Human development and repair cycle

The local cycle fetches both the current base and remote task ref, records exact remote
`O`, rewrites and inspects the branch to `N`, and runs the paired local diagnosis against
`B...N` and `O N`. Publication uses
`--force-with-lease=<ref>:<O>`. A rejected lease means another actor moved the ref; the new
remote O is fetched and the classification is repeated rather than overridden.

An invalid or ambiguous CI result is repaired by creating `N'`, running the local paired
check against the now-current remote tip, and pushing `N'` with its exact lease. Only an
unchanged retry is invalid; a repaired branch necessarily has another push. When remote CI
cannot fetch old O, the developer's still-present local O remains useful for diagnosis,
while the remote result remains coverage-unavailable until the object becomes exactly
fetchable or a later rewritten update supplies a new checkable pair.

### Corrected production gates

Production starts only after a new immutable revision receives the complete five-lens
review. Its tests include old-side deletion/recreation, binding restore, hidden-byte
restore, two-arm aggregate budgets, stable persisted Findings and counts, the closed CLI
grammar, synthetic read-only checkout, writer checkout binding, pre-snapshot transaction
ordering, every exhaustive exact/+1 dimension, bounded historical generated-retry work,
and removal of every active `--displaced-tip` source/document/workflow assertion.

The GitHub adapter remains a separate gate after its bounded-transport POC and executable
same-repository/fork/conflicted-fork canaries. A missing credential or fixture records
unverified coverage rather than a fabricated pass. Core classification can proceed in its
own non-overlapping implementation unit only after the corrected design review; adapter
completion cannot be claimed until all transport and canary evidence exists.

## 2026-09-01 correction amendment 2 — intrinsic ancestry and edge-scoped adapters

The fresh review of `30c9cc0f9a71a3ae5f82cefb7928a818c383f421` stopped after
three independent blocks. This section supersedes the graph command, historical-helper,
deadline, GitHub call-shape, coverage, required-check, evaluator-binding, canary-manifest,
push-tuple, and branch-lifecycle text above. Production remains unopened.

### Intrinsic graph command

The intrinsic set is
`(Desc(C) ∩ Anc(O)) ∪ (Desc(C) ∩ Anc(N))`, plus the `C` snapshot. Its exact production
enumeration is one streamed child:

```sh
git --no-replace-objects rev-list \
  --parents --topo-order --reverse --ancestry-path O N ^C
```

Raw parent OIDs stay on each emitted record, so an immediate outside parent can be read
once as a boundary snapshot. That parent is not intrinsic and its ancestors are neither
emitted nor charged to the intrinsic graph budget. Mirrored old- and new-arm gates extend
a neutral outside lineage beyond 4,096 ancestors and prove byte-identical classification,
result, intrinsic counters, and one boundary snapshot. Removing `--ancestry-path`, opening
the outside ancestor, or charging it is an observed-red damage control.

### Historical evaluator registry and deadlines

Generated-retry support uses a separate explicit
`HISTORICAL_RETRY_EVALUATORS: check-id → bounded evaluator` registry. Generic dispatch
through `CHECKS` is forbidden. Every check ID for which `generated_retry_collectable()` is
true has one named historical evaluator or is explicitly unsupported. An unsupported ID
makes the provenance result incomplete; it is not treated as cleared or invalid. Admission
requires semantic parity at the same immutable tree for every collectable check ID, plus
exact/+1 input, output, record, object, path, helper, and obligation-replay tests. The
`queue-resolution` ID remains non-collectable and cannot authorize its own deletion.

Every child belongs to one process group and has a monotonic deadline as well as byte and
record budgets: 30 seconds per one-shot Git child, 10 seconds per request/response exchange
with a long-lived batch child, and 120 seconds aggregate classification time. Timeout,
EOF, malformed output, and budget refusal terminate the process group, reap every child,
discard partial caches/results, emit one stable incomplete diagnostic, preserve every
writer byte, and exit 2. Injected-clock tests stall `rev-list`, `merge-base`, `cat-file
--batch`, and one historical evaluator before and after partial output; exact-deadline
completion succeeds and the first monotonic tick beyond it refuses.

### Two core entrypoints, one classifier

One provider-independent library owns the O/N classifier and accepts only immutable O/N,
a bounded committed-object source, repository queue policy from those objects, and a
budget/deadline profile. It has no worktree, index, current HEAD, provider, writer, or
ordinary-range dependency.

`automation/reconcile/reconcile.py --ref-update O N --range B...N` is the integrated local
and push entrypoint. It runs the library preflight, then the existing ordinary checks and
optional writers under the checkout rules already specified.

`automation/reconcile/ref_update.py --git-dir <isolated-git-dir> --old O --new N` is a
dedicated read-only historical entrypoint. It rejects every writer, range, worktree, index,
provider, and compatibility option; emits only the canonical continuity result; and never
imports Python or executable content from the object source. The trusted GitHub lane runs
this entrypoint from one pinned trusted-code checkout while the candidate object source is
a different isolated Git directory. Library-parity tests require byte-identical results
and counters between both entrypoints for the same O/N/object database.

Ordinary `B...N`, index, and worktree checks for a pull request remain in the unprivileged
`pull_request` lane. They are separate results and execute candidate repository code only
with the lane's unprivileged token. The trusted historical lane never tries to make its
base-code checkout equal N or a synthetic candidate.

### Honest remote scope and coverage debt

Each remote result classifies exactly one immutable edge O→N. It never asserts cumulative
branch continuity. An unavailable O→N remains an unresolved edge forever unless that exact
pair is rerun successfully or an equally authoritative immutable receipt for that exact
pair is introduced by a separately approved design. A later N→N' result cannot discharge,
replace, summarize, or turn the earlier edge green. Restoring O and performing a new O→N
update creates a new auditable edge but does not rewrite the old event record.

This task introduces no durable provider debt store and no trusted status publisher.
Consequently GitHub continuity output is advisory and edge-scoped, especially for forks;
it is not a required-check context on N and no branch-level green claim exists. A later
task may design a least-privilege publisher plus durable per-ref/per-PR debt, but it must
consume revision-bound authenticated receipts, prevent candidate-controlled context
forgery, and carry every unresolved original edge. The production and canary gates include
the laundering sequence `O→N unavailable; N→N' locally valid` and require two independent
records: the first stays unavailable and the second says only that its own edge is valid.

The same-repository push job naturally runs on N and may expose its edge result to branch
policy, but it still cannot claim cumulative continuity or erase a prior unavailable edge.
The trusted fork lane cannot publish a required check to N with read-only permissions, and
the design makes no such claim.

### Trusted evaluator identity and job isolation

The trusted data-inspection job binds the workflow repository ID, base repository ID,
`github.workflow_ref`, and immutable `github.workflow_sha`, then checks out and verifies
that exact evaluator SHA. A PR targeting another base branch remains acceptable only when
those identities agree and that branch's exact workflow SHA supplies the evaluator. All
third-party actions are pinned by full commit OID.

The parser job alone has `contents: read`, `persist-credentials: false`, no secrets, no PR
write/API step, no shared cache or workspace, a sanitized Git config, disabled replacement
refs and lazy fetch, and an allowlist of required Git protocols. Candidate O/N objects enter
only the isolated object directory. The job neither checks out their tree nor places it on
Python, shell, action, hook, filter, pager, editor, credential-helper, or executable search
paths. Evidence binds evaluator repository/SHA separately from candidate repository/O/N.

### Executable canary manifest

The canary CLI uses a locally generated closed-grammar `scenario-id`; provider run IDs are
a list discovered after events fire. Provisioning installs and records the already-reviewed
fixture workflow/evaluator SHA on the fixture default branch before scenario refs exist.
Every ref and PR is created atomically only if absent. A name collision refuses without a
force update.

The manifest is canonical JSON with a SHA-256 digest, not a signed artifact. It binds base
and fork repository numeric IDs, scenario nonce, exact created ref names/OIDs, exact PR
numbers/node IDs, evaluator SHA, workflow ID, expected event/ref/N tuples, discovered run
IDs, artifact digests, and cleanup state. Capture discovers each run by the complete
repository/workflow/event/ref/N tuple rather than by time or name alone. Raw event fields
are copied into immutable run artifacts by the pinned trusted workflow before assertions.

Cleanup is compare-and-delete: repository IDs, scenario nonce, PR IDs, and each current ref
OID must still match the manifest. Drift refuses deletion and is recorded. Canary tests
cover collision, digest forgery, replay, drifted ref, partial provisioning, multiple runs,
missing artifacts, assertion failure followed by cleanup, and idempotent cleanup of already
absent exact identities. There is no broad pattern deletion.

### Complete push and branch lifecycle tuples

The push adapter admits only these mutually exclusive branch tuples derived from
`event.ref`:

| Shape | Required payload |
|---|---|
| creation | `refs/heads/*`, `created=true`, `deleted=false`, zero `before`, non-zero `after` |
| deletion | `refs/heads/*`, `created=false`, `deleted=true`, non-zero `before`, zero `after` |
| update | `refs/heads/*`, both flags false, both endpoints non-zero |

Every contradiction is coverage-unavailable. `ref_name`, `github.sha`, and `forced` are
cross-check observations only. Creation runs ordinary checks at `after` without continuity;
deletion runs no deleted-branch candidate check; an update runs ordinary and O/N checks.

Human documentation covers first publication, fast-forward work, restack, lease rejection,
repair publication, CI-unavailable diagnosis, and branch retirement. It describes the
observed O and exact expected-O lease but leaves automatic publisher/pre-push enforcement,
multi-ref atomicity, initial create-if-absent publication, and compare-and-delete retirement
to backlog task `2026-08-03-bind-task-branch-pushes-to-observed-tips`. This task does not
claim or absorb that task's acceptance criteria.

### Revised gate order

The next immutable design review covers all five lenses from scratch. After it passes, the
core library and its two local entrypoints may enter isolated implementation units. The
GitHub adapter still waits for the bounded-fetch POC, installed fixture workflow, and all
live canaries; absent provider credentials keep that adapter unverified rather than
weakening its contract. No remote required-check, cumulative-continuity, fork-authority, or
automatic-publisher completion claim exists in this task.

## 2026-09-01 correction amendment 3 — policy binding and closed provider procedure

The review of `db720d3321ee25f09c82def46d77fd418735e904` stopped after a
semantic acceptance and two independent blocks. This section supersedes evaluator-policy
selection, trusted workflow identity, the PR matrix, fixture installation, canary
authentication/discovery, and the abbreviated human lifecycle above. The intrinsic DAG,
bounded execution, two-entrypoint library, and edge-only remote claim remain selected.

### Authority-policy digest

The classifier's executable authority surface is extracted completely from
`reconcile.py` into a closed file manifest owned by `ref_update_core.py`. It includes the
classifier, canonical result encoder, queue identity/mutation rules, explicit historical
retry evaluators, support-certificate interpreter, and both CLI parsers. Integrated glue,
provider adapters, ordinary checks, and writers cannot define or override an authority
decision.

`authority-policy/v1` hashes the fixed ordered path list and each exact byte payload with
domain-separated, length-prefixed SHA-256. At every non-zero O/N update, including a
fast-forward, the policy bytes at O,
at N, and in the executing evaluator checkout must all exist and produce the same digest.
Any missing file, extra authority import, digest mismatch, registry mismatch, or policy
change is incomplete before graph or authority work. The running interpreter also hashes
its own on-disk policy files and requires them to equal its checkout tree, preventing an
uncommitted or substituted evaluator.

The integrated and isolated entrypoints therefore execute the same policy digest for a
given pair. A candidate that changes one collectable checker, evaluator,
registry member, identity rule, or result encoder cannot use the old policy to authorize a
deletion and cannot ask the old trusted evaluator to interpret new semantics; both honest
entrypoints return the same canonical `policy-version-mismatch` incomplete result. Policy
rollout occurs as its own reviewed fast-forward, whose continuity result is explicitly
policy-version-mismatch, and becomes the baseline for later pairs after landing. The
version-independent bootstrap parser and minimal incomplete envelope are frozen outside
the policy surface; cross-version tests bind their bytes. Fast-forward updates do not
suppress continuity Findings, and ordinary checks still run independently.

Cross-version gates change each policy-surface file independently at N, change O alone,
change the executing checkout alone, add an undeclared import, alter one collectable
checker, and alter only ordinary/provider code. The first five shapes are byte-identical
incomplete results from both entrypoints; ordinary/provider-only changes preserve the
policy digest and classifier result. A build-time import audit rejects authority code that
reaches outside the closed manifest except Python's pinned standard-library allowlist.

### Authoritative pull-request event matrix

Only `pull_request_target` with action `synchronize` may transport a PR O/N pair to the
trusted historical entrypoint. Top-level non-zero `before` and `after` are mandatory;
`after` must equal `pull_request.head.sha`; the head repository numeric ID/full name and
head ref must be present; and the source repository must equal the event-named repository.
Both exact O and N are fetched from that repository only. A mutable ref, merge ref, current
PR API lookup, base ref, checkout HEAD, or another repository can never replace either
endpoint. Missing/null fields, mismatch, ambiguous object format, or exact-fetch failure is
coverage-unavailable exit 2.

| PR cycle | Edge behavior |
|---|---|
| same-repository synchronize | trusted edge audit plus the independent push audit; results remain edge-scoped |
| fork synchronize | trusted data-only edge audit when the exact payload and objects exist; otherwise unavailable |
| conflicted fork synchronize | expected trusted data-only audit, but unverified until the live canary |
| opened, edited, ready, review, assigned | no O/N pair; unprivileged ordinary candidate checks only |
| closed or reopened | no reconstructed displaced pair; ordinary checks only and the closed-period gap remains |
| force-push while fork PR is closed | uncovered edge; reopening cannot synthesize it |
| stale rerun | original event O/N and evaluator SHA only; no current-ref substitution |
| base advance or retarget | candidate-policy/ordinary input only; never O/N and no guaranteed new run |
| multiple PRs for one head | each event may repeat the same edge audit, with separate ordinary ranges |
| null/deleted head repository | unavailable; no fallback |

The unprivileged `pull_request` lane accepts either direct N or the already specified exact
two-parent synthetic checkout for ordinary candidate checks. It does not publish trusted
continuity. Same-repository push remains the primary edge observation before, during, and
after a PR. Fork and conflict results stay advisory; no required-check or cumulative claim
is implied.

### Trusted workflow identity

For `pull_request_target`, evaluator authority always comes from the validated workflow
repository, workflow path, default ref, and immutable `github.workflow_sha`. The PR's
`base.ref` and `base.sha` are candidate-policy data and never executable trust roots,
including when the PR targets a non-default branch. `github.workflow_ref` must name the
expected base-repository workflow path at the repository's default ref, repository numeric
IDs must match, and verified checkout HEAD must equal `github.workflow_sha`.

The evaluator policy digest from that exact checkout must also equal the O/N policy digest
for divergent classification. All job-isolation constraints from amendment 2 remain
binding. A mismatch is incomplete, not a fallback to base, candidate, or current code.

### Preinstalled fixture and cleanup capability

The dedicated canary repository and separately owned fork have a reviewed workflow and
evaluator preinstalled on the default branch as a prerequisite outside a scenario run.
`provision` is read-only toward the default branch: it verifies repository numeric IDs,
workflow path/ID, default ref, exact installed workflow/evaluator SHA, action pins, and
policy digest before creating scenario refs. It never installs, updates, restores, or
deletes default-branch content. A fixture upgrade has its own reviewed PR and exact lease,
outside scenario cleanup.

Provisioning creates a random 256-bit cleanup capability and stores it only in a
mode-0600, git-ignored `tmp/canary/<scenario-id>/capability` file. It never enters an
artifact, log, manifest, environment dump, or provider field. Canonical manifest bytes are
authenticated with domain-separated HMAC-SHA-256 over the fixture IDs, nonce, created
identities, and one cleanup epoch. Cleanup requires that external capability, verifies the
HMAC and unused epoch, and then performs the earlier compare-and-delete checks. A copied or
edited manifest with a freshly recomputed plain digest remains unauthorized. PR cleanup
also verifies exact repository/base/head refs, PR/node ID, scenario nonce marker, and
still-open state before closing; provider artifacts are never deleted from manifest claims.

Cleanup takes an exclusive lock on the local capability state and atomically journals
`open → in-progress → complete`; each exact mutation is durably recorded before the next.
A crash in-progress can resume only the same authenticated epoch, while complete refuses
replay. Loss of the
capability leaves the narrow fixture identities for manual human review rather than
broadening deletion authority.

### Bounded run and artifact discovery

The scenario ID and start time only bound enumeration; they are not event authority.
Capture polls for at most 15 minutes, ten seconds per poll, ten pages, 100 workflow runs,
eight artifacts per run, 64 MiB aggregate compressed bytes, 128 MiB aggregate extracted
bytes, and 1 MiB per raw event record. It first filters the exact base repository numeric
ID, workflow ID/SHA, event name, and scenario time window. It then downloads the pinned
raw-event artifact and accepts exactly one complete repository/workflow/event/ref/N tuple
for each expected case. Zero, duplicate, malformed, oversized, late, or ambiguous matches
are unverified.

`GH_CANARY_BASE_TOKEN` and `GH_CANARY_FORK_TOKEN` are separate least-privilege credentials.
The base token is never placed in a fork remote, process, request, environment inherited by
a fork command, credential helper, or log; the fork token cannot mutate the base fixture.
The trusted workflow itself retains no credential after checkout. Tests inject paginated,
duplicate, stalled, oversized, wrong-repository, wrong-N, and cross-token responses and
prove bounded refusal plus authenticated cleanup.

### Current manual human lifecycle

Before a rewrite, the developer fetches the base and exact remote task ref, records O, and
retains the local O object. The rewrite produces N; inspection and local O→N plus B...N
classification precede publication. Publication uses the exact observed-O lease. A lease
rejection stops without automatic refresh, force, or retry; a later attempt begins by
observing a new O and repeats the full plan.

After a published invalid/ambiguous edge, repair starts from the then-current exact remote
N, produces N', runs local N→N' plus its ordinary range, and publishes with
`--force-with-lease=<ref>:<N>`. Local success after remote coverage-unavailable is useful
diagnosis only and never clears or replaces that remote O→N record.

For a first publication, the currently supported manual effect is an explicit remote
absence check followed by a normal create push; the check and push still have a race and no
atomic enforcement is claimed. For retirement, the currently supported manual effect is
an observed current tip followed by an exact expected-tip lease deletion; deletion runs no
candidate continuity. Automatic create-if-absent, compare-and-delete, pre-push prevention,
and multi-ref atomicity remain wholly owned by backlog task
`2026-08-03-bind-task-branch-pushes-to-observed-tips`.

### Gate restatement

The core implementation gate is a fresh five-lens acceptance of the policy digest, closed
event matrix, and prior semantic/budget contract. The adapter gate is the bounded-fetch POC
plus the preinstalled-fixture live canaries. A reviewed core can complete independently
while the optional GitHub adapter remains unimplemented or unverified; such a result makes
no claim of remote cumulative protection, required checks, automatic publication, or
provider-independent coverage debt.

## 2026-09-01 correction amendment 4 — split transactions and exact GitHub identities

The review of `0a488cc38bf772982d06a6519f828c6cc9bbd43f` stopped after three
blocks. This section supersedes fast-forward/policy transaction composition, policy
budgets, GitHub repository identity and event rows, evidence durability, fixture
relationship checks, run-attempt identity, and first-publication commands above.

### Continuity and ordinary transactions

Every non-zero O/N continuity invocation follows exactly this order:

1. bounded authority-policy verification across O, N, and evaluator;
2. on mismatch, one canonical incomplete result, exit 2, zero continuity Findings;
3. on a matching policy with `O <= N`, one clean fast-forward result before graph or action
   provenance;
4. on matching divergent endpoints, the complete bounded two-sided classification.

Continuity never reports a fast-forward queue mutation. Ordinary `B...N` checks own those
mutations. An incomplete continuity transaction never runs ordinary checks or writers in
the same invocation, preserving zero partial output and mutation.

Every non-zero O/N workflow update therefore has two explicit, separately captured invocations: the
read-only `ref_update.py` continuity transaction and `reconcile.py --check --range B...N`
ordinary transaction. The ordinary invocation runs even when continuity returns exit 2;
its result cannot clear, replace, or relabel the incomplete edge, and it has no writer
flags. Local combined `reconcile.py --ref-update O N --range B...N` remains transactional:
ordinary checks and writers run only after complete continuity. A developer who needs
ordinary diagnostics after local incomplete provenance runs a second read-only range-only
command.

Admission includes same-policy fast-forward deletion (continuity clean, ordinary block),
policy-changing fast-forward deletion (continuity exit 2, separate ordinary block), and
policy-changing divergence. The workflow result presents both statuses without collapsing
them into one exit code or summary.

### Bounded policy bootstrap

Policy verification has deterministic logical counters, independent of filesystem cache
or object-reader implementation. O, N, and evaluator sources are always streamed in that
fixed order and fully charged before comparison, so both entrypoints report identical
counters even when the first mismatch appears early.

| Policy dimension | Limit |
|---|---:|
| Logical policy sources | 3 exactly |
| Manifest paths | 32 |
| Manifest path bytes | 8 KiB |
| Policy files per source | 32 |
| Policy bytes per file | 1 MiB |
| Policy bytes per source | 4 MiB |
| Policy bytes all sources | 12 MiB |
| Stream chunks / peak chunk | 6,144 / 64 KiB |
| Hash input bytes | 12 MiB |
| Import-audit nodes / edges | 128 / 512 |
| Bootstrap diagnostic bytes | 64 KiB |

Source count, path, file, byte, chunk, hash, import-node/edge, deadline, and diagnostic work
is pre-charged. On-disk evaluator reads use the same streaming reader shape as committed
blobs and do not add physical-cache counters. Exact/+1 gates damage O only, N only,
evaluator only, the manifest, an import edge, and each byte/row/chunk limit; all assert the
same result bytes/counters, child cleanup, and writer state from both entrypoints.

### Base identity versus object-source identity

The trusted workflow binds base identity independently:
`github.repository_id == event.repository.id == pull_request.base.repo.id`, with matching
base full name and validated workflow repository. Candidate object-source identity is
`pull_request.head.repo.id/full_name`; O and N are fetched only from that nested head
repository. A same-repository PR requires head ID equal base ID. A fork requires them to
differ and satisfy the fixture/provider fork relationship. An identical OID deliberately
present in both repositories still selects the head repository by numeric identity; object
text never substitutes for repository provenance.

The base credential is scoped only to the base host/repository. Fork fetches receive only
the separately scoped fork credential in a scrubbed child environment. No credential
helper, alternates file, redirect to another host/repository, or URL supplied by payload
data is accepted.

### Closed PR action matrix

The exact configured `pull_request`/`pull_request_target` actions are `opened`, `edited`,
`reopened`, `synchronize`, `ready_for_review`, `review_requested`,
`review_request_removed`, `assigned`, `unassigned`, and `enqueued`. Only synchronize has
continuity inputs. Reopened and the other non-synchronize actions may run ordinary
candidate checks only when their required payload and exact candidate exist.

`closed` is not a configured candidate-check action and has no general continuity or
ordinary-check guarantee. A merged close is observed only through the resulting base push;
an unmerged close, a fork close, an empty payload, or a vanished merge ref is unavailable
for candidate checking. A force-push while closed remains an uncovered edge.

GitHub suppresses `pull_request_target` for SHA-like head branch names. Such a fork update
is an explicitly uncovered edge: no missing run becomes success and no base push exists.
The negative live canary creates an exact SHA-like fork ref, triggers synchronize, polls
within the bounded discovery window, records that no trusted tuple appeared, and emits the
expected unavailable coverage record rather than a green classification.

### Retention-bounded evidence

An unavailable edge remains logically unresolved unless that exact pair is later audited
successfully, but this adapter stores no durable debt. GitHub runs and artifacts are
retention-bounded; after expiry the adapter cannot prove that the old observation is still
visible. Every result and human guide therefore states that a later green edge establishes
only its own pair and cannot establish prior coverage, whether the old run remains visible
or has expired. Permanent visibility and cumulative completeness require the separately
designed authenticated receipt/debt store.

### Fork fixture relationship and workflow attempt

Before any scenario mutation, fixture verification binds base and fork repository numeric
IDs, distinct owner numeric IDs, `fork=true`, and `fork.parent.id` plus `fork.source.id`
equal to the base/source fixture IDs. Each field has an independent damaged fixture test;
an unrelated repository, same-owner repository, detached fork, or wrong network refuses
before provisioning.

Every provider execution identity is `(run_id, run_attempt)`. Manifest rows, raw-event
artifacts, discovery tuples, URLs, artifact digests, stale-rerun assertions, and cleanup
logs bind both values. Exactly one attempt may satisfy a case; mixed, duplicate, absent, or
superseded-attempt artifacts are unverified. Rerun tests keep run_id fixed, increment
run_attempt, and prove no bytes are combined across attempts.

### Atomic manual first publication

After local remote-absence observation, the supported manual creation effect is Git's empty
expected-value lease:

```sh
git push \
  --force-with-lease=refs/heads/<branch>: \
  origin <N>:refs/heads/<branch>
```

This atomically rejects an existing ref. Rejection stops the attempt; it never refreshes
and retries automatically. Automation and multi-ref enforcement remain in task
`2026-08-03-bind-task-branch-pushes-to-observed-tips`.

### Review and implementation boundary

The implementation gate remains a new immutable five-lens acceptance. Core units stay
closed before it. The optional adapter remains separately gated on bounded transport and
live canaries, including SHA-like suppression and retention-limited evidence; no missing
run, expired record, or later green edge is promoted into cumulative success.

## 2026-09-01 correction amendment 5 — exact hash framing and per-event lanes

The review of `927a48825962d0b3923751f0e3ce152f3806b697` accepted semantic/DAG
behavior and blocked budget arithmetic plus provider-lane composition. This section
supersedes policy hash counters, fork credentials, universal two-result wording, ordinary
base selection, closed-update coverage, and the rewrite-only human sequence above.

### Policy payload and framing counters

`policy_payload_hash_bytes` counts only the three sources' policy payload bytes and has a
12 MiB limit. `policy_framing_hash_bytes` separately counts the domain separator, source
labels, ordered manifest path bytes, and every length prefix, with a 64 KiB limit.
`policy_total_hash_bytes` has the exact aggregate limit `12 MiB + 64 KiB` (12,648,448
bytes). Framing is constructed and charged incrementally; it is never an unmetered
temporary buffer.

The exact maximum test uses three 4 MiB payload sources and the maximum 64 KiB framing and
succeeds. The next payload byte, framing byte, or total byte independently refuses before
hash input. This replaces the ambiguous 12 MiB `Hash input bytes` row and preserves all
other policy-bootstrap limits.

### Anonymous production fork transport

The trusted production workflow fetches public fork O/N anonymously. Its fork-fetch child
inherits no token, authorization/header variable, credential helper, cookie, proxy
credential, SSH agent, alternate object directory, or base-workflow environment. Terminal
prompting and redirects are disabled, the HTTPS host is fixed to GitHub, and the repository
path is constructed from the already validated head full name rather than a payload URL.
The base `GITHUB_TOKEN` is never sent to or made visible to the fork transport.

An inaccessible private/internal fork is coverage-unavailable unless GitHub documents and
provides an event-bound credential scoped to that exact head repository. No repository or
user secret is introduced to simulate such access. `GH_CANARY_FORK_TOKEN` exists only in
the local canary controller for provisioning/cleanup and never enters the trusted workflow
or its artifacts.

### Provider lanes and stable conclusions

The workflow exposes two non-aggregating stable results:
`agentfold-continuity-edge` and `agentfold-ordinary-range`. Each has its own success,
blocking, or unavailable domain status and evidence. The provider check conclusion is
success only for domain success and failure for blocking or unavailable. One lane never
changes the other's name, conclusion, exit code, or summary.

| Provider case | Continuity lane | Ordinary lane |
|---|---|---|
| same-repository non-zero push | exact event O/N | `B=O`, range `O...N` |
| same-repository branch creation | none | unavailable without an authenticated immutable B |
| same-repository branch deletion | none | no deleted-candidate check |
| mergeable same-repository PR | push lane is primary; synchronize may repeat edge | unprivileged `B=event base.sha`, `N=head.sha` |
| mergeable fork synchronize | trusted anonymous data-only O/N | unprivileged `pull_request` range at event base/head |
| conflicted fork synchronize | trusted anonymous data-only O/N | unavailable because `pull_request` is suppressed |
| SHA-like fork synchronize | unavailable because trusted event is suppressed | unprivileged ordinary only if that event actually runs |
| fork update while closed | uncovered | unavailable |

For a non-zero branch push, O is the immutable ordinary base as well as the continuity old
endpoint, without becoming continuity policy. Creation has no event-stable B and never
falls back to a later default ref or merge base; remote ordinary coverage is unavailable,
while repository tests may still run and local prepublication uses the developer's chosen
immutable base. PR ordinary B is the payload's immutable `pull_request.base.sha`; base
advance after event capture cannot replace it. Direct/synthetic checkout binding remains a
separate candidate-code validation.

Workflow steps capture each result even if the other exits non-zero. Same-repository,
mergeable-fork, conflicted-fork, SHA-like-fork, creation-without-base, and base-advance race
tests assert the exact pair of lane conclusions. No generic promise of two successful or
even two runnable results remains.

### Closed same-repository versus fork updates

A non-zero same-repository head push is observed by the repository push event regardless
of whether its PR is open, closed, conflicted, or absent. Closing or reopening never
reconstructs another pair. An external/fork push while its PR is closed has no base
repository push or synchronize observation and remains uncovered. A later reopen can run
ordinary candidate checks but cannot synthesize the closed-period edge.

### Manual sequence for every non-zero update

Fast-forward work, a rewrite, and a repair use the same manual boundary:

1. the developer fetches the current remote ref and chosen immutable ordinary base, records
   and retains exact O;
2. local work produces and inspects N;
3. read-only O→N continuity and the event-appropriate ordinary range run as two commands;
4. publication uses `--force-with-lease=<ref>:<O>` even for a fast-forward;
5. lease rejection stops without refresh or retry, and a later attempt observes a new O
   and repeats the complete sequence.

Incomplete continuity does not prevent the second read-only ordinary diagnostic and that
diagnostic never relabels the edge. The N→N' repair, empty-expect first publication, and
exact-tip retirement procedures remain authoritative. Local success never clears a remote
unavailable record or proves cumulative coverage.

### Gate boundary

The new immutable five-lens review remains the core gate. Adapter admission additionally
depends on observed provider-lane matrices, anonymous bounded fork transport, negative
SHA-like coverage, and exact budget/canary results. No private-fork, creation-base,
conflicted-ordinary, closed-fork, or cumulative protection is inferred from a missing lane.

## 2026-09-01 correction amendment 6 — canonical framing and observable provider states

The review of `22e1c00ce0fcec05da9ea6842db9d31128e2571a` accepted semantic/DAG
behavior and blocked one budget format plus the trust/observability model of GitHub push
runs. This section supersedes policy framing, creation ordinary coverage, push trust,
provider-result states, and incomplete update/deletion commands above.

### Canonical policy transcript

Each of O, N, and evaluator independently hashes this exact byte transcript:

```text
ASCII("agentfold-authority-policy/v1") || 00 ||
uint16_be(file_count) ||
for each path in ascending UTF-8 byte order:
  uint16_be(path_byte_length) || path_utf8 ||
  uint64_be(payload_byte_length) || payload_bytes
```

The domain is exactly 30 bytes including its terminal NUL. The manifest contains 1–32
unique normalized repository-relative UTF-8 paths, no empty/absolute/dot/dot-dot segment,
and at most 8,192 path bytes per source. The path list repeats identically in each source;
source labels are not hashed, so identical content has identical digests. File count and
path length use unsigned big-endian 16-bit values; payload length uses unsigned big-endian
64-bit values. There is no JSON, locale transform, platform separator, implicit newline,
or additional delimiter.

The exact reachable framing maximum is
`3 × (30 + 2 + 32 × (2 + 8) + 8,192) = 25,632` bytes. The framing cap is therefore
25,632, not 64 KiB. The payload cap remains 12,582,912 bytes. A derived
`policy_total_hash_bytes` counter must equal their sum but has no independent gate, because
a total-only +1 is unreachable when both components are capped. Exact/+1 tests separately
reach maximum payload and maximum framing, then exceed only the selected component; the
maximum combined transcript is 12,608,544 bytes and succeeds.

### Candidate-controlled push evidence

A GitHub push workflow executes the workflow bytes at candidate N. Its adapter is outside
the authority-policy digest, so its presence, endpoint transport, and reported result are
candidate-revision-controlled advisory evidence, conditional on the expected workflow
actually running. It is not the primary trusted observation and cannot prove that a
closed/no-PR update was audited. Pushes created with the repository `GITHUB_TOKEN`, deleted
or invalid workflow files, provider suppression, and candidate tampering may produce no
run.

While a PR is open, trusted same-repository remote continuity comes from the default-branch
`pull_request_target` synchronize lane. Trusted fork behavior remains as previously scoped.
A same-repository push while the PR is closed, absent, or not synchronized is covered only
by local evidence and any candidate-controlled push run; trusted remote continuity is
uncovered. Canary damage cases delete the workflow, alter O/N transport, fabricate success,
and push through `GITHUB_TOKEN`; none may become trusted or completed green evidence.

### Domain state versus provider observation

The domain state set is `success`, `blocking`, `unavailable`, `not-applicable`, and
`no-observation`.

- A completed classifier maps success to provider success and blocking/unavailable to
  provider failure.
- Not-applicable is an explicitly skipped provider lane only when the event workflow was
  created and the input shape excludes that classifier.
- No-observation means no trustworthy job result exists because the event/run/job was
  suppressed, missing, cancelled, timed out, syntactically invalid, provider-failed, or
  candidate-removed. It has no fabricated provider conclusion; external coverage is
  unavailable.

The two stable job names are promised only for workflow runs that are actually created.
Creation/deletion may expose an explicit skipped lane; closed fork, SHA-like suppression,
token recursion, deleted workflow, outage, cancellation, and timeout may expose no result.
No missing or native non-success outcome is rewritten as a completed unavailable record or
as green evidence.

| Provider case | Continuity state | Ordinary state |
|---|---|---|
| candidate-controlled non-zero push run exists | completed advisory | completed candidate-controlled advisory `O...N` |
| push run suppressed/removed | no-observation | no-observation |
| branch creation run exists | not-applicable | completed bounded `root:N` |
| branch deletion run exists | not-applicable | not-applicable |
| open same-repository synchronize | completed trusted PRT edge | completed unprivileged PR range |
| mergeable fork synchronize | completed trusted PRT edge when anonymously fetchable | completed unprivileged PR range |
| conflicted fork synchronize | completed trusted PRT edge when anonymously fetchable | no-observation |
| SHA-like fork synchronize | no-observation | completed only if unprivileged PR event runs |
| closed fork update | no-observation | no-observation |

Bounded `root:N` remains the immutable ordinary range for a branch creation and preserves
the existing first-push queue-edge protection. It uses no mutable base fallback. Creation
tests include an invalid deletion in the new history, long-history bounds already owned by
ordinary checks, and independent continuity not-applicable state.

### Exact manual refspecs

Every non-zero normal update or repair uses the complete command:

```sh
git push \
  --force-with-lease=refs/heads/<branch>:<O> \
  origin <N>:refs/heads/<branch>
```

Exact-tip retirement uses:

```sh
git push \
  --force-with-lease=refs/heads/<branch>:<O> \
  origin :refs/heads/<branch>
```

The empty-expect creation command remains unchanged. All three commands name the remote,
source OID, destination ref, and expected remote value; they do not depend on checkout,
upstream, `push.default`, or `remote.*.push`. Tests install hostile upstream, multi-ref
remote push rules, and push.default values and prove that only the named destination can
move. Rejection always stops the attempt.

### Gate boundary

Core admission remains a fresh full five-lens acceptance. Adapter evidence additionally
distinguishes trusted default-branch runs, candidate-controlled advice, explicit
not-applicability, and absent observation. No candidate workflow or missing provider result
can satisfy the trusted edge gate.

## 2026-09-01 correction amendment 7 — derived counters and bounded ordinary history

The review of `10e2d6a1cf2e7983301cdb10dd9ba1dbd976de81` accepted semantic/DAG
behavior and blocked derived-counter tests, unbounded ordinary root history, SHA-like
same-repository suppression, and provider-visible trust aliasing. This section supersedes
those subjects above.

### Derived policy counters

`policy_payload_hash_bytes`, `policy_framing_hash_bytes`, and
`policy_total_hash_bytes` are informational derived counters, not independent gates.
Payload safety is enforced by the per-file, per-source, and all-source byte limits;
framing safety is enforced by file-count and path-byte limits; total is their checked sum.
There is no claim that a structurally valid fixture can exceed only one derived counter.

Exact structural tests reach all payload and manifest maxima. Instrumentation damage
controls inject an `observed - 1` test-only limit for each derived counter while leaving
the same valid transcript unchanged; each refusal proves the counter is charged before
hashing, but it is recorded as an observed-red gate mutation rather than a production
limit-plus-one fixture.

### Ordinary historical-range preflight

Any non-empty `--range`, including `root:N`, receives a read-only historical preflight
before the global snapshot cache, ordinary Findings, output, or writer. One streamed
`rev-list --parents --topo-order --reverse` child supplies a shared immutable revision and
parent map for `queue_revision_edges`, task admission, handover history, and every other
ordinary parent consumer. No consumer buffers another whole revision list or launches a
per-commit parent query.

Queue-edge comparisons use bounded committed-object/tree readers and a shared typed delta
map rather than one unbounded diff subprocess per commit. The historical preflight has
these numeric aggregate limits:

| Ordinary historical dimension | Limit |
|---|---:|
| Revisions | 4,096 |
| Parent edges/tokens | 8,192 |
| Rev-list stdout / peak line | 16 MiB / 1 MiB |
| Rev-list stream chunks | 65,536 |
| Historical edge deltas | 8,192 |
| Delta records | 262,144 |
| Delta path bytes | 8 MiB |
| Delta payload bytes / peak payload | 32 MiB / 4 MiB |
| Historical object reads / cache hits | 65,536 / 262,144 |
| Historical object-header bytes | 4 MiB |
| Historical object payload bytes / peak | 32 MiB / 4 MiB |
| Historical tree entries / name bytes | 131,072 / 8 MiB |
| Historical Git children | 32 |
| Historical Git stderr | 256 KiB |
| Per-child / aggregate deadline | 30 s / 120 s |

Every dimension is pre-charged, streaming, terminated/reaped on refusal, and exact/+1
tested. Range preflight incomplete is exit 2 with zero ordinary Findings/writers and
byte-identical state. When combined with continuity, continuity completes first, ordinary
range preflight completes second, and only then can the global snapshot or writer phase
begin. The separate ordinary workflow invocation has the same range preflight.

This bounds the historical work newly exercised by creation `root:N`; it does not claim a
fixed upper bound for every current-worktree file scan in the whole reconciler. A history
beyond the configured limit is ordinary coverage-unavailable rather than a clean result or
an exhausted runner. Existing ordinary semantics and Finding identities remain unchanged.

### Source-distinct provider names and trust

Provider-visible names are distinct by source:

- `agentfold-continuity-edge/advisory-push`
- `agentfold-ordinary-range/advisory-push`
- `agentfold-continuity-edge/trusted-prt`
- `agentfold-ordinary-range/unprivileged-pr`

Candidate N can control only the two advisory-push names and the unprivileged PR code. It
cannot emit a trusted-prt record through the default-branch workflow. Even the trusted
name and conclusion are not sufficient authentication: the trusted evidence binding also
requires event `pull_request_target`, exact base repository ID, expected default-branch
workflow path/ref, immutable workflow/evaluator SHA, run_id, run_attempt, candidate head
repository ID, and O/N. Ordinary branch-protection status contexts cannot authenticate
that complete binding, so this task defines no trusted required-check gate.

Creation ordinary output is explicitly candidate-controlled advisory `root:N`. A missing,
tampered, or suppressed creation workflow is no-observation; local prepublication remains
the authoritative diagnosis.

### SHA-like heads in both repository shapes

SHA-like head-name suppression applies to `pull_request_target` for both same-repository
and fork PRs. An open same-repository SHA-like head therefore has trusted continuity
no-observation; candidate-controlled push advice may exist, and unprivileged ordinary PR
coverage exists only if its event actually runs. The fork row has the same trusted
no-observation without a base push. Negative live canaries cover both repository shapes and
never translate the missing trusted tuple into success.

### Gate boundary

The complete five-lens immutable review remains unopened for implementation until a new
revision accepts the ordinary historical preflight, source-distinct trust binding, and all
prior semantic/transaction contracts. Adapter evidence remains optional and separately
gated by live provider behavior.

## 2026-09-01 correction amendment 8 — role-specific ordinary projections

The review of `d075666935d1e9cabf28cc40321584137f0b1828` blocked an
over-generalized ordinary history map, hidden activation/root/result work, fork approval
states, and Git publication configuration leakage. This section supersedes ordinary
preflight structure/counters and the affected provider/manual details above. The accepted
continuity classifier is unchanged.

### Closed ordinary history snapshot

The ordinary preflight produces one immutable `OrdinaryHistorySnapshot` with distinct
named projections; consumers cannot iterate an untyped union.

For `root:N`, one streamed command supplies candidate history:

```sh
git --no-replace-objects rev-list \
  --parents --topo-order --reverse N
```

Every record has roles `candidate`, `task-message`, and `root-range`. For `B...N`, preflight
first requires exactly one `C = merge-base --all B N`, then streams these literal views:

```sh
git --no-replace-objects rev-list \
  --parents --topo-order --reverse C..N
git --no-replace-objects rev-list \
  --left-right --parents --topo-order --reverse B...N
```

The first view owns queue `C..N` edges and task-message `B..N` membership. The second owns
base-only/candidate-only side markers and final-tree symmetric-diff consumers. Records are
deduplicated by OID while retaining every role and raw parent OID. A base-only commit can
never enter candidate or task-message projections.

When checked HEAD is a validated exact two-parent synthetic candidate `H != N`, its one raw
record and real parent edges are appended with only `synthetic-candidate` and the exact
current consumer roles that already govern H; H is never relabeled as N or inserted into
task-message `B..N`. Direct checkout has no synthetic row. Zero or multiple merge bases,
side-marker ambiguity, truncated/malformed records, or an unvalidated H is incomplete.

The projections preserve these separate semantics:

- queue and task admission edges: candidate `C..N` plus the validated synthetic candidate;
- commit task tokens/messages: candidate-only `B..N`;
- final-tree/new-handover discovery: exact side-marked `B...N` diff and N tree;
- root task admission: separately discovered repository roots;
- schema governance: separately recorded activation history and ancestry state;
- handover incarnation: separately recorded path history with Git's existing full-history,
  no-rename, ordering, and diff-filter semantics.

Parity damage cases cover base-only deletion/token, candidate-only deletion/token, a
pre-C handover incarnation, merged outside lineage, multiple merge bases, and synthetic H
mutation. Removing a role or feeding an untyped union to a consumer is observed red.

### Reachable graph accounting

With 64-byte object IDs, 4,096 revision tokens and 8,192 parent tokens imply exact derived
maxima of 798,720 stdout bytes and 532,545 peak line bytes. Rev-list stdout, line bytes,
stream chunks, and historical edge-delta count are derived informational counters, not
independent exact/+1 gates. Structural revision/parent limits and fixed 64 KiB reads own
their production refusal; injected observed-minus-one damage tests prove derived
accounting. Malformed raw lines still refuse under grammar before retention.

### Root, activation, and handover inputs

Root discovery is its own bounded child:

```sh
git --no-replace-objects rev-list --max-parents=0 N
```

It admits at most 64 full-OID rows, 4,160 stdout bytes, and a 65-byte peak line. The child
has the common 30-second deadline, 512 MiB address-space limit, process-group cleanup, and
256 KiB stderr cap; exact/+1 output and stalled/OOM controls apply. Root discovery does not
charge its internal full-history traversal as range revisions, so a mature repository with
a small change is not rejected merely for age. Resource-limit or timeout is incomplete.

Schema activation requests come from one closed registry of current `(head, path, field,
version)` consumers. Each preserves the existing literal path-history command shape:
`git log --full-history --reverse --format=%H <head> -- <path>`. The snapshot caps 64
registered requests, 8,192 activation rows, 1 MiB stdout, 65-byte lines, 8 MiB referenced
policy blobs, and 64 children. Activation-versus-revision governance uses the bounded object
parent reader and a memoized ancestry-state graph, not thousands of merge-base children:
262,144 ancestry nodes/transitions, 32 MiB object payload, and the common deadline.

Handover path-history requests are admitted only for bounded paths discovered by the range
delta: 2,048 paths, 65,536 history rows, 8 MiB stdout, 8 MiB path bytes, and 512 children.
Each request retains its current literal options (`--full-history` where the current
consumer uses it, `--no-renames`, `--reverse`, and `--diff-filter=A`), its exact scope
(`N`, `B...N`, or current-incarnation head), and ordered result. Aggregate deadline,
address-space, stdout, stderr, process-group, and object budgets apply. Unsupported or
over-limit path history is incomplete, never simplified to a different Git history.

All ordinary Git children now share a 1,024-process aggregate maximum, 512 MiB per-child
address-space limit, 30-second per-child deadline, 120-second aggregate deadline, and the
previous byte/record caps. Successful as well as failed paths close and reap long-lived
object readers.

### Immutable ordinary result transaction

After history preflight and global snapshot capture, all registered ordinary checkers run
into a transaction-local immutable result before output or writers. The result caps are:

| Ordinary result dimension | Limit |
|---|---:|
| Checker invocations | 64 |
| Helper calls | 262,144 |
| Finding rows | 65,536 |
| Result rows / references | 131,072 / 262,144 |
| Retained result bytes / peak row | 16 MiB / 64 KiB |
| Serialized bytes / peak chunk | 16 MiB / 1 MiB |
| Diagnostic bytes | 256 KiB |

Finding identity, aggregation, severity, and ordering remain unchanged. Every row,
reference, helper, retained byte, and serialization chunk is pre-charged. Any later helper,
checker, result, serialization, deadline, or object failure discards all ordinary Findings,
closes readers, emits one bounded exit-2 diagnostic, and leaves every writer byte
unchanged. Only a complete result is printed and then supplied to retry/index/fold writers.
Exact/+1 and writer-matrix tests include a maximum delta map producing maximum Findings and
a later failing checker, proving zero partial stdout and byte-identical state.

### Approval-pending fork observations

Fork `pull_request` ordinary runs may remain queued, waiting, `action_required`, or approval
required. Those states are pending no-observation, not completed unavailable, failure, or
success. The bounded canary window may later bind one approved completed `(run_id,
run_attempt)`; pending and completed attempt artifacts are never combined. When the window
expires without a completed approved attempt, ordinary coverage remains externally
unavailable. The mergeable-fork matrix row is conditional on approval and completion.

### Configuration-closed publication

Create, update, repair, and deletion commands add `--no-follow-tags` and
`--recurse-submodules=no`. Immediately before publication, the workflow verifies exactly
one expected push URL from `git remote get-url --push --all origin`, `remote.origin.mirror`
is false, and no applicable `url.*.insteadOf` or `url.*.pushInsteadOf` rule can rewrite it.
Any duplicate pushurl, unexpected URL, mirror, or rewrite rule stops before push.

The exact update/repair command is:

```sh
git push --no-follow-tags --recurse-submodules=no \
  --force-with-lease=refs/heads/<branch>:<O> \
  origin <N>:refs/heads/<branch>
```

Creation uses the same flags with the empty expected-value lease; deletion uses the same
flags with the exact expected-tip lease and empty source. Explicit refspecs continue to
override `push.default` and `remote.*.push`. Hostile tests cover annotated reachable tags,
push.followTags, recurse-submodules, multiple pushurls, mirror, URL rewrites, upstream, and
multi-ref remote push configuration; only one validated repository/ref may move.

### Gate boundary

A fresh full five-lens immutable review remains the implementation gate. The ordinary
snapshot and result transaction are now part of core scope because they replace existing
unbounded production history used by Strategy A composition. Optional provider work still
waits on transport/canary evidence.

## 2026-09-01 correction amendment 9 — complete handover scope and reachable budgets

The review of `6ea2d284a882daebae6f043ba4762bbd80b3b6ea` found that the
ordinary preflight omitted unchanged live handovers, undercounted side markers, promised
two unreachable byte boundaries, admitted more path requests than its child budget, left
the retained snapshot unbounded, and allowed tracked hooks to compose an otherwise exact
push. This section supersedes the affected handover-input, reachable-graph-accounting,
ordinary-snapshot-budget, publication-command, and parity-test clauses above. The accepted
continuity classifier and provider observation model are unchanged.

### Candidate-complete handover request set

Handover history is admitted from the exact bound ordinary candidate, not merely from its
range delta. The candidate is `N` for a direct checkout and the already validated exact
two-parent synthetic candidate `H` otherwise. Before launching any path-history child,
preflight streams this literal candidate-tree query:

```sh
git --no-replace-objects ls-tree -rz --full-tree <candidate> -- \
  ':(glob)history/conversations/*/handover.md'
```

Only regular `100644` or `100755` rows with the exact four-component governed handover
grammar are retained. A malformed row, duplicate path with conflicting identity, symlink,
submodule, or path outside that grammar is not silently promoted to a live handover. The
tree stream is capped at 512 raw rows, 8 MiB total bytes, 8 MiB path bytes, and a 4 MiB
peak row before a path is retained.

The closed handover request registry is the deduplicated union of:

1. every regular governed live handover in that candidate tree, including one inherited
   unchanged from `B` or from a synthetic candidate's first parent;
2. every handover path in candidate admission/mutation edge deltas, including a record
   added and deleted before the final tree; and
3. every deleted, restored, or same-path re-created incarnation needed by the existing
   prior-incarnation checks.

The registry key is `(path, literal command shape, exact scope/head)` rather than just the
path. It admits at most 256 unique paths and 512 unique request keys. Every key maps to one
existing literal Git history command and one child; no consumer may issue an unregistered
query or reinterpret another key's result. The 512 handover-child limit therefore is
reachable and cannot be exceeded even when one path needs multiple command shapes. An
over-limit union is ordinary incomplete before any history child, checker, output, or
writer begins.

This preserves current semantics for an unchanged live v1 handover: its candidate bytes
are still compared with its current incarnation's add snapshot even when the only
`B...N` delta is unrelated. Direct and synthetic parity fixtures cover both a valid
unchanged live handover and a handover mutated before `B` followed by an unrelated
candidate commit. Removing the live-candidate member from the union makes the latter
fixture falsely clean and is an observed-red damage control.

### Raw stream accounting and reachable byte observations

The 4,096 revision-token and 8,192 parent-token limits count raw emitted records and raw
parent OID fields across both ordinary rev-list streams before OID deduplication. Retained
unique revisions, parent edges, side markers, and consumer-role references are separate
snapshot charges. Every `--left-right` record's leading `<` or `>` is retained and charged.

Under the raw structural limits, rev-list stdout has derived maxima of 802,816 bytes in
aggregate and 532,546 bytes for one side-marked octopus line, including delimiters and
newline. These are derived observations, not separately configurable gates: structural
token limits own refusal, and observed-minus-one byte observers prove that marker or
delimiter undercounting is detected. Tests include a side-marked octopus record and
overlapping `C..N`/`B...N` streams; a token emitted twice is charged twice before retained
deduplication.

Activation and handover-history stdout bytes are likewise derived from their hash-only
grammars. Their maxima are 532,480 bytes for 8,192 activation rows and 4,259,840 bytes for
65,536 handover rows, including one newline per 64-byte OID. The former 1 MiB and 8 MiB
independent exact/+1 promises are withdrawn. Row grammar and row count own production
refusal; observed-minus-one byte injections prove complete accounting, while malformed,
partial, overlong, or non-hex rows refuse independently.

### Aggregate retained snapshot transaction

`OrdinaryHistorySnapshot` is one compact, transaction-local arena. It uses integer indices
and immutable byte slices rather than a graph of recursively owned Python objects. Before
retaining anything it charges all revision rows, root rows, tree rows, delta rows,
activation rows, handover rows, ancestry states/transitions, request keys, parent edges,
role memberships, cache references, raw payload bytes, index bytes, and fixed record
framing. The closed aggregate caps are:

| Snapshot dimension | Limit |
|---|---:|
| Retained rows | 524,288 |
| Retained references | 1,048,576 |
| Arena bytes, including indices and framing | 64 MiB |
| Peak admitted record | 4 MiB |

These aggregate gates are independent and lower than the sum of compatible family
maxima. Test-only deterministic stream fixtures reach each aggregate limit while every
family remains below its own limit, then add exactly one row, reference, byte, or
peak-record byte. The exact case completes; each +1 case exits 2 with zero ordinary
Findings/output/writers, closes every reader, kills and reaps every child process group,
and releases the arena. A `tracemalloc` regression ceiling records implementation overhead
for the maximum supported fixture; it supplements rather than replaces logical charging.

All prior per-family counters continue to apply, except that the handover path/request
limits above replace 2,048 paths and make the 512-child ceiling structurally reachable.
The 1,024 aggregate ordinary-child limit counts root, activation, handover, rev-list,
delta, object-reader, and any other registered ordinary child across successful and failed
paths.

### Hook-closed exact publication

Every create, update, repair, and deletion push disables repository and global hooks in
the trusted invocation itself. The exact update/repair command is now:

```sh
git -c core.hooksPath=/dev/null \
  -c push.followTags=false \
  -c push.recurseSubmodules=no \
  push --no-follow-tags --recurse-submodules=no \
  --force-with-lease=refs/heads/<branch>:<O> \
  origin <N>:refs/heads/<branch>
```

Creation and deletion use the same trusted `-c` overrides and flags with their previously
specified empty expected value or empty source. The procedure verifies after applying
those overrides that `core.hooksPath` resolves exactly to the operating-system null device
at /dev/null; it does not execute
an alias, wrapper, or candidate-provided publication script. A hostile tracked executable
pre-push hook fixture under the tracked hook directory attempts to move a second ref and
write a sentinel;
neither effect may occur, and only the exact leased destination ref may change. Existing
URL, mirror, rewrite, tag, submodule, refspec, and lease hostile tests remain mandatory.

### Gate boundary

Production remains unopened. A fresh five-lens review must accept one immutable revision
containing this correction and every earlier superseding amendment. Optional GitHub
adapter implementation still requires bounded transport and live canary evidence; a core
implementation cannot infer adapter success from the design review.

## 2026-09-01 correction amendment 10 — executable enumeration and closed readers

The review of `aa872dfb6b27b864b2e9b12f9a542c834c86efb7` reproduced an
unsupported `ls-tree` pathspec, found another unreachable paired byte cap, and showed that
older continuity and merge-base counters still made impossible exact/+1 promises. It also
found that successful long-lived readers were not required to close before ordinary work.
This section supersedes amendment 9's candidate-tree command and tree byte accounting,
and every earlier continuity graph, merge-base, shallow-probe, chunk, or reader-lifecycle
counter that conflicts with it. Classification semantics are unchanged.

### Literal supported candidate-tree enumeration

Git 2.55.0 rejects `:(glob)` pathspec magic in `ls-tree`; the rejected command is not a
production option. The only candidate-tree command is the supported prefix enumeration:

```sh
git --no-replace-objects ls-tree -rz --full-tree <candidate> -- \
  history/conversations
```

The streaming parser counts every raw prefix row, including irrelevant files, before it
applies the exact four-component conversation/handover grammar and regular-mode filter.
The literal command is exercised against a real repository in direct-N and synthetic-H
tests; substituting either the rejected pathspec-magic form or a plain wildcard is an
observed-red control.

The primary tree-stream gates are 512 raw rows, 8 MiB raw stdout, and a 4 MiB peak raw
row. There is no independent 8 MiB path-byte gate: valid path bytes are a derived portion
of raw stdout after mode/type/OID/tab/NUL framing, then are charged again as actual retained
arena bytes. Observed-minus-one instrumentation covers path-byte accounting. Malformed or
overlong framing refuses under the raw byte/row/peak gates before parsing or retention.
The 256 admitted-path and 512 request-key limits remain independent and reachable because
irrelevant raw rows do not enter either registry.

### Structurally owned continuity observations

The continuity graph's 4,096 raw commit records and 8,192 raw parent OID fields are primary
structural gates across the one intrinsic graph stream. With 64-byte full OIDs and no side
marker, 798,720 aggregate stdout bytes and 532,545 peak line bytes are derived maxima,
including spaces and newlines. The former 16 MiB aggregate and 1 MiB line gates are
withdrawn. A fixed 64 KiB parser buffer owns peak input allocation; line assembly remains
charged to the derived line maximum. Raw bytes and delimiters are observed, and an
observed-minus-one control proves the byte accounting rather than pretending a larger
independent exact boundary exists.

The unique merge-base child needs at most two valid rows: one row supplies `C`, and a
second proves non-uniqueness and immediately makes continuity incomplete. Its primary
limits are two 64-byte OID tokens and two rows; its derived stdout/peak-line maxima are
130/65 bytes. Malformed, partial, non-hex, or overlong rows refuse before OID use. Output
after the second row is neither buffered nor interpreted: the process group is terminated
and reaped because the result is already non-unique. The former 64-row, 64 KiB, and 4 KiB
limits are withdrawn.

The shallow-repository probe is the literal
`git --no-replace-objects rev-parse --is-shallow-repository`. It admits exactly one ASCII
`true` or `false` token and one line; six stdout bytes and six peak-line bytes are derived
maxima. Any other token, second line, partial line, timeout, or nonzero exit is incomplete.
The former two-row, 64-byte, and 16-byte independent limits are withdrawn.

Input chunk calls are an implementation mechanism rather than adversarial Git records.
The parser uses one fixed 64 KiB buffer and never retains whole graph stdout. Logical graph
budgets charge decoded raw rows/tokens/bytes, not scheduler-dependent pipe fragmentation;
the earlier 65,536-chunk and 1 MiB-peak-chunk exact/+1 promise is withdrawn. Short-read,
single-byte-read, and delimiter-split test streams must produce byte-identical results and
counters under the same deadline, proving that OS chunking cannot change admission.

### Success-path reader finalization

Every one-shot and long-lived child opened by policy extraction, continuity, or ordinary
preflight is transaction-owned. Before any successful continuity result is returned to the
integrated caller, and on every exception or refusal path, the owner:

1. closes the request/stdin side;
2. drains only already budget-admitted stdout and stderr through the same bounded readers;
3. waits under the remaining monotonic child and aggregate deadlines; and
4. on timeout, unexpected extra output, nonzero exit, or open descendant, terminates the
   entire process group and reaps it before returning incomplete.

No `cat-file --batch`, graph, merge-base, shallow-probe, policy, or historical-evaluator
process survives a successful continuity preflight or crosses into ordinary snapshot
construction. Success, semantic-invalid, budget refusal, EOF, malformed output, injected
exception, and timeout tests assert closed descriptors, no live PID/process group, empty
transaction-local caches after refusal, and byte-identical writer state.

### Gate boundary

Production remains unopened. The next review begins from a new immutable revision and
must cover all five independent lenses; passing POC evidence cannot waive an executable
command or resource-lifecycle defect.

## 2026-09-01 correction amendment 11 — pre-output memory and literal transport

The review of `6643bdc0c68282420b9778badfd425d68810a900` accepted semantic
and executable-command parity, then found two pre-observation escape paths: a continuity
Git child can allocate while traversing before it emits a budgeted row, and a named remote
can select a candidate-controlled transport helper after its URL passes validation. This
section supersedes every earlier child-resource and publication operand/configuration
clause that conflicts with it. The O/N classifier, ordinary projections, and provider
observation states are unchanged.

### Pre-exec memory boundary for every Git child

Every Git process started for authority-policy extraction, endpoint/object validation,
shallow probing, merge-base discovery, intrinsic continuity enumeration, object/tree batch
reading, historical evaluation, or ordinary preflight receives a 512 MiB address-space
ceiling in the child between fork and exec. The ceiling is installed before Git parses the
repository or traverses one object; failure to install it is incomplete and the command is
not launched. Process-group, descriptor, stdout/stderr, record, per-exchange, per-child,
and aggregate deadlines remain cumulative defenses rather than substitutes.

This closes work performed before first output: `merge-base` may walk the reachable graph
before printing `C`, and `rev-list --topo-order --reverse --ancestry-path` may retain
topological state before the parent sees a row. A disposable wide/deep repository and a
fault-injected child allocator exercise each one-shot and batch command family at the
ceiling and over it. At the ceiling, a supported fixture completes. On allocation/resource
failure or an injected +1 byte, the parent observes a non-successful child, terminates and
reaps the process group, discards the whole local transaction, emits one bounded incomplete
diagnostic, and leaves stdout Findings and every writer byte empty/unchanged. The tests
also assert no policy or continuity child survives into ordinary work.

The supported execution baseline is macOS and Linux, where the installer verifies an
enforceable address-space resource limit before enabling Strategy A. A platform that cannot
install and demonstrate an equivalent pre-exec ceiling reports the classifier unavailable;
it does not silently rely on timeout or logical output counters.

### Literal-URL, transport-closed publication

The publisher never passes the remote name to `git push`. It first reads exactly one push
URL for `origin`, validates the expected GitHub HTTPS repository identity and the existing
no-rewrite/no-mirror constraints, and stores that exact byte string as `<validated-url>`.
It rejects any present `remote.origin.vcs`, `remote.origin.receivepack`, or additional
push URL before launch. Creation, update, repair, and deletion then use the literal URL and
an explicit receive-pack name:

```sh
git -c core.hooksPath=/dev/null \
  -c push.followTags=false \
  -c push.recurseSubmodules=no \
  push --receive-pack=git-receive-pack \
  --no-follow-tags --recurse-submodules=no \
  --force-with-lease=refs/heads/<branch>:<O> \
  <validated-url> <N>:refs/heads/<branch>
```

Creation and deletion preserve the previously specified empty expected value or empty
source. Because the operand is a URL rather than `origin`, Git cannot consult
`remote.origin.vcs`, `remote.origin.receivepack`, or remote-specific push/refspec behavior
to choose the transport or destination. The existing URL-rewrite rejection prevents a
validated literal from being remapped after validation. The trusted launcher supplies a
sanitized Git configuration environment: it ignores system/global configuration for the
push subprocess, removes inherited `GIT_CONFIG_*` injection variables, supplies only the
three shown `-c` values, and uses a prevalidated Git executable and exec-path outside the
candidate repository. Authentication is supplied as a separately prevalidated ephemeral
credential/askpass capability outside the repository; candidate or repository-local
credential helpers are never imported, and absence of that capability stops before
publication. Failure to construct the environment stops before publication.

A hostile transport fixture installs an observable `git-remote-evil`, sets
`remote.origin.vcs=evil` and `remote.origin.receivepack` to a sentinel command, and leaves
the visible push URL correct. The publisher must refuse before either sentinel runs. A
second test proves the literal-URL command ignores those remote fields even under a
controlled dry-run transport. Existing malicious hook, URL rewrite, follow-tag, submodule,
mirror, multiple-pushurl, lease-race, and extra-ref tests remain required; only the exact
leased destination may move.

### Gate boundary

Production remains unopened. A fresh five-lens immutable review must accept this complete
superseding design before implementation ownership is added to the orchestration run.

## 2026-09-01 correction amendment 12 — enforceable platform and sealed publisher

The review of `8ef4cf2b5bf7c99376edb9232315905cb5201e19` proved that the
chosen address-space limit cannot be lowered on the current macOS launcher and that a
literal URL still reads credential and HTTP policy from the original repository's local
Git configuration. This section supersedes amendment 11's platform, memory-test, and
publisher-configuration clauses. It deliberately narrows availability instead of claiming
an unenforceable safety property.

### Linux-enforced classifier memory

The production Strategy A classifier is available only on a Linux execution host where a
startup probe installs and reads back an exact 512 MiB `RLIMIT_AS` for a disposable child,
then demonstrates that the child cannot map beyond it. The pre-exec limit applies to every
policy, continuity, historical, and ordinary Git child as amendment 11 requires. If the
probe, limit installation, readback, or allocation control fails, the classifier returns
coverage-unavailable before opening repository history.

Native macOS is not an execution baseline for this classifier. The current macOS launcher
cannot lower `RLIMIT_AS` to the specified ceiling, and its data/address-space limits were
not demonstrated to constrain allocation. A macOS developer uses a separately isolated
Linux runner/container or the trusted Linux CI lane for continuity classification; absent
that adapter, local paired diagnosis returns exit 2 and ordinary checks remain separately
available. POC replay and pure unit tests may still run on macOS, but cannot claim the
production resource gate passed.

OS memory enforcement is page-granular and includes runtime mappings, so there is no
`+1 byte` address-space admission claim. Tests separate:

1. exact installation/readback of the numeric 512 MiB limit before exec;
2. a bounded supported Git traversal below the ceiling;
3. a small allocation helper that maps whole pages until the next page is refused without
   ever exceeding the configured address space;
4. child behavior at resource failure and failed limit installation; and
5. bounded diagnostics, zero Findings/writers, descriptor closure, and full process-group
   termination/reaping in every failure case.

All logical row, token, payload, arena, result, and serialization budgets retain their
exact/+1 gates. The OS ceiling is a separate coarse containment boundary, not another
logical byte counter.

### Sealed Git directory for publication

The trusted publisher never runs `git push` with the candidate worktree or common Git
directory as `GIT_DIR`. After validating the source repository identity, object format,
exact O/N objects, destination repository/ref, and literal HTTPS URL, it creates a
random-capability, mode-0700 temporary bare Git directory outside the candidate tree. The
temporary repository has the same object format, no refs, remotes, hooks, includes,
credential helpers, or HTTP configuration. Its empty writable object directory reads the
prevalidated source object directory only through an exact read-only alternate binding;
the publisher verifies O and N again through this sealed object view before push. It then
uses the literal URL, full O/N OIDs, exact lease, and explicit receive-pack contract from
amendment 11.

The launcher constructs the subprocess environment from an allowlist rather than deleting
named variables from the ambient environment. It supplies only the sealed `GIT_DIR`, the
read-only object alternate, trusted absolute Git executable and exec path, fixed locale,
terminal-prompt disablement, system/global-config disablement, and a one-use authenticated
askpass capability carried outside the repository. Candidate `HOME`, XDG, `GIT_CONFIG_*`,
`GIT_DIR`, worktree/index/namespace, object-replacement, alternate-object, SSH, credential,
proxy, curl, certificate, TLS-disable, trace, pager, editor, and prompt variables are not
inherited. The sealed local config is hashed before launch and checked again after the
process exits; unexpected mutation makes the publication result invalid and the temporary
repository is preserved for bounded forensic inspection.

Authentication canaries use that exact sealed launcher for create, exact-lease update,
lease rejection, repair, and exact-lease deletion. Hostile tests put executable
`credential.helper`, extra-header, proxy, CA/certificate, SSL-disable, include, remote-vcs,
receive-pack, hook, and alternate-object settings in the original local config and ambient
environment. Each writes a distinct sentinel if observed; none may run or affect the sealed
child. The canary also proves the ephemeral askpass capability is invoked exactly for the
validated GitHub host, cannot be read by a candidate helper, and is destroyed after one
attempt. Only the exact destination ref may move.

The sealed temporary repository is a runtime adapter boundary, not a new source of truth.
It owns no durable task, queue, verification, or credential state. Success removes it;
failure retains only bounded nonsensitive metadata and never writes secrets into the task
repository.

### Gate boundary

Production remains unopened. A fresh immutable five-lens panel must accept the Linux-only
resource boundary, sealed publisher, and all previous semantic contracts before any
production unit starts.

## 2026-09-01 correction amendment 13 — observer core, external publisher

The review of `56b73d57cd1564c510d6a331793b6b9f5aa4beed` proved that a
sealed publisher would need its own complete pack, network, alternate-object, credential,
cleanup, and uncertain-remote-outcome protocol. That is the scope already owned by backlog
task `2026-08-03-bind-task-branch-pushes-to-observed-tips`, not by this continuity
classifier. This section withdraws every earlier exact-push-command, configuration-closed
publication, hook-closed publication, sealed-publisher, publisher-canary, or only-one-ref-
moved implementation claim in this task. It also closes the macOS ordinary contradiction.

### Core and adapter do not publish

Strategy A is an observer over immutable Git object endpoints. Neither entrypoint, the
GitHub adapter, the ordinary-history transaction, nor any implementation unit in this task
invokes `git push`, chooses credentials, creates a remote helper, packs an object closure,
or changes a local or remote ref. No remote name, URL, credential, proxy, TLS policy,
askpass capability, alternate-object path, publisher temp directory, or publication result
enters the classifier result or authority policy.

The exact-lease commands recorded in rejected amendments are no longer part of this task's
contract or tests. They remain useful motivation for the separate publisher task, which
must independently solve multi-ref atomicity, hooks/config, pack and network budgets,
credentials, recursive alternates, crash cleanup, and unknown remote outcome before it can
claim prevention. This task neither weakens nor pre-accepts that future design.

GitHub canary setup may use an owner-operated fixture controller outside candidate code,
but the controller's publication mechanics are test infrastructure, not core behavior or
proof that AgentFold prevented a ref update. The observed event's immutable O/N pair is the
only continuity input after any external publication.

### Honest human development cycles

The common cycles have these observable effects:

1. On a Linux host that passes the resource startup probe, a developer may run the paired
   local O/N plus ordinary-range diagnosis before asking an external publisher to update a
   ref. A clean result diagnoses the proposed objects; it does not reserve or move the ref.
2. On native macOS, every production invocation with non-empty `--range`, `root:N`, or
   `--ref-update` returns coverage-unavailable exit 2 before historical work. The task makes
   no bounded-production claim for a legacy range path. Checks that require no protected
   historical child are outside Strategy A and may continue under their own existing
   contract, but cannot substitute for continuity or `OrdinaryHistorySnapshot`.
3. A macOS developer who lacks a separately verified Linux runner cannot perform the local
   Strategy A diagnosis. They may still publish with their external tool, but the first
   Strategy A result is the post-push Linux provider check; this is explicitly detection,
   not prevention.
4. Creation, fast-forward update, divergent update/restack, repair, and deletion are all
   externally published. Creation/deletion have the already specified zero-endpoint
   semantics; nonzero updates use the provider's exact event O/N. No current ref or PR API
   reconstructs a missed pair.
5. If the external publisher reports rejection or an unknown result, the developer stops,
   fetches the exact destination ref through that tool's trusted procedure, and compares it
   with the expected O/N. They never infer success from local output or retry unchanged N.
6. An invalid/ambiguous completed provider result is repaired into a new N and externally
   published as a new update. An unavailable result remains unavailable; a later clean edge
   does not launder it.

The UI or handover must therefore say separately: proposed objects diagnosed locally,
external publication requested, provider event observed, continuity complete/invalid/
unavailable, and merge eligibility. It must never collapse those stages into “AgentFold
pushed safely.”

### Publisher-free verification boundary

Core and adapter tests assert that no Strategy A process spawns `git push`, a credential
helper, remote helper, receive-pack client, or publisher cleanup process. Hostile local Git
configuration and transport environment cannot affect classification because no
publication command exists and committed-object readers use their already isolated
read-only object-source contracts.

Live GitHub canaries remain conditional external evidence for provider payload and fetch
behavior. Their fixture controller records only event/run artifacts; its own transport
success is not recorded as a Strategy A guarantee. A missing authorized fixture or
credential leaves adapter behavior unverified without blocking provider-independent core
implementation.

### Gate boundary

Production remains unopened. The next five-lens review judges the smaller observer-only
scope, Linux historical-execution boundary, and unchanged accepted O/N semantics. The
publisher backlog stays a separate task and future PR.

## 2026-09-01 correction amendment 14 — read-only transport is not publication

The review of `a79425b7de1234b390ed0c495b6ed774a6b32c51` accepted the O/N
semantics and observer/publisher boundary, then found that the negative wording also banned
the trusted adapter's required anonymous HTTPS fetch. This section supersedes only that
over-broad remote-helper prohibition. It does not reopen publication.

The provider-independent classifier library, integrated local CLI, and ordinary-history
transaction are network-free. They consume an already available bounded object source and
never run a remote helper.

The trusted GitHub adapter may perform the previously specified bounded, read-only
fetch/upload-pack transport into its isolated empty object directory. That transport may
execute the trusted installation's HTTPS remote helper, but only for the event-named public
GitHub repository and exact O/N object IDs, under the existing host/repository validation,
redirect, credential, transfer, disk, process, memory, deadline, and no-candidate-code
contracts. It never invokes push, receive-pack, a publication credential helper, or a
candidate-provided remote helper. A missing private-fork credential remains unavailable;
the adapter does not acquire one implicitly.

Negative tests therefore assert:

- no Strategy A component invokes `git push`, receive-pack, or any ref-mutation API;
- the library and local entrypoints perform no network or remote-helper operation;
- the trusted adapter accepts only its bounded fetch/upload-pack helper and rejects a
  helper path, URL, redirect, repository identity, or credential source outside its closed
  transport contract; and
- replacing the allowed fetch helper with a push/receive-pack/publication path is observed
  red.

Production remains unopened pending the full five-lens review of a new immutable revision.

## 2026-09-01 correction amendment 15 — separate CLI and atomic activation

The five-lens review of `b6966a34252184f6245d346ecf6904fa1cffcfc6`
accepted semantic, resource, workflow, and core-fit boundaries. The CLI lens then proved
that Linux-gating every ordinary range would break the macOS landing-set builder, that
parser and workflow migration could not land independently, that the standalone output was
not byte-defined, and that new authority modules would sit outside the Git-spawn guard.
This section supersedes every earlier integrated `reconcile.py --ref-update` interface,
every claim that existing ordinary range checking is replaced or Linux-only in this task,
and the affected parser/output/migration/test-ownership clauses. The Strategy A classifier
semantics are unchanged.

### Two separate commands, no combined mode

automation/reconcile/ref_update.py is the only Strategy A continuity CLI. It is read-only,
Linux-only, and accepts exactly one occurrence of each required option:

```text
--git-dir <absolute-path> --old <full-oid> --new <full-oid>
```

It rejects duplicate, missing, partial, zero, abbreviated, non-commit, or extra positional
values before opening the object source. A custom single-occurrence parser rejects repeated
`--git-dir`, `--old`, or `--new`; default last-value-wins `argparse` behavior is forbidden.
It rejects writer, range, worktree, index, branch, task, provider, compatibility, and
publication options. `--help` is the only option that may appear alone.

`automation/reconcile/reconcile.py` remains the ordinary repository/index/worktree CLI.
It does not gain `--ref-update`. Existing `--range B...N` and `root:N` behavior remains
cross-platform and continues serving `automation/integrate.py`; this task does not claim to
replace or resource-bound that legacy ordinary history implementation. The proposed
`OrdinaryHistorySnapshot` and immutable ordinary-result rewrite from amendments 6–10 are
withdrawn from this task and require a separate claimed task before implementation. Their
research remains useful evidence, not accepted production scope.

On Linux, a human or workflow runs continuity and ordinary checking as two processes with
two separately named results. On native macOS, ordinary range checking remains available
under its current contract, while `ref_update.py` emits Linux-unavailable exit 2 before
history. An ordinary clean result never substitutes for missing continuity.

### Canonical standalone bytes and exit mapping

Every complete continuity result is exactly one UTF-8 JSON line on stdout, encoded with
sorted keys, ASCII escaping, separators `,` and `:`, no insignificant whitespace, and one
final LF. Stderr is empty. The top-level object has exactly these keys:

```text
schema, old, new, common, state, rows, counters
```

`schema` is `agentfold-ref-update/v1`; `state` is `clean` or `blocked`; endpoint/common
values are lowercase full OIDs. Rows are canonically sorted by full identity digest and
have exactly:

```text
identity, paths, status, reasons, finding, evidence
```

Paths and closed typed reason codes are sorted unique ASCII/UTF-8 strings. Status is one of
`valid`, `none`, `invalid`, or `ambiguous`. `finding` is null only for a valid row; every
`none`, `invalid`, or `ambiguous` row contains the exact integrated-compatible projection:

```text
check   = queue-resolution
subject = lexicographically first representative path at O
message = divergent ref update has no unique valid continuity proof for old action <full-identity>: <comma-joined-reason-codes>
fix     = restore the old action or create one complete evidence-valid resolution in a new ref update; preserve every required commit, tree, and blob
```

`none` includes closed reason `no-resolution-root`, so the reason list is never empty for a
finding. Evidence and counters use only the closed bounded fields already defined by the
classifier; no raw action text, localized Git stderr, provider state, or moving ref enters
the result. `state=clean` requires every row valid (or no affected rows) and exits 0.
`state=blocked` requires at least one non-valid row and exits 1.

Any syntax, platform, policy, object, graph, budget, deadline, child, or serialization
incompleteness emits no stdout. It emits exactly one canonical ASCII JSON line to stderr
with keys `schema`, `state`, and `reason`, where state is `incomplete` and reason is one
closed code; then exits 2. Raw stderr is drained under budget but never copied. Help is
fixed UTF-8 text on stdout and exit 0. Golden-byte tests cover every state, locale, time
zone, hash seed, duplicate option, unknown option, and stdout/stderr/exit combination.

### Additive implementation, then one atomic activation

The migration has three gates:

1. **Dormant additive core:** add the provider-independent library, standalone CLI, source
   guard coverage, and tests. Do not change `reconcile.py`, the workflow, or current
   `--displaced-tip` behavior. This commit is safe to review and test but is not production
   activation.
2. **Adapter proof:** complete the bounded read-only transport POC and live same-repository,
   fork, conflicted, SHA-like, approval, stale, and retention canaries. Until this gate is
   green, the current adapter and continuity mechanism remain active and no completion is
   claimed.
3. **Atomic activation commit:** in one commit, update every workflow call site to invoke
   the new standalone continuity command plus the existing ordinary command; delete
   `--displaced-tip` from parser/help/globals/current continuity implementation; update
   workflow/source/CLI tests; and demonstrate the old option is rejected. No mergeable
   revision may contain a new parser with the old workflow, or a new workflow without the
   new proven classifier.

If the adapter proof cannot run, the branch may retain the dormant additive core in a draft
PR, but production behavior remains unchanged and the task stays incomplete. There is no
temporary compatibility bridge in the final activated revision.

### Recursive authority-module spawn guard

The source guard no longer enumerates only `reconcile.py`. It recursively discovers every
tracked Python file anywhere under `automation/reconcile/` and rejects any subprocess or OS
spawn whose literal argument shape it cannot inspect. Every Git object read must carry
`--no-replace-objects` in the hardened position; the closed bare-read allowlist remains
per-file and empty by default. Network and publication commands remain forbidden except the
separately scanned trusted adapter fetch lane.

Guard tests inject a new reconciliation module with each known bypass spelling, including
dynamic program names, tuples, concatenation, shell strings, import indirection, `Popen`,
`os.exec*`, and a bare Git read. Each must fail without adding the filename to a manual
registry. The real new library and CLI must be discovered, and at least the centralized Git
execution module must expose recognized hardened reads so an accidentally empty scan cannot
pass. Workflow shell commands retain their separate guard.

### Gate boundary

Production remains unopened. A fresh full five-lens review must accept this separated CLI,
canonical byte contract, recursive guard, and atomic activation plan. Only then may the
dormant additive core units start.

## 2026-09-01 correction amendment 16 — preserved rows and accepted delivery

Independent semantic and budget reviews rejected
`28d63c0e654bbadfd932f69908512c755c848987`. The semantic review found that amendment 15
turned the accepted POC's clean persisted-action result into a blocker and replaced stable
identity-based Finding keys with movable paths. The budget review proved that a process
cannot roll back a partially written 32 MiB stdout stream when its reader stalls past the
deadline. This section supersedes amendment 15's status/finding rules, Finding projection,
and zero-stdout-on-delivery-failure claim. The classifier, separated-command boundary, and
atomic activation sequence remain unchanged.

### Persisted is a first-class clean status

Every identity at `O` still has exactly one result row. The closed status set is now:

- `preserved`: the identity is live at `N` and its unique persisted occurrence has a
  complete valid `C`-rooted continuity proof;
- `valid`: the identity is absent at `N` and exactly one valid causal resolution root, with
  no competitor, explains that absence;
- `none`: the identity is absent at `N` and no causal root exists;
- `invalid`: at least one required proof is complete and invalid; or
- `ambiguous`: multiplicity, competing roots, or complete contradictory proofs prevent one
  conclusion.

The production port maps the POC's `status=none`, `finding=false`,
`reason_code=identity-preserved` tuple to `status=preserved`; the POC's disappeared
`status=none`, `finding=true`, `reason_code=no-resolution-root` remains `status=none`.
Golden oracle tests require that mapping explicitly, including `P8-path-timing-move`.
`finding` is null exactly for `preserved` and `valid`. It is present for `none`, `invalid`,
and `ambiguous`. `state=clean` requires every row to be `preserved` or `valid` (or no rows)
and exits 0; any other complete row makes `state=blocked` and exits 1.

Amendment 15's exact top-level key set is superseded by
`schema,policy,old,new,common,state,rows,counters`. `policy` is the lowercase
`sha256:<64-hex>` authority-policy digest already required to match O, N, and the executing
evaluator. It is present even when `rows` is empty, so a consumer can always bind the
accepted result to the immutable policy invocation.

The row keys remain exactly `identity,paths,status,reasons,finding,evidence`, but their
previously open scalar meanings are closed here. `identity` is the same lowercase
`sha256:<64-hex>` domain-separated identity digest used by the Finding, never the raw
identity tuple. `evidence` is a lowercase `sha256:<64-hex>` digest over the library's
complete canonical retained row evidence; the full bounded proof remains available to
in-process verification but raw action text and a recursively open proof schema do not
enter the CLI format. `counters` is an object containing every policy-bound counter-registry
name exactly once, with no unknown or omitted name; each value has exactly integer keys
`used` and `limit`, and `0 <= used <= limit`. Registry names and limits are part of the
authority-policy digest. These choices make every nested CLI type closed while retaining a
cryptographic binding to the complete proof exercised by tests.

### Finding identity never follows a path

The row's sorted `paths` remain bounded human context only. The exact Finding object has
keys `check`, `subject`, `message`, and `fix`, with this projection:

```text
check   = queue-resolution
subject = message-queue/action-identities/<domain-separated-identity-digest>
message = divergent ref update has no unique valid continuity proof for old action <identity-digest>: <comma-joined-reason-codes>
fix     = restore the old action or create one complete evidence-valid resolution in a new ref update; preserve every required commit, tree, and blob
```

The digest is the earlier collision-checked digest of the full authoritative identity;
neither a representative path nor raw action text enters the Finding key or message. A path
move therefore preserves retry identity, while digest collision remains incomplete exit 2.

### Complete bytes versus accepted bytes

Classification and serialization finish into one bounded immutable byte buffer before the
first stdout write. The 32 MiB result-serialization ceiling includes the final LF. The
writer uses the same absolute 120-second transaction deadline, makes stdout nonblocking
where the descriptor supports it, accounts every attempted byte, handles short writes, and
never retries beyond the remaining deadline. A successful delivery writes the entire one-
line canonical buffer, observes no write error, and then exits 0 or 1 according to state.

There is deliberately no claim that an operating system can retract bytes already accepted
by an output sink. Pre-delivery incompleteness emits zero stdout. A short write, `EPIPE`,
`ENOSPC`, closed descriptor, deadline, or other delivery failure may leave a prefix on
stdout, but exits 2; that prefix is transport debris, not a result. The command attempts the
canonical bounded incomplete diagnostic on stderr, but a failed stderr sink cannot be made
reliable and the exit remains 2. No partial stream is a Finding, retry, evidence record, or
provider conclusion.

Every authority-bearing caller must capture stdout and stderr without teeing or publishing,
drain both concurrently under their respective byte caps, wait for process termination, and
accept a continuity result only when all of these hold:

1. exit is exactly 0 or 1 and agrees with the decoded `state`;
2. stderr is empty and stdout reaches EOF within 32 MiB including LF;
3. stdout is exactly one LF-terminated JSON value with no prefix or suffix;
4. strict parsing, exact schema/key/type validation, and canonical re-encoding reproduce
   the captured bytes; and
5. schema, `old`, `new`, and policy identity match the immutable invocation.

Anything else is incomplete and must be discarded before logs, annotations, artifacts,
Findings, or ordinary-check composition. The GitHub adapter and local wrapper own this
capture protocol; a shell pipeline or `tee` is not an authority-bearing caller. Tests cover
slow readers, a reader that stops after 64 KiB, closed stdout/stderr, short writes, `EPIPE`,
`ENOSPC`, failure after a complete buffer but before exit, deadline during delivery, an
exit/state mismatch, a truncated final LF, over-cap output, noncanonical JSON, and a forged
endpoint. Each attack must produce no accepted result and no repository mutation.

### Gate boundary

Production remains unopened. A new immutable revision must receive the full five-lens
review; the prior two blocks are rejection evidence, not approvals transferable to this
amendment.

## 2026-09-01 correction amendment 17 — executable preflight and canary-bound callers

The five-lens review of `92a5f3e61fd3e03009813bf6e49a842e422bf25f`
accepted resource and core-fit boundaries but rejected semantic, CLI, and workflow
composition. It proved that fast-forward row requirements contradicted the accepted POC,
object type cannot be known before opening an object source, identity/evidence hash inputs
were not framed, live canaries were not bound to the adapter later activated, and the
authority-bearing local capture wrapper did not exist in the implementation contract. This
section supersedes the affected endpoint-preflight, fast-forward row, row schema/digest,
caller, adapter-proof, and activation clauses. Divergent Strategy A semantics and the
accepted-delivery rule remain unchanged.

### Syntax first, object type after a bounded open

The custom parser performs only facts knowable without an object read. It rejects duplicate,
missing, or unknown options; a non-absolute Git-directory path; O/N tokens that are not
lowercase ASCII hexadecimal of length 40 or 64; all-zero tokens; unequal token lengths; and
identical O/N. These failures occur before an object source is opened.

The next minimal read-only source stage discovers repository object format and requires the
token length to match it. One bounded hardened batch-check exchange then requires each exact
OID to exist and have object type `commit`; a blob, tree, tag, missing object, malformed
header, alternate/replacement view, or source error is incomplete exit 2. This stage
necessarily opens the isolated object database, but it completes before policy payload,
merge-base, graph, queue snapshot, or action provenance reads. Tests pair same-width commit,
blob, tree, and annotated-tag OIDs and prove that syntax alone does not guess their type.

### Fast-forward is the POC's empty-row transaction

The row/status/Finding rules in amendment 16 apply only when `O` is not an ancestor of `N`.
After endpoint and three-source policy verification, a same-policy fast-forward returns the
canonical complete clean result with `common=O`, `rows=[]`, and only preflight/policy
counters. It performs zero queue identity derivations, queue snapshots, graph enumeration,
or action provenance, matching POC scenario `W0-fast-forward-return`. A policy-changing
fast-forward remains incomplete exit 2. The separate ordinary O-to-N range owns every
fast-forward deletion or mutation and still runs independently in provider composition.

For divergent endpoints, every identity at O receives exactly one row and the `preserved`,
`valid`, `none`, `invalid`, and `ambiguous` rules remain as specified. Golden tests assert
both halves: W0 has empty rows and zero action work, while P8 maps the POC's clean persisted
`none` to production `preserved`.

### One exact identity transcript; no public proof-digest claim

The CLI row schema is now exactly `identity,paths,status,reasons,finding`; amendment 16's
`evidence` member is withdrawn. The CLI is a bounded conclusion projection, not a durable
independent copy of the complete internal proof. The in-process classifier still retains
and tests the full structured proof transaction before projection, but this task does not
claim that an opaque hash of an unspecified proof schema is externally auditable.

The stable identity digest has one exact transcript. Let `parts` be the complete string
tuple returned by `queue_action_identity`: four elements for an ordinary action or five for
a generated retry, including its existing kind discriminator. Every part must be a valid
Unicode scalar string obtained by the repository's strict UTF-8 parser; no Unicode
normalization, case folding, trimming, or path inclusion is added by the digest encoder.
Encode:

```text
ASCII("agentfold-queue-action-identity/v1") || 0x00
|| uint64be(len(parts))
|| for each part in tuple order:
     uint64be(len(UTF8(part))) || UTF8(part)
```

The displayed value is lowercase `sha256:` plus the 64-hex SHA-256 of exactly those bytes.
An independently implemented golden encoder covers empty fields, embedded NUL, non-ASCII,
combining characters, long text, the four- versus five-field variants, and every one-byte
length boundary. A digest collision between unequal full tuples is incomplete exit 2. Raw
identity text never enters CLI output, the Finding message, or the subject.

### Named authority-bearing capture entrypoint

automation/reconcile/ref_update.py remains the only classifier CLI. The human/provider
acceptance entrypoint is automation/reconcile/ref_update_capture.py with the same exact
single-occurrence grammar:

```text
--git-dir <absolute-path> --old <full-oid> --new <full-oid>
```

It invokes the sibling classifier by an immutable literal path and sanitized interpreter
environment, concurrently drains stdout/stderr under the specified caps, waits and reaps
under an outer deadline, applies every amendment-16 acceptance check, and only then re-emits
the exact accepted canonical bytes with the same 0/1 state exit. Child failure or invalid
bytes becomes wrapper exit 2 and no accepted result; wrapper output delivery follows the
same prefix-is-not-authority rule. It never runs Git, ordinary reconciliation, provider
logic, a writer, or a publication command.

The wrapper installs the same probed Linux address-space ceiling before capture. Classifier
and wrapper each have a 512 MiB per-process ceiling; their simultaneous closed maximum is
1 GiB, plus only kernel pipe capacity. The wrapper's outer deadline is 130 seconds: at most
120 seconds for the classifier transaction and at most 10 seconds for validation/final
delivery. It kills the fixed child process group on cap, deadline, or parse refusal, drains
bounded residual bytes, and reaps before exit. Exact/+1 tests cover both per-process memory
boundaries, the composed maximum, stdout/stderr caps, child cleanup, and final delivery.

This capture entrypoint is part of the authority-policy manifest and the dormant-core gate.
Both local Linux diagnosis and every provider adapter invoke it; no human must invent a
parser or shell pipeline. Documentation presents the capture command followed by the
existing separate ordinary range command. Native macOS receives the same explicit Linux-
unavailable exit 2 before child launch.

### Canary bytes must equal activated adapter bytes

The GitHub transport has a separate `adapter-policy/v1` digest; it is not classifier
authority. Its closed ordered manifest contains the production event/O/N extraction script,
the read-only object-transport script, the repository-local action metadata that invokes
ref_update_capture.py, and a canonical workflow invocation projection covering event names,
permissions, trust source, exact arguments, result mapping, and unavailable behavior. The
digest uses the authority-policy transcript's domain separation, UTF-8 path ordering, and
uint64 big-endian length framing. It also embeds the exact authority-policy digest expected
by the capture entrypoint.

The adapter proof runs the full live same-repository, fork, conflicted, SHA-like, approval,
stale, and retention matrix through those exact manifest blobs. Its immutable receipt names
the tested commit, adapter digest, authority-policy digest, fixture identity, workflow run
and attempt, every captured endpoint/result, and cleanup result. Gate 2 may land these bytes
dormant, but it may not activate or retire current continuity.

Before gate 3 is mergeable, a mechanical activation check requires:

1. every authority-policy and adapter-policy blob in the candidate tree is byte-identical
   to the canary receipt digests;
2. the actual workflow projection is byte-identical to the canaried canonical projection;
3. the adapter and capture entrypoint are unchanged from the tested commit; and
4. the receipt covers every required live row with no unavailable or stale substitution.

The atomic activation commit may change only the checked workflow call sites, retire the
legacy `--displaced-tip` parser/implementation, and update activation tests/records. It may
not change digest-covered classifier, capture, adapter, or invocation-contract bytes. Any
such change invalidates the receipt and returns to gate 2; a passed canary for adapter A can
never authorize adapter B. Static damage tests mutate each workflow permission, event,
argument, result mapping, digest-covered byte, and capture path and require activation
refusal before legacy protection is removed.

### Gate boundary

Production remains unopened. The full five-lens review must accept a new immutable revision
before dormant implementation units begin; approvals on the rejected revision do not carry.

## 2026-09-01 correction amendment 18 — direct evaluators and external receipt authority

Review of `2f43c7d024b046600ded34c2e0b93430ae29d0ba` accepted semantic
behavior but rejected workflow and CLI closure. The extra capture process could not contain
separately grouped Git grandchildren and omitted them from aggregate memory; adapter framing
and full workflow execution bytes remained open; fast-forward counters conflicted; the
activation allowlist omitted live documentation; and the activation candidate could replace
its own canary receipt. This section supersedes amendment 17's wrapper, composed-process,
adapter transcript/projection, receipt, and activation clauses plus the affected fast-forward
counter wording. Endpoint, identity, row, divergent, and accepted-delivery semantics remain.

### One evaluator process, no nested classifier

There is no ref_update_capture.py and no evaluator that spawns another evaluator.
automation/reconcile/ref_update.py is the sole local continuity CLI and calls
ref_update_core in process. It validates the complete immutable result object, serializes it,
strictly decodes and re-encodes that bounded buffer, checks schema/O/N/policy/state, and only
then begins amendment 16's bounded delivery. For a human, the documented authority result is
the exact canonical line plus the CLI's final 0/1 exit; exit 2 or a missing/truncated line is
incomplete. No shell parser, `tee`, or second Python process is required.

The GitHub adapter also imports the same ref_update_core entrypoint in its own evaluator
process. It validates the in-memory result and canonical bytes before provider projection;
it never launches ref_update.py. Golden parity runs the local CLI and adapter entrypoint over
the same immutable repositories and requires byte-identical result buffers before delivery.
Thus provider and local paths share classifier authority without a parent/classifier/Git
grandchild hierarchy.

The evaluator and every Git child each install the probed 512 MiB address-space ceiling.
The runtime permits at most two simultaneous direct Git children: one long-lived bounded
object batch reader and one one-shot graph/policy/historical child. A third live child is a
pre-spawn budget refusal. The evaluator is the direct parent of both, assigns each its own
killable group, and on every refusal terminates, drains, waits, and reaps both before exit.
The closed simultaneous address-space maximum is therefore 1,610,612,736 bytes (512 MiB
evaluator plus two 512 MiB Git children), plus the already capped two OS pipes per child;
provider transport completes and is reaped before classifier children start. Exact process-
registry and fault tests keep both allowed children live, refuse the third before spawn,
stall each child independently, and assert no process or descriptor survives.

### Fast-forward emits the complete zero-valued registry

Every complete result still emits every policy-bound counter-registry name exactly once.
For a same-policy fast-forward, only endpoint and policy counters may be nonzero; every graph,
snapshot, identity, action, evidence, and serialization-work counter not exercised by the
empty-row path is present with `used=0` and its normal `limit`. A byte-golden W0 result proves
the complete key set, zero action values, `common=O`, `rows=[]`, clean state, and exit 0.

### Exact adapter-policy transcript and complete workflow blobs

The adapter digest input is exactly:

```text
ASCII("agentfold-ref-update-adapter-policy/v1") || 0x00
|| raw_32_byte_authority_policy_sha256
|| uint16be(file_count)
|| for each manifest path in ascending UTF-8 byte order:
     uint16be(path_byte_length) || path_utf8
     || uint64be(payload_byte_length) || exact_payload_bytes
```

The domain is 39 bytes including NUL. The embedded authority value is the 32 decoded digest
bytes, not its `sha256:` spelling. The manifest has 1–16 unique normalized repository-
relative strict-UTF-8 paths, no empty/absolute/dot/dot-dot segment, at most 4,096 aggregate
path bytes, and at most 4 MiB aggregate payload. The exact framing maximum is
`39 + 32 + 2 + 16 * (2 + 8) + 4,096 = 4,329` bytes; the maximum total digest input is
4,198,633 bytes. The displayed digest is lowercase `sha256:` plus the 64-hex SHA-256.
Independent golden vectors cover one file, reordered files, empty payload, non-ASCII paths,
maximum framing/payload, each +1, and a one-byte authority digest change.

The manifest contains exact complete blobs, not an extracted workflow projection: the
provider event/O/N and read-only transport code, one reusable trusted Linux workflow, and
one full dedicated activation-workflow template. The template is the entire future workflow
file from first byte through final LF, including all triggers/action filters, permissions,
runner, action pins and checkout source, job/step conditions, dependencies, concurrency,
environment, shell, timeouts, failure handling, outputs, artifacts, and result publication.
The reusable workflow is likewise hashed in full. Gate 3 may only install a dedicated
workflow whose whole file is byte-identical to that template. There is no unprojected YAML
key or inherited caller setting. Any byte change invalidates the adapter digest; semantic
damage tests additionally flip each named execution family and prove refusal.

### Canary receipt authority lives before the activation branch

Gate 2 is its own dormant PR. It lands ref_update_core, ref_update.py, the provider adapter,
the reusable workflow, activation template, guards, and tests on the default branch without
calling them from production events or retiring legacy continuity. The trusted canary
workflow then runs from that exact merged default-branch commit and publishes one bounded
artifact.

A separate trusted verifier downloads that exact artifact through the existing bounded API
lane and commits a canonical receipt at
automation/canaries/receipts/ref-update-observer-v1.json in a second records-only PR before
the activation branch is created or rebased. Its ASCII/sorted-key/no-whitespace/one-LF JSON
has exactly top-level keys `schema,tested_commit,authority_policy,adapter_policy,fixture,workflow,artifact,rows,cleanup`.
The nested objects have exactly:

```text
workflow = repository,workflow_path,workflow_sha,head_sha,run_id,run_attempt,conclusion
artifact = artifact_id,name,size,sha256
row      = scenario,source_repository,old,new,state,exit,result_sha256
cleanup  = manifest_sha256,status
```

`schema` is `agentfold-ref-update-canary-receipt/v1`; every SHA/OID/digest is full lowercase,
integers are nonnegative bounded decimals, scenario rows are unique and sorted, and the
closed scenario registry requires every live matrix row. The trusted verifier requires the
provider metadata's repository, workflow path/SHA, head SHA, run/attempt, success conclusion,
artifact ID/name/size/digest, and downloaded canonical payload to agree before proposing the
receipt. Unknown or missing keys, duplicate JSON keys, stale attempts, copied run IDs, or
expired artifacts refuse the receipt.

Gate 3 reads receipt bytes from its immutable default-branch base commit, not the candidate
tree. Its trusted default-branch workflow rejects any candidate diff touching the receipt,
re-fetches the exact provider run/attempt/artifact, revalidates the artifact hash and metadata,
and compares candidate authority/adapter/workflow bytes to that authenticated receipt. If
the artifact has expired or the API is unavailable, activation is unavailable and legacy
continuity remains. Activation tests/records cannot replace the receipt or its base blob.

### Atomic activation updates every live contract

The activation commit installs the byte-identical dedicated workflow, removes the old
workflow calls and parser/implementation, and updates every live caller contract, help
surface, repository instruction, handbook procedure, source guard, test, and test-ownership
entry that names `--displaced-tip` or its program identifiers. The current mandatory set
includes .github/workflows/harness.yml, automation/AGENTS.md,
automation/reconcile/reconcile.py, automation/tests/test_github_action_projection_workflow.py,
automation/tests/test_markdown_semantics.py, automation/tests/test_reconcile_queue.py, and
handbook/git-workflow.md, plus any new live hit discovered at activation time. Immutable
historical POCs, task records, handovers, and captured evidence keep their original text.

A final-tree source scan classifies every occurrence as live or immutable history and fails
unless live occurrences are zero. The activation diff may update those discovered live
contract/test paths and task records, but no authority-policy, adapter-policy, canary receipt,
reusable workflow, or template byte. An unclassified new reference, a changed digest-covered
byte, or receipt change refuses the whole activation before legacy code is removed.

### Gate boundary

Production remains unopened. A fresh full five-lens review of one immutable revision must
accept these direct-process, full-workflow, and external-receipt boundaries before dormant
core implementation starts.

## 2026-09-01 correction amendment 19 — closed receipts and exact activation tree

Review of `c9608fcc191072fbe1bcea27313384eba8e47b9b` accepted classifier
semantics but rejected the receipt and activation contracts. A batch child needs three
pipes, not two; receipt JSON escaping, fixture identity, artifact rows, and negative
observation states were open; and a path-level activation allowlist could hide unrelated
ordinary-check changes. This section supersedes amendment 18's descriptor, receipt schema,
scenario-registry, and activation-diff clauses. Direct evaluator, full workflow blobs, and
adapter transcript remain selected.

### Exact child descriptors and kernel pipe capacity

The centralized Linux child launcher uses explicit `os.pipe2`/fork/exec descriptors rather
than an implementation-dependent subprocess layout. A one-shot child has stdin bound to a
read-only /dev/null descriptor plus two pipes: stdout and stderr. The long-lived batch
child has three pipes: request stdin, response stdout, and stderr. One close-on-exec status
pipe reports pre-exec resource-limit/group/descriptor failure and closes on successful exec.
At the maximum overlap, the batch child's three pipes, one one-shot child's two pipes, and
the one-shot spawn-status pipe make six live kernel pipes.

Before fork, the launcher sets each pipe to exactly 65,536 bytes with Linux `F_SETPIPE_SZ`
and verifies it with `F_GETPIPE_SZ`; inability to obtain and verify that exact size makes
Strategy A unavailable before the child exists. Therefore the closed peak kernel pipe
capacity is `6 * 65,536 = 393,216` bytes. Parent ends are nonblocking and served by one
selector; child ends are blocking. Every request, response, stderr, and status byte is also
charged to its logical cap before retention. Exec success closes/reaps the status pipe;
every other completion closes every end, terminates the child's group if needed, drains
bounded readable data, waits, and reaps. Fault tests stop reads/writes on each of the six
pipes, leak each descriptor in turn, fail before/after exec, and prove the exact capacity,
deadline, EOF, cleanup, and at-most-two-child registry.

### One canonical receipt and artifact encoder

Canary artifact and receipt JSON use exactly Python's semantic encoding
`json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))`
encoded as ASCII plus one LF. Forward slashes are not escaped; non-ASCII uses lowercase
`\\u` escapes and valid surrogate pairs; integers have no leading zero; booleans/null use
lowercase JSON spellings. Strict decoding rejects duplicate keys, floats, NaN/infinity,
unpaired surrogates, unknown/omitted keys, and any byte sequence whose decode/re-encode is
not identical. Receipt bytes are capped at 2 MiB, rows at 32, strings at 8 KiB each, and all
provider integer IDs at `1..2^63-1`; the existing 64 MiB compressed/128 MiB extracted
artifact caps still apply. Fixed cold-clone golden bytes cover slashes, quotes, controls,
non-ASCII, surrogate pairs, every integer boundary, duplicate keys, and each cap/+1.

The canary artifact has exactly top-level keys
`schema,tested_commit,authority_policy,adapter_policy,fixture,workflow,rows,cleanup`; its
schema is `agentfold-ref-update-canary-artifact/v1`. The committed receipt has those exact
members plus `artifact`; its schema is `agentfold-ref-update-canary-receipt/v1`. Every
shared nested value in the receipt must be object-equal and canonically byte-equal to the
downloaded artifact projection; metadata cannot replace the artifact's claims.

`fixture` has exactly these scalar keys:

```text
scenario_nonce, manifest_sha256,
base_repository_id, base_repository_full_name, base_owner_id, base_owner_login,
fork_repository_id, fork_repository_full_name, fork_owner_id, fork_owner_login,
fork, parent_repository_id, source_repository_id
```

Repository/owner IDs are positive bounded integers; full names/logins are exact provider
ASCII strings. Base/fork repository IDs and owner IDs must differ, `fork` is literal true,
and both parent/source repository IDs equal the base repository ID. The verifier re-fetches
both repositories by numeric ID, requires the recorded names, owners, `fork`, parent, and
source to match, and refuses a rename or topology change rather than following it.

`workflow` has exactly
`repository_id,repository_full_name,workflow_path,workflow_sha,head_sha,run_id,run_attempt,conclusion`.
The repository pair must equal the base fixture, conclusion is `success`, workflow/head
SHAs are full OIDs, run attempt is `1..1,000`, and all other IDs use the provider integer
bound. `artifact` remains exactly `artifact_id,name,size,sha256`; size is within the artifact
cap and name is the one literal registry value. `cleanup` remains exactly
`manifest_sha256,status`, where status is `complete` and the digest equals fixture manifest.

### Tagged observation rows and literal scenario registry

All row variants share exact keys
`kind,scenario,source_repository_id,source_repository_full_name,old,new`. Source identity
must equal either the base or fork fixture pair; O/N are full object-format tokens, with an
all-zero event sentinel allowed only in a not-applicable creation/deletion row.

- `completed` adds exactly `state,evaluator_exit,result_sha256,job_id,job_conclusion`.
  State is `clean|blocked`, exit is respectively 0|1, conclusion is `success|failure` under
  the closed result mapping, and no zero endpoint is allowed.
- `no-observation` adds exactly
  `observation,reason,event_sha256,polls,runs_examined,matching_tuples,window_complete`.
  It has no evaluator exit/result/job. Counts are bounded nonnegative integers,
  `matching_tuples=0`, and `window_complete=true`.
- `pending` adds exactly
  `observation,reason,event_sha256,run_id,run_attempt,job_id,job_conclusion`.
  It has no evaluator exit/result; conclusion is one of
  `queued|waiting|action_required|approval_required`.
- `not-applicable` adds exactly `observation,reason,event_sha256` and has no evaluator or
  job fields.

Every event/artifact SHA-256 is over exact downloaded raw bytes and uses lowercase
`sha256:<64-hex>`. The provider verifier independently repeats bounded discovery and
requires each negative/pending fact; controller exit or artifact success can never stand in
for an evaluator result.

The literal sorted scenario registry and required kind is:

```text
approval-pending-public-fork                 pending
branch-creation                              not-applicable
branch-deletion                              not-applicable
conflicted-public-fork-invalid               completed
conflicted-public-fork-valid                 completed
public-fork-invalid                          completed
public-fork-valid                            completed
retention-expired                            no-observation
same-repository-invalid                      completed
same-repository-valid                        completed
sha-like-public-fork                         no-observation
sha-like-same-repository                     no-observation
stale-rerun-exact-edge                       completed
```

The artifact and receipt contain each registry name exactly once, sorted, with the exact
kind. Completed valid/invalid rows must exercise both exit mappings; stale rerun must reuse
the original event O/N; retention and SHA-like rows must carry real zero-match discovery;
pending must bind the provider attempt. An unexpected `unavailable` row never substitutes
for a registry entry.

The receipt is an automation input, so its isolated landing is a core-data PR, not a
records-only PR. It runs core-scope, schema, provider-reverification, and cold-clone golden
tests before becoming the immutable base of activation.

### Activation is one authenticated blob transition, not a path allowlist

Gate 2 also lands two digest-covered files: a canonical activation manifest and its exact
binary-safe patch. The manifest has schema `agentfold-ref-update-activation/v1`, the patch
SHA-256, and a sorted row for every live runtime/workflow/contract/help/test/ownership path.
Each row has exactly `path,mode,before_blob,after_blob`; a new/deleted blob uses JSON null on
the absent side. Blob OIDs are full repository-object-format IDs and modes are the exact Git
tree modes. The patch is reviewable source; a test applies it to a temporary tree whose
before blobs equal the manifest, then requires every resulting mode/blob to equal the after
side and no other non-record path to change.

The adapter-policy manifest hashes both activation files before live canaries. The canary
receipt binds their adapter digest. At gate 3, trusted default-branch code reads the
activation manifest/patch and receipt from the immutable base, requires every candidate
non-record change to be exactly one listed before→after transition, and requires every
listed transition. It separately permits only task/worklog/verification record changes,
which cannot affect runtime or tests. Candidate tests do not define the expected tree; the
base-authenticated after blob IDs do.

The trusted gate then applies the base patch in a temporary tree, runs the full repository
suite, source/workflow damage guards, reconciler, and live-reference scan against that exact
tree, and requires its tree to equal the candidate. A modified ordinary check, weakened
test, extra hunk, omitted documentation repair, new live legacy reference, before-blob drift,
or different file mode changes a blob/tree ID and refuses activation. Default-branch drift
invalidates the before set and returns to gate 2; it is never three-way merged into an
uncertified activation.

### Gate boundary

Production remains unopened. A new immutable revision needs all five fresh lenses before
dormant core work begins.

## 2026-09-01 correction amendment 20 — provider-real pending and projected activation

Review of `7a6eec531026e5c59af4a7a2affd0f07952483d7` again accepted
classifier semantics and rejected CLI/workflow closure. Pending run status was placed in a
job conclusion that may be null or absent; string/count/reason limits and artifact name were
open; activation-manifest bytes/modes/patch commands were undefined; and record permission
contradicted full-tree equality. This section supersedes amendment 19's pending row, scalar
limits/enums, activation-manifest encoding, and final comparison. Other receipt variants,
fixture topology, pipe layout, and exact-blob authority remain.

### Scalar charges and closed provider reasons

Every decoded JSON string is first charged by strict UTF-8 payload bytes, with an 8,192-byte
maximum. Its complete canonical JSON string token, including quotes and escapes, is then
charged with the derived maximum 49,154 ASCII bytes: 8,192 one-byte control scalars can each
expand to six `\\u00xx` bytes plus quotes. Neither count is a Unicode-code-point limit.
Exactly 8,192 UTF-8 bytes succeeds when the whole receipt cap also permits it; the next byte
refuses before encoding. Golden cases cover ASCII, NUL controls, two-/three-/four-byte UTF-8,
combining sequences, and the derived escape maximum. The aggregate 2 MiB receipt cap is
charged on final canonical bytes including LF.

Provider discovery counts have exact limits inherited from the polling contract:
`polls <= 90`, `runs_examined <= 100`, and `matching_tuples <= 1`; a no-observation row
requires zero matches. Run attempts remain `1..1,000`, row count is exactly 13, and numeric
provider IDs remain `1..2^63-1`. The artifact name is exactly
`agentfold-ref-update-canary-v1`.

Observation/reason pairs are fixed by scenario:

```text
approval-pending-public-fork   pending         fork-approval-required
branch-creation                not-applicable  zero-old-endpoint
branch-deletion                not-applicable  zero-new-endpoint
retention-expired              no-observation  artifact-expired
sha-like-public-fork           no-observation  sha-like-head-suppressed
sha-like-same-repository       no-observation  sha-like-head-suppressed
```

Completed rows have no observation/reason fields. Stale rerun is completed and must bind its
original exact event. Unknown reason text, provider outage, controller success, or another
scenario's pair is a schema refusal rather than an unavailable substitute.

### Pending reflects run status; job is optional evidence

The `pending` variant's additional exact keys are now
`observation,reason,event_sha256,run_id,run_attempt,run_status,run_conclusion,job`.
`observation=pending`, `reason=fork-approval-required`, `run_status` is one of
`queued|waiting|pending|requested`, and `run_conclusion` is JSON null. `job` is either JSON
null when GitHub has not materialized one, or an object with exactly
`job_id,status,conclusion`; its status is `queued|waiting|pending`, its conclusion is null,
and its positive ID uses the provider bound. A completed/action-required run does not satisfy
this scenario. The verifier binds the raw workflow-run object by run/attempt and, when
present, the job object by ID; it never copies status into conclusion or invents a job.

Fixed golden/live fixtures cover queued null-job, waiting null-job, and pending-with-job.
If repository approval policy cannot produce one of the permitted pending observations
within the bounded window, the adapter gate is unavailable and activation does not replace
the scenario with a completed or fabricated row.

### Canonical activation manifest and patch

The activation manifest uses the exact amendment-19 JSON encoder and a 2 MiB including-LF
cap. It has exactly top-level keys `schema,patch_format,patch_size,patch_sha256,paths`.
`schema` is `agentfold-ref-update-activation/v1`; `patch_format` is
`git-diff-binary-v1`; patch size is `0..16,777,216` and equals exact patch bytes; digest is
their lowercase SHA-256. There are 1–256 unique path rows sorted by strict UTF-8 bytes,
with 4,096 UTF-8 bytes per path and 1 MiB aggregate path bytes. Paths are normalized
repository-relative strings with no empty, absolute, dot, dot-dot, backslash, NUL, or
duplicate segment/entry.

Each row has exactly
`path,before_mode,before_blob,after_mode,after_blob`. A present mode is one ASCII string in
`100644|100755|120000`; its paired blob is a full object-format OID. An absent side has both
fields JSON null. Both sides cannot be absent. Mode-only, create, delete, and payload changes
therefore have one representation.

Patch bytes are produced in a sanitized-config temporary clone by the literal argument
sequence:

```text
git --no-replace-objects diff --binary --full-index --no-color --no-ext-diff
    --no-textconv --src-prefix=a/ --dst-prefix=b/ <before-tree> <after-tree>
    -- <manifest paths in UTF-8 order>
```

The environment disables external diff, textconv, filters, attributes outside the exact
trees, locale variation, pager, replacement refs, and config includes. The patch is applied
only with `git --no-replace-objects apply --binary --index --whitespace=nowarn <exact-file>`
to an index/worktree initialized at the recorded before blobs; fuzz, three-way fallback,
recount, rejects, and whitespace repair are forbidden. The post-apply index modes/blob IDs
must equal every after row before tests. Cold-clone golden fixtures cover text, executable,
symlink, binary, create/delete/mode change, path ordering, every malformed header, patch
size/+1, and byte/digest drift.

### Runtime projection plus constrained record overlay

The authenticated activation patch owns every non-record candidate change. Define the
runtime projection as all tree entries except these four exact current-task record paths:
`design.md`, `plan.md`, `verification.md`, and `worklog.md` under task
`2026-08-02-stop-a-restack-from-being-blamed-for-another-branchs-deletion` at its unchanged
`1_in-progress` location. No other task, queue, memory, history, roadmap, template, or record
path is excluded.

Trusted base code first applies the authenticated patch to the base and requires the
candidate runtime projection—paths, modes, and blob IDs—to equal that patched runtime
projection exactly. It then admits a record overlay only when all four paths remain regular
`100644` files: design/worklog/verification may only append bytes to their base contents;
plan may only replace existing literal `- [ ]` tokens with equal-length `- [x]` tokens and
must be otherwise byte-identical. Missing, renamed, extra, truncated, or altered prefix
bytes refuse.

The gate overlays those exact candidate record blobs onto the patched temporary tree and
then requires the full tree ID to equal the candidate tree. The full suite, source/workflow
guards, reconciler, core-scope receipt check, and live-reference scan run after this overlay,
so record schema and cross-links are evaluated without letting record bytes define expected
runtime. A later task-status move or handover is a separate post-activation record commit;
it cannot ride inside the authenticated activation.

### Gate boundary

Production remains unopened. A new immutable revision needs all five fresh review lenses
before dormant core implementation.

## 2026-09-01 correction amendment 21 — attempt-bound evidence and closed launcher bytes

Fresh review of `7e41dc7a1a1a916060770fde03bbe821ada2ce64` again accepted
classifier semantics and rejected provider/CLI closure. The aggregate canary run could not
prove which attempt produced each scenario result; the public-fork hold excluded GitHub's
native `action_required` shapes; the exec-status pipe had capacity but no cumulative frame
contract; and a schema-valid activation patch could exceed the complete adapter transcript.
This amendment supersedes amendments 19–20's row variants, attempt verification, status-pipe
bytes, adapter payload bound, and affected golden cases. Canonical JSON, fixture topology,
literal scenarios, process topology, activation reconstruction, and runtime projection remain.

### Scenario input is not provider evidence

Every row now shares exactly
`kind,scenario,source_repository_id,source_repository_full_name,old,new,scenario_input_sha256`.
The last field hashes the exact canonical scenario row in the pre-mutation fixture manifest;
it is an input commitment, not a claim that GitHub emitted an event. For `completed`, the
trusted raw event must independently yield the same source/O/N tuple. For `pending`,
`no-observation`, and `not-applicable`, O/N remain expected fixture endpoints and can never
authorize an evaluator result. This replaces those variants' misleading `event_sha256`.

The variants add only these exact fields:

- `completed`: `state,evaluator_exit,result_sha256,run`;
- `pending`: `observation,reason,run`;
- `no-observation`:
  `observation,reason,polls,runs_examined,matching_tuples,window_complete`;
- `not-applicable`: `observation,reason`.

The existing state/exit mapping, observation/reason pairs, count limits, zero-endpoint rules,
and 13-name kind registry remain. `no-observation` has no run and proves a complete bounded
zero-match provider search. `not-applicable` has no run. Neither variant may carry result,
job, artifact, or provider-event fields.

### One attempt-bound run envelope

Every `completed` or `pending` row has one `run` object with exactly:

```text
repository_id,repository_full_name,workflow_id,workflow_path,workflow_sha,
run_id,run_attempt,event,head_sha,status,conclusion,job,evidence
```

Repository identity equals the base fixture. Provider/workflow/run IDs are positive bounded
integers; `run_attempt` is `1..1,000`; path/event/status and non-null conclusion use the
global string charge; SHAs are full repository-object-format OIDs. `workflow_id`, path, run
ID, attempt, event, head SHA, status, and conclusion must equal the response from
`GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{run_attempt}`. The workflow SHA
is the immutable commit OID named by the expected `github.workflow_sha`; its workflow-path
blob is verified before scenario mutation. A completed publication proves that commit from
trusted job bytes; a held run cannot execute and therefore binds it only as the expected
installed commit/path blob, never as executed code.

`job` is JSON null or exactly `job_id,name,status,conclusion`. A non-null job must appear by
the same positive ID in
`GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{run_attempt}/jobs?per_page=100&page=1`.
The response must report exactly one job and no second page; the undocumented `filter`
parameter, latest-attempt endpoint, and run-wide job collection are forbidden. Its literal
name is `agentfold-ref-update-canary`. Unknown, duplicate, stale-attempt, paginated-extra, or
run-wide-only matches refuse.

For `completed`, run and job status are `completed`, both conclusions are the row's existing
`success|failure` mapping, job is non-null, and `evidence` has exactly
`raw_event_artifact,result_artifact,publication_sha256`. Each artifact object has exactly
`artifact_id,name,size,sha256`; IDs/sizes use existing bounds and digests hash exact downloaded
archive bytes. Names are exactly
`agentfold-ref-update-event-v1-<scenario>-<run_id>-<run_attempt>` and
`agentfold-ref-update-result-v1-<scenario>-<run_id>-<run_attempt>`. Provider metadata must
bind each artifact to the same run ID and report it unexpired.

The pinned workflow writes one ASCII job-log line after both pinned uploads:

```text
AGENTFOLD_REF_UPDATE_PUBLICATION_V1 <unpadded-base64url(canonical-publication-JSON)>\n
```

The unpadded token decodes to the canonical publication JSON including its one LF and is at
most 87,382 ASCII bytes, derived from a 65,536-byte canonical-publication cap. The decoded
publication has exactly
`schema,scenario,repository_id,workflow_id,workflow_sha,run_id,run_attempt,job_name,event_sha256,result_sha256,raw_event_artifact,result_artifact`;
its schema is `agentfold-ref-update-publication/v1`, all values equal the row/run/evidence,
and `publication_sha256` hashes its canonical JSON bytes including LF. The verifier downloads
at most 8 MiB of that attempt-specific job log and 64 MiB across all scenario logs, scans
without retaining unrelated log bytes, and requires exactly one marker occurrence delimited
by LF or CRLF; provider timestamp/presentation bytes may precede the literal marker, but no
byte may split or enter the marker/token. It refuses an overlong token before base64 decode,
decodes/re-encodes it canonically, and matches every byte.

It then safely downloads and extracts the two exact artifacts under the existing archive
caps. The raw-event archive has exactly one regular non-link entry `event.json`, at most
1 MiB, whose bytes are the exact `$GITHUB_EVENT_PATH`; the result archive has exactly one
regular non-link entry `result.json`, at most 32 MiB, whose bytes are the accepted canonical
evaluator result. Absolute/dot/dot-dot/backslash/NUL paths, duplicate entries, directories,
links, devices, encryption, unsupported compression, trailing archive data, or another entry
refuse before extraction. Their payload digests equal the publication, the event derives
source/O/N, and the result derives state/exit/result digest. Artifact metadata alone, an
aggregate-artifact claim, a job from another attempt, or a controller value cannot satisfy
any of these joins.

The aggregate canary artifact remains the transport containing the 13 rows, but the receipt
verifier and Gate 3 independently re-fetch every completed run attempt, attempt-specific job
and log marker, artifact metadata, archive, raw event, and result. Stale rerun explicitly
records the original run attempt and refuses a later attempt even when run ID, scenario, or
artifact basename is shared. Expired per-scenario logs/artifacts make activation unavailable.

### Provider-real public-fork hold union

For `pending`, `evidence` is JSON null and job is optional because no workflow byte may have
executed. Exactly one provider-observed run pair is accepted:

```text
status=waiting          conclusion=null
status=action_required  conclusion=null
status=completed        conclusion=action_required
```

This is an exact union, not two independent enums. It follows the provider's public-fork
hold shapes while excluding ordinary queueing, execution, cancellation, and terminal
failure. For the first two pairs, a non-null job has status
`queued|waiting|pending|requested` and null conclusion. For the third pair, a non-null job
has status `completed` and conclusion `action_required`. Every non-null job must satisfy the
attempt-specific lookup above; otherwise job is null. The row reason remains
`fork-approval-required`. Because the held run cannot publish raw event bytes, this
variant proves only provider-visible policy state and expected scenario input, never event
payload or classifier success. If none of the three pairs appears inside the fixed discovery
window, the adapter gate is unavailable.

Golden provider fixtures cover all three run pairs, each with null job and each permitted
job status where the API materializes one, plus crossed status/conclusion pairs, completed
success/failure, action-required under a different run/attempt, latest-attempt aliasing, and
job/artifact/log swaps. Live canaries must observe one permitted pair; they do not require
the provider to manufacture every historical shape.

### Exec-status is a 16-byte protocol, not a streaming channel

The close-on-exec status pipe accepts exactly one of two transcripts. Successful `execve`
is zero bytes followed by EOF. A pre-exec failure is one atomic 16-byte record followed by
EOF:

```text
bytes 0..3   ASCII "AFEX"
byte 4       version 1
byte 5       stage: 1=setpgid, 2=address-limit, 3=descriptor-map,
                      4=descriptor-close, 5=execve
bytes 6..7   zero
bytes 8..11  uint32be errno, range 1..2^31-1
bytes 12..15 zero
```

The child makes one `write` no larger than `PIPE_BUF` and then `_exit`s; a short/interrupted
write is not retried into a second record. The parent has a cumulative accepted cap of 16
bytes and a 17-byte detection allowance: it reads at most 17 total, retains at most 17,
and on the seventeenth byte immediately marks infrastructure unavailable and terminates the
registered group without draining unbounded logical data. Kernel-resident unread bytes stay
inside the separately charged 65,536-byte pipe capacity. EOF at 1–15 bytes, invalid magic,
version/stage/errno/reserved bytes, a second/extra byte, or a deadline before EOF all refuse;
none is a domain `blocked` result. Parent-side failures before fork use the parent error path
and never fabricate a status record.

Tests cover zero-byte EOF, every valid stage, errno bounds, exact 16, bytes 1–15, byte 17,
two concatenated records, invalid/reserved fields, short write, writer stall, reader stall,
success/failure races, and descriptor/group cleanup. The six-pipe 393,216-byte kernel peak
and at-most-two-child process registry are unchanged.

### Adapter transcript has composable category budgets

The adapter-policy manifest keeps its exact framing and 1–16 path limit, but its aggregate
payload cap is now 26 MiB (27,262,976 bytes), divided into simultaneously enforceable
categories: the exact activation patch is at most 16,777,216 bytes; its exact activation
manifest is at most 2,097,152 bytes including LF; every other digest-covered adapter/core/
workflow/template/guard/test blob is at most 8,388,608 bytes in aggregate. The two activation
paths are literal registry entries and cannot be reclassified. Every path belongs to exactly
one category; all three counters are precharged before hashing.

With the unchanged maximum framing of 4,329 bytes, the exact maximum digest input is
27,267,305 bytes. Hashing streams each immutable Git blob in at most 65,536-byte chunks and
does not retain the aggregate transcript. Golden vectors reach all three category maxima at
once, the 26 MiB aggregate maximum, and each category/aggregate +1; a 16 MiB patch plus 2 MiB
manifest always leaves the promised 8 MiB for every other required blob. Gate 2 is unavailable
if the exact required non-activation files exceed that reserved category rather than silently
reducing the patch limit.

### Gate boundary

Production remains unopened. Budget and core-fit review do not inherit the semantic ACCEPT;
all five lenses must review one new immutable revision before dormant implementation.

## 2026-09-01 correction amendment 22 — bounded activation materialization

Fresh review of `3ba7d9f54c7ad22761a5306a0a43035f51a00a59` accepted semantic and
provider behavior and rejected activation resource closure. A Git binary patch can compress
a one-GiB zero blob below the 16 MiB patch limit, so post-apply OID comparison cannot protect
memory or disk. This amendment supersedes amendments 20–21's activation row, diff/apply
execution, and resource tests. Attempt-bound receipt evidence, Strategy A semantics, and the
26 MiB adapter transcript remain.

### Blob size is authenticated before content is materialized

Each activation path row now has exactly
`path,before_mode,before_blob,before_size,after_mode,after_blob,after_size`. A present side's
size is the decimal Git blob payload size `0..33,554,432`; an absent side has mode, blob, and
size all JSON null. Both sides cannot be absent, and the two present/absent mode/OID/size
tuples cannot be identical. Rows still count per path, so two paths referencing one blob
charge its materialized size twice.

There are at most 134,217,728 before bytes and 134,217,728 after bytes across all rows;
their combined materialization charge is at most 268,435,456. Before patch generation and
again before application, trusted code queries every OID through the sanitized, no-alternate,
no-replacement, no-promisor object view using the centralized child launcher and exact
`git cat-file --batch-check` grammar. Type must be `blob`, reported size must equal the
manifest, every requested OID must return once in request order, and the per-path and three
aggregate counters are precharged before any blob body, diff, checkout, or apply is read.
Missing/corrupt objects, unexpected fetch, duplicate output, size drift, overflow, or a
counter +1 makes the gate unavailable.

Gate 2 accepts no supplied patch. It first proves these bounds against the exact before and
candidate-after trees, then generates the patch itself. Gate 3 authenticates manifest and
patch bytes from its immutable default-branch base, repeats size/type preflight against its
base and the candidate ODB, and rejects patch/digest drift before invoking the parser or Git.
A candidate cannot use a small manifest size to license a larger object or replace the
canaried patch.

### Binary inflation is parsed before Git apply

After digest and size preflight, a bounded streaming parser validates the complete patch.
It admits only Git's exact full-index text or `GIT binary patch` grammar for the sorted
manifest paths, with no combined diff, rename/copy, submodule, quoted-path ambiguity, omitted
index OID/mode, extra section, or unconsumed/trailing byte. Every header OID/mode and
create/delete relation equals its manifest row.

For each binary forward/reverse body, the parser decodes Git base85 and zlib incrementally,
with one byte beyond the declared bound reserved only for overrun detection. A literal body
must inflate to exactly its declared and corresponding target size. A delta body parses the
source/target varints, requires them to equal the corresponding manifest sizes, checks every
copy range against source size and every insert against available delta bytes, and charges
the computed output before each instruction; its final output is exactly target size and at
most the per-blob cap. Concatenated streams, dictionary requests, invalid/non-minimal lengths,
integer overflow, unused compressed data, a second zlib member, checksum failure, premature
EOF, and declared/actual mismatch refuse before `git apply`.

Text hunks are not compressed: their entire added payload is already charged to the 16 MiB
patch cap. The parser validates monotonically increasing non-overlapping hunk coordinates,
old/new line counts, prefixes, and Git's exact no-final-newline marker. It streams the
bounded before blob once, byte-counting unchanged/deleted/added segments without retaining a
second full copy, and requires the computed output size to equal `after_size` before Git.
An out-of-range coordinate, overlapping hunk, omitted source byte, or trailing source/hunk
data refuses. Git remains the final text/delta semantics oracle; after application, exact
mode/OID/size equality remains mandatory.

Patch generation adds literal `--no-renames` to amendment 20's sanitized `git diff`
argument sequence. Patch size is now `1..16,777,216`; a manifest has 1–256 changed rows, so
zero-byte/no-op patches are invalid. The exact `git apply --binary --index
--whitespace=nowarn <exact-file>` sequence remains, with no fuzz, three-way, recount,
rejects, filters, hooks, or repair.

### Activation children have their own closed resource envelope

Activation preflight, diff, and apply use one direct child group at a time; none overlaps
another activation child or a Strategy A classifier. The trusted parent is limited to
268,435,456 address-space bytes and each child to 536,870,912, for a closed 805,306,368-byte
address-space peak. Each child has a 60-second monotonic deadline and 34 MiB `RLIMIT_FSIZE`;
the whole preflight/diff/parser/apply materialization phase has a 240-second monotonic
deadline. Failure kills the registered process group, closes every descriptor, waits, and
reaps before another stage.

Each child uses the amendment-21 16-byte exec-status protocol plus stdout/stderr pipes whose
kernel capacity is fixed and verified at 65,536 bytes. Batch-check stdout is capped at
1 MiB, diff stdout at 16,777,217 bytes including its refusal sentinel, apply stdout at
65,536 bytes, and every stderr at 1 MiB. Diff stdout streams directly into the quota-bound
patch file while hashing and retains at most 65,536 bytes; byte 16,777,217 terminates the
group and the file is never accepted. Apply reads the already authenticated
patch file directly. Partial UTF-8 is irrelevant to patch bytes; diagnostics are retained as
bounded opaque bytes and escaped only after failure.

### Scratch storage is a required capability, not ambient disk

Gate 2 and Gate 3 require a fresh private scratch-volume capability with a hard one-GiB
(1,073,741,824-byte) per-run write quota, at least 536,870,912 usable bytes at start, no
pre-existing entries, an exact 4,096-byte allocation unit, and no reach outside its root.
The host adapter must prove quota enforcement independently (project quota, container volume,
or equivalent); ordinary `statvfs` free-space observation is insufficient. If the host
cannot provide this behavior, activation is unavailable. This requirement is provider-neutral
and does not add a user-global installer or privileged fallback to core.

Within that volume, trusted code also maintains an exact 462,469,636-byte logical ledger.
Its independently refusing categories are:

```text
working-copy peak       before_total + after_total + max_changed_blob = 301,989,888
loose-object ceiling    raw after bytes + per-row zlib/header/4KiB rounding = 135,313,924
patch                   16,777,216
manifest                 2,097,152
index/path/journal        4,194,304
retained child output     2,097,152
```

The working-copy formula reflects one-path-at-a-time replace: prior after files, remaining
before files, and at most one new temporary blob coexist; after bytes are not charged twice.
The loose-object logical charge per row is exactly
`size + (size >> 12) + (size >> 14) + (size >> 25) + 13 + 14 + 4,095`.
The fixed 14 bytes reserve the largest `blob <decimal-size>\0` header and the fixed 4,095
reserve the worst 4,096-byte block rounding; together they dominate applying zlib's literal
`compressBound` formula to the real header plus payload. The charge remains per path even
when OIDs deduplicate. Its displayed ceiling is reachable as a charge with four 32 MiB rows
and 252 zero-byte rows, and is checked by integer arithmetic rather than assumed allocation.
Fanout directories and filesystem metadata, plus actual manifest, patch, path, journal,
index, and output sizes, charge the 4 MiB metadata category before or at first byte; a
category or aggregate +1 refuses. No category borrows from the hard-volume reserve. The
one-GiB quota contains a Git defect or unexpected extra file; `RLIMIT_FSIZE` contains a
single-file expansion; the logical ledger refuses a valid-but-overbudget plan before starting
a child.

The scratch root is opened fd-relative with no symlink traversal. Success and every failure
remove all generated entries, close the volume capability, and verify the root is empty
before release. `ENOSPC`, `EFBIG`, cleanup timeout, residual entry, mount/quota loss, or a
child surviving group cleanup is infrastructure-unavailable and cannot publish activation.
An interrupted local run leaves one authenticated run-ID tombstone; the next invocation may
clean exactly that one bounded root after verifying ownership, otherwise it refuses rather
than accumulating scratch state.

The reconstructed-tree suite and guards also run inside this same hard-quota volume with
`TMPDIR` and every repository-local cache rooted there. They inherit the existing test-runner
process/deadline limits; quota exhaustion or an attempted write outside the capability makes
activation unavailable. Test output and caches cannot become manifest evidence and are
removed before the exact candidate-tree comparison.

### Activation damage and boundary suite

Cold-clone fixtures include: zero and 32 MiB blobs; per-blob +1; 128 MiB before/after
aggregates and each +1; duplicate-blob paths charged twice; a highly compressible exact-limit
blob; a sub-16-MiB patch that advertises or inflates to 64 MiB/1 GiB; literal and delta
declared-size drift; delta copy/insert overflow; zlib/base85 exact/+1, concatenation, trailing
data, and checksum damage; text added-byte expansion; patch 1/16 MiB/+1; every logical-ledger
category; the exact 462,469,636 aggregate and +1; hard quota exhaustion; per-file
`RLIMIT_FSIZE`; parent/child address-space failure; every stdout/stderr/status exact/+1;
deadline/group escape; and cleanup after every stage. Generation rejects an oversized
candidate before `git diff`; application rejects an authenticated-fixture damage patch before
`git apply`; no test relies only on the final OID comparison.

### Gate boundary

Production remains unopened. The new immutable revision must again pass all five lenses
before dormant implementation begins.

## 2026-09-01 correction amendment 23 — Git-real mode metadata and supervised suite

Fresh review of `a8f52f86e356c8f35aff9d62eebd268b6342c6a0` accepted classifier
semantics and rejected three activation details: Git omits `index` for a pure mode change,
the current repository runner has no inherited deadline/output cap, and an aggregate +1 is
not independent when the aggregate equals the sum of category maxima. This amendment
supersedes amendment 22's extended-header grammar, post-overlay runner claim, and aggregate
ledger refusal/test. All size categories, hard scratch quota, and pre-apply bounds remain.

### Exact extended-header union includes pure mode changes

The parser admits one and only one form selected from the authenticated row:

1. **Pure mode:** `before_blob == after_blob`, `before_size == after_size`, and modes differ.
   The section is exactly `diff --git`, `old mode <before_mode>`, `new mode <after_mode>`.
   It has no `index`, hunk, binary body, similarity, rename/copy, or create/delete header.
   Omitting `index` is mandatory in this form, matching Git's generated patch.
2. **Content, unchanged mode:** both blobs exist, differ, and modes are equal. The full-index
   line contains exact before/after OIDs and that one mode; any old/new mode header refuses.
3. **Content plus mode:** both blobs exist and differ and modes differ. Exact old/new mode
   headers precede a full-index before/after OID line with no redundant mode token.
4. **Create/delete:** exactly one side is absent. The exact new/deleted-file mode and
   zero-to-full/full-to-zero index OIDs agree with the manifest; the present payload then has
   the corresponding text or binary body.

Only forms 2–4 may contain hunks or a binary body, and every content-changing form requires
both logical full OID endpoints including the all-zero absent sentinel. The parser rejects a
pure-mode section whose blob/size differs, an `index` line in form 1, an omitted index in
forms 2–4, swapped/abbreviated OIDs, misplaced mode token, duplicate extended header, or a
body inconsistent with the selected form. Cold-clone coverage generates, parses, applies,
and tree-compares regular executable-bit and regular/symlink pure-mode rows plus content-only,
content+mode, create, and delete rows from the literal Git command.

### The activation suite has a real supervisor

Activation never relies on the current runner to police itself. The host scratch capability
also provides one ephemeral cgroup-v2-equivalent execution scope with hard aggregate
`memory.max=2,147,483,648`, swap disabled, `pids.max=32`, and a working kill-all operation.
Capability setup/teardown and limit readback are startup-probed; a host without equivalent
group-wide memory, process, kill, and scratch-quota enforcement is unavailable. The scope is
repository-local/ephemeral and grants no core authority or user-global state.

Trusted base code runs exactly `python3 automation/run_tests.py --jobs 1` as one direct
process group inside that scope. Serial mode prevents the runner's concurrent buffered-output
path. The supervisor streams stdout and stderr separately with 32 MiB accepted caps plus one
detection byte each, enforces a 900-second monotonic deadline, and inherits the 512 MiB
per-process address-space and 34 MiB file-size limits. Exit 0, both EOFs, no live descendant,
and cgroup/process-group emptiness are all required. Cap +1, timeout, signal, nonzero exit,
fork/process limit, aggregate/per-process memory limit, or descendant escape invokes both
process-group termination and scope kill, then waits/reaps before returning unavailable.

The reconciler runs next as exact
`python3 automation/reconcile/reconcile.py --check` in a fresh scope with a 120-second
deadline and 8 MiB stdout/stderr caps. Source/workflow/live-reference guards run as separately
named exact commands registered by the dormant implementation, each in a fresh scope with a
120-second deadline and 8 MiB caps; there are at most four guard commands and the manifest
hashes their complete source and literal argv registry. All post-overlay commands are serial,
share a 1,560-second aggregate monotonic deadline (60 seconds beyond the command ceilings
for bounded startup/cleanup), use the same quota-bound scratch root and
sealed environment, and must exit 0. No candidate test can weaken the trusted supervisor,
argv registry, cgroup adapter, or caps because those bytes are base-authenticated.

The supervisor sets `TMPDIR`, cache roots, Git config, and repository view inside scratch and
allows no write capability outside it. It streams output rather than asking
`subprocess.run(..., PIPE)` to retain it. Tests cover a nonterminating test, 32 MiB and +1
output, a grandchild that changes process group/session, 32-process and +1 forks, aggregate
and per-process memory limits, `EFBIG`/`ENOSPC`, nonzero/signal exits, cleanup interruption,
and an otherwise green serial suite. A scope kill must leave zero descendants and an empty
scratch root before activation can continue.

### Aggregate scratch usage is derived, not a second gate

The six amendment-22 category counters remain independently precharged and refuse at their
own exact limits. `462,469,636` is only their reported derived maximum sum; there is no
seventh aggregate limit or aggregate +1 branch. Therefore tests cover every category's exact
limit and +1 plus the arithmetic sum, but do not claim an independently reachable aggregate
+1. The separate one-GiB enforced volume is the containment boundary for unexpected Git or
test writes; it retains its own quota-exhaustion test.

### Gate boundary

Production remains unopened. The new immutable revision must again pass semantic, CLI, and
provider review before the first budget/core-fit review of this complete contract.

## 2026-09-01 correction amendment 24 — Git file-type pairs and single-charge categories

Fresh review of `fef7d871e1b0364a447ae51b072c1d7caf4bd068` again accepted
classifier semantics and rejected two executable details. Git represents regular-file ↔
symlink changes as a delete/create section pair, not a one-section mode change; and amendment
22's prose accidentally charged patch/manifest/output bytes again to metadata. This amendment
supersedes amendment 23's form selection and amendment 22's category-membership sentence.

### File type selects a fifth paired-section form

Modes `100644` and `100755` share the regular-file type; `120000` is the symlink type.
Amendment 23 forms 1 and 3 apply only to the regular-file executable-bit transition
`100644 ↔ 100755`. A `120000 → 120000` content change uses form 2. Whenever exactly one
side is `120000` and the other is regular, the parser selects a fifth **file-type change**
form regardless of whether blob OIDs/sizes are equal or different.

That fifth form binds one manifest row to exactly two consecutive same-path sections in
this order:

1. a complete deletion from authenticated before mode/OID/size to the all-zero absent
   sentinel, with `deleted file mode`, full-to-zero index, and exact deletion body; then
2. a complete creation from the all-zero absent sentinel to authenticated after
   mode/OID/size, with `new file mode`, zero-to-full index, and exact creation body.

Both sections repeat the same exact normalized `diff --git a/<path> b/<path>` header. No
other path or section may intervene; the path consumes exactly one sorted manifest row and
cannot appear again. Each body independently satisfies amendment 22's bounded text/binary
grammar and the corresponding before→absent or absent→after size/OID relation. The parser
permits no hunk/body only for a deletion/creation whose present blob has size zero and whose
exact Git form therefore ends after the full-index header. It rejects every other bodyless,
reversed, missing, extra, interleaved, rename/copy, abbreviated-OID, wrong-mode, or
independently listed delete/create form. Same-OID/same-size regular↔symlink,
zero-regular↔nonempty-symlink, and different-content transitions are required cold-clone
cases. Literal generation, bounded parse, `git apply --index`, post-apply mode/OID/size, and
final tree equality must all agree.

Actual one-sided path creation/deletion still uses amendment 23 form 4 and exactly one
section, with the same exact zero-size body omission. Therefore a manifest side being null
and a present-side type change remain distinct, unambiguous cases.

### Every scratch byte has one category

Category membership is now mutually exclusive:

- patch file bytes charge only the 16,777,216-byte patch category;
- activation-manifest bytes charge only the 2,097,152-byte manifest category;
- retained stdout/stderr/status bytes charge only the 2,097,152-byte output category;
- path encodings, Git index bytes, journal/tombstone bytes, fanout-directory entries, and
  filesystem metadata charge only the 4,194,304-byte metadata category;
- working-copy payload charges only the working-copy formula; and
- loose-object payload plus its reserved header/compression/block overhead charges only the
  loose-object formula.

The implementation tags each ledger debit with this closed enum and refuses an unknown or
second tag. The patch, manifest, and output payloads are not metadata. This restores the
independent 16 MiB patch boundary while leaving the reported derived sum `462,469,636`
unchanged. Tests reach each category exact limit with all other categories in range, then
change only that category by +1; cross-tag, double-tag, missing-tag, and sum arithmetic have
separate tests.

### Gate boundary

Production remains unopened. One new immutable revision needs the three base lenses before
budget and core-fit review.

## 2026-09-01 correction amendment 25 — mode-bound authority and executable bounds

Fresh review of `38ce7a911af196b9ea88b5252f05abca89f31f87` found three independent
contract defects. A schema-valid control-character path made Git quote patch headers that
the parser could not admit; two source-derived scratch maxima incorrectly promised
independent `+1` fixtures; and an authority file could change from a regular file to a
same-payload symlink without changing the byte-only policy digest. This amendment supersedes
the policy/adapter transcript framing, activation path domain/diff command, and amendment
24's every-category `+1` sentence. Classifier/DAG semantics and the five Git section forms
are unchanged.

### Executable identities bind Git mode and never follow symlinks

The unactivated `authority-policy/v1` and `adapter-policy/v1` byte-only domains are replaced
by `authority-policy/v2` and `adapter-policy/v2`. For either domain, each fixed registry row
is now framed as:

```text
uint64be(len(UTF8(path))) || UTF8(path)
|| uint64be(6) || ASCII(git_mode)
|| uint64be(len(blob_payload)) || blob_payload
```

The domain label, zero separator, row count, fixed registry order, SHA-256, and every other
existing framing rule remain. `git_mode` is exactly `100644` or `100755`; the tree entry must
be a blob. A symlink `120000`, gitlink, tree, absent entry, unsupported mode, duplicate, or
mode/payload lookup failure refuses before hashing. Thus a regular executable-bit change is
a policy/adapter digest change, while a regular-to-symlink change is never a valid executable
registry at all.

Authority digest comparison at O, N, and the executing evaluator binds each exact tree mode
as well as path and payload. The evaluator's on-disk self-check walks from an already opened
checkout-root descriptor, opens every directory component with no-follow directory
semantics, opens the final component with `O_NOFOLLOW`, and hashes from that same descriptor.
`fstat` must report a regular file whose executable-bit class agrees with the authenticated
Git mode: any of `0111` set means `100755`, and none set means `100644`; other permission
bits are not Git tree identity. Substitution, a symlink in any component, executable-class
drift, path replacement during the walk, unsupported no-follow semantics, or byte drift is
`policy-version-mismatch` before classification. The import/registry audit uses the same
mode-bound rows.

The adapter canary and Gate 3 apply the identical rule to every adapter-policy registry
entry. The canary receipt schema is consequently
`agentfold-ref-update-canary-receipt/v2`; it carries the v2 authority and adapter digests,
and an old v1 receipt cannot authorize activation. Gate 3 compares candidate tree modes and
payloads to the immutable-base receipt before accepting the activation patch. Damage tests
change each authority and adapter file independently through `100644 -> 100755`,
`100755 -> 100644`, and regular -> same-payload symlink; change a parent directory to a
symlink; and replace a checked file between path walk and read. Every case refuses before a
domain result. The semantic regression includes the reviewer's latent
`os.path.islink(policy.__file__)` false-clean construction and requires it to stop at policy
verification.

### Activation paths have one unquoted UTF-8 domain

Activation-manifest paths remain strict UTF-8 and keep every existing relative-path,
segment, length, uniqueness, and ordering rule. They now additionally reject any UTF-8 byte
in `00..1f`, byte `22` (`"`), byte `5c` (`\\`), or byte `7f`. This is a byte predicate after
strict UTF-8 validation; non-ASCII UTF-8 remains distinct and is not Unicode-normalized.

Patch generation adds the literal Git option `-c core.quotePath=false` before `diff` in the
already sanitized invocation. For the admitted byte domain, every `diff --git`, `---`, and
`+++` pathname is therefore the raw manifest UTF-8 path with the exact configured `a/` or
`b/` prefix, never a C-quoted or escaped spelling. The parser constructs each complete
expected header from authenticated path bytes and compares it byte-for-byte; it does not
split on spaces or decode a second pathname language. Any quote byte, escape, unexpected
prefix, raw/manifest mismatch, or quoted header refuses before body parsing.

Cold-clone fixtures accept spaces, leading/trailing space, single quote, `#`, a leading
hyphen, and multi-byte UTF-8 under `core.quotePath=false`, and prove literal generation,
bounded parse, apply, and final-tree equality. They reject NUL, every ASCII control byte,
double quote, backslash, and DEL before starting `git diff`; damaged fixtures inject Git
C-quoted, octal-escaped, raw high-byte, and mixed raw/quoted headers. The reviewer's
`line<LF>break` regular/symlink transition is a mandatory pre-child schema refusal rather
than a generated patch that the parser cannot authenticate.

### Working-copy and loose-object values are derived reservations

The logical ledger has six mutually exclusive accounting tags but only four independently
refusing byte counters: patch, manifest, retained output, and metadata. Their existing exact
limits and independent exact/`+1` fixtures remain.

Working-copy and loose-object charges are checked, source-derived reservations. The
working-copy expression reaches `301,989,888` exactly only when the already independent
before-total, after-total, and largest-blob inputs reach 128 MiB, 128 MiB, and 32 MiB. The
loose-object expression reaches `135,313,924` exactly only at the already bounded 256 rows,
128 MiB after-total shape of four 32 MiB rows plus 252 zero-byte rows. Checked-uint64
recomputation from authenticated manifest rows must equal the ledger reservation before any
child starts; exceeding either constant still refuses defensively, but no structurally valid
manifest can exceed only that derived value.

Tests therefore reach both derived maxima with valid manifests and retain the source-bound
exact/`+1` tests. For each derived expression, a test-only `observed - 1` limit applied to
the unchanged maximum transcript proves the reservation is charged before work; it is an
observed-red damage control, not a fictitious production `+1` fixture. Unknown, double, or
missing accounting tags and checked arithmetic still refuse. The six-class reported maximum
sum remains `462,469,636`; it is derived rather than a seventh gate, and the hard one-GiB
private-volume quota remains the containment boundary.

### Gate boundary

Production remains unopened. This corrected immutable revision must pass all three base
lenses again before budget and core-fit review; no verdict on a prior SHA transfers.

## 2026-09-01 correction amendment 26 — authenticated source execution and literal paths

Fresh review of `3f3a9554708f7b7f8fb6eac6eb7ee2503f046e48` rejected four
executable gaps. The v2 row framing grew without updated budgets; Git still interpreted an
admitted `:(literal)foo` as pathspec magic; a timestamp-valid untracked `.pyc` could execute
different authority code while the authenticated source passed; and an opened descriptor
cannot observe a later pathname replacement. This amendment supersedes the affected v2
framing maxima, diff invocation, ordinary Python import wording, and amendment 25's
post-open-race refusal. Provider evidence, Git section forms, and Strategy A semantics remain
unchanged.

### V2 framing has v2 limits

Mode length and mode bytes are framing, not payload. Under amendment 25's exact
`uint64 path length + uint64 mode length + six mode bytes + uint64 payload length` row, the
three-source authority maximum is:

```text
3 * (30-byte domain + 2-byte count + 32 * 30-byte row framing + 8,192 path bytes)
= 27,552 framing bytes
12,582,912 payload bytes + 27,552 = 12,610,464 total digest-input bytes
```

These values supersede `25,632` and `12,608,544`. The adapter maximum is:

```text
39-byte domain + 32-byte authority digest + 2-byte count
+ 16 * 30-byte row framing + 4,096 path bytes = 4,649 framing bytes
27,262,976 payload bytes + 4,649 = 27,267,625 total digest-input bytes
```

These values supersede `4,329` and `27,267,305`. Every allocator, precharge, counter limit,
golden transcript, receipt verifier, and exact/`+1` case uses the v2 values. Payload-category
limits do not borrow the extra framing bytes, and all additions/multiplications are checked
before hashing.

### Manifest paths are literal Git arguments

Patch generation adds the global option `--literal-pathspecs` before amendment 25's
`-c core.quotePath=false` and `diff`. The complete command prefix is therefore:

```text
git --no-replace-objects --literal-pathspecs -c core.quotePath=false diff
    --binary --full-index --no-color --no-ext-diff --no-textconv --no-renames
    --src-prefix=a/ --dst-prefix=b/ <before-tree> <after-tree> -- <manifest paths...>
```

The sanitized environment also removes every `GIT_*_PATHSPECS` variable; command-line
literal semantics are still mandatory and cannot be supplied only by ambient configuration.
Golden fixtures change files literally named `:(literal)foo`, `:(glob)*`, `:/top`, `:!drop`,
`:^drop`, and `:` and require a nonempty exact patch whenever the trees differ. Damage tests
remove or reorder `--literal-pathspecs`, inject hostile pathspec environment variables, and
prove the candidate tree is never silently projected to an empty or different path set.

### Authority modules execute only authenticated source bytes

"Imports ref_update_core in process" now means an authenticated in-memory source load, not
Python's filesystem import machinery. The local CLI and GitHub evaluator are each launched
as a direct source script by the host-pinned CPython executable with exact `-I -S -B` flags,
an allowlisted environment, empty user import paths, and the supported interpreter profile.
Module, directory, zipapp, `runpy`, sourceless, and `-c` entry shapes are unavailable. Each
entrypoint verifies those flags/profile before importing or executing any authority module;
failure is exit 2 with no classifier result.

Before authority execution, the bootstrap completes amendment 25's O/N/evaluator v2
mode/payload verification and retains one immutable byte buffer per evaluator registry row
from the already opened no-follow descriptor. It rejects any authority module name already
present in `sys.modules`, preloads only the pinned standard-library allowlist under the
isolated interpreter, removes filesystem/zip/path-hook finders, and installs one loader whose
closed name table maps only authority module names to those buffers.

For every authority module, that loader:

1. strictly decodes the authenticated payload as UTF-8;
2. compiles that exact text with a fixed synthetic `agentfold-authority:<path>` filename,
   `dont_inherit=True`, `optimize=0`, and no caller-supplied flags;
3. creates a fresh module with the fixed registry name/package and no `__file__` or
   `__cached__` value; and
4. executes only the returned code object in that module namespace.

It never asks `PathFinder`, `SourceFileLoader`, `SourcelessFileLoader`, a cache tag, bytecode
magic, `marshal`, or an on-disk path for code. The source/import audit rejects authority use
of `__file__`, `__cached__`, dynamic `compile`/`eval`/`exec`/`__import__`, importlib/runpy/
pkgutil/marshal loaders, or an undeclared module edge. After preload, an allowlisted standard
library module can be reused from `sys.modules`; no new filesystem import is possible during
classification. The adapter evaluator applies the same loader contract rather than using a
second implementation of authority imports, and local/provider parity compares the complete
canonical result.

Untracked timestamp-valid, checked-hash, unchecked-hash, corrupt, and sourceless `.pyc`
files; a same-name zip module; a source-shadow directory; preloaded `sys.modules` entry;
hostile meta/path hook; and every cache-tag spelling are mandatory damage fixtures. Each is
either ignored because no filesystem loader is consulted or refused before authority code;
none can change one result byte or counter. A control compiles different equal-length source
into a timestamp-valid cache, restores the authenticated source/mode/timestamp, and must
still execute the authenticated `blocked` source rather than the cached `clean` code.

### An opened descriptor is the namespace boundary

The impossible promise that a rename after successful `open(..., O_NOFOLLOW)` must be
detected is withdrawn. A replacement before the final open is still refused by no-follow,
regular-mode, size, and payload verification. Once opened, the descriptor and retained bytes
are the authority: a later rename or symlink cannot alter `fstat`, the bytes compiled, or the
in-memory module, and authority code has no source pathname capability to re-open or inspect.

Race tests pause immediately before open and require a replacement to refuse; then pause
immediately after open, replace the namespace entry with different bytes and with a
same-payload symlink, and require byte-identical execution from the opened descriptor. The
reviewer's latent `os.path.islink(policy.__file__)` source is rejected by the authority audit,
and its untracked-pyc false-clean construction executes the authenticated source. This is
execution binding, not a claim that POSIX reports a post-open rename.

### Gate boundary

Production remains unopened. A new immutable revision must again pass all three base lenses
before budget and core-fit review; prior accepts and partial positive controls do not carry.

## 2026-09-01 correction amendment 27 — external trust root and sealed evaluator

Fresh review of `79a4fe9f3e45feac2214509fc2dea17254295859` accepted provider
sequencing and literal Git behavior but rejected three execution claims. An entrypoint cannot
authenticate bytes before CPython has executed that entrypoint; removing `__file__` does not
remove `open()` or known-path observation; and the interpreter/standard-library profile was
unnamed. CLI review also found two more derived adapter values still promised impossible
independent `+1` fixtures. This amendment supersedes the evaluator launch/root-of-trust,
source-namespace, runtime-profile, and derived-counter wording. It does not widen classifier
or provider authority.

### Trust begins outside the mutable evaluator checkout

No repository Python process claims to authenticate its own first instruction. Strategy A
now requires a **host launcher capability** whose running identity is established before the
candidate/evaluator checkout is visible. The launcher is an adapter boundary, not classifier
authority: core defines its closed input/output/capability protocol, and a host either
attests the exact launcher/runtime identities or reports unavailable. There is no fallback
to executing a self-verified worktree script.

The admitted launcher artifact is one statically linked Linux executable for the selected
architecture, at most 16 MiB, with no ELF interpreter, dynamic dependency, plugin, config
include, executable search, or runtime download. `launcher-policy/v1` binds its architecture,
size, mode, SHA-256, exact argv/environment schema, and required kernel-capability probe.
The probe executes mount/user-namespace, read-only-remount, pivot/detach, sealed-volume,
descriptor, and privilege-drop controls against disposable sentinels before accepting the
host. Kernel/capability mismatch is unavailable; a version string alone is not evidence.

For GitHub, the trusted default-branch workflow is the prior trust root. Before launching
Python, its base-authenticated adapter step verifies the launcher artifact ID, SHA-256, mode,
size, and adapter-policy-v2 membership against the immutable receipt. Candidate code, the
candidate object source, and a candidate workflow cannot supply or replace it. For local
diagnosis, `automation/install.py` materializes the same digest-covered launcher in the Git
common directory outside every worktree and records its source commit/digest; the documented
command invokes that installed path. A missing, drifted, worktree-resident, or differently
digested launcher makes continuity unavailable. The installer copy is repository-local and
optional; it creates no user-global state or provider dependency.

The launcher opens every authority-policy-v2 source with amendment 25's fd-relative
no-follow checks, compares exact Git mode/size/payload to its base-authenticated manifest,
and only then constructs the evaluator. `ref_update.py`, its CLI parser, bootstrap, core, and
support modules are all ordinary authenticated rows. None is executed from its original
path. A substituted direct script, `python -m`, `-c`, stdin, directory, zipapp, or ordinary
worktree invocation is not a Strategy A authority entrypoint and cannot produce an accepted
result.

The launcher creates a sealed memory-backed policy directory from the already opened bytes,
preserves only authenticated `100644|100755` executable class, fsyncs it, bind-mounts it
read-only in a new private Linux mount namespace, and verifies every resulting file back to
the manifest. It then launches the authenticated `ref_update.py` from that sealed path with
the exact interpreter profile below. Thus CPython's first evaluator byte is the same
pre-opened, mode-checked, payload-authenticated byte sequence; the in-process loader still
compiles the remaining rows from retained authenticated buffers and never consults a cache.

Launcher provenance is explicit in `launcher-policy/v1`, and accepted evidence carries
`launcher_policy_sha256`. The v2 canary artifact/receipt and Gate 3 bind that value beside
authority-policy-v2 and adapter-policy-v2. A launcher update is a new dormant landing,
canary, and receipt; a launcher cannot attest a changed copy of itself into an old receipt.
Local/provider parity is claimed only when the exact launcher, runtime, authority, and
adapter digests all match.

### The evaluator has no source-checkout namespace

Before evaluator exec, the launcher makes mount propagation private and constructs a fresh
root containing only:

- the sealed read-only policy directory;
- the exact read-only runtime-profile files;
- the read-only isolated Git object directory selected for O/N;
- the already bounded writable scratch volume; and
- device/descriptor endpoints explicitly required by the child-launcher contract.

The original evaluator checkout, host root, home, other worktrees, caches, sockets, and
ambient `/proc` are not mounted. The launcher pivots into the new root, detaches the old
root, closes every source/host descriptor not named by the protocol, verifies the mount and
descriptor allowlists, drops setup privilege, and only then execs CPython. A host unable to
prove private mount propagation, read-only policy/runtime/object mounts, pivot/detach,
descriptor closure, and no route to the old namespace reports unavailable.

Authority code may retain ordinary Python filesystem APIs, but every spelling of an
original registry path, `sys.argv[0]`, cwd-relative escape, symlink, hardlink, /proc/self/fd,
or absolute host path is either absent or outside the sealed root. The only source pathname
it can observe is the immutable authenticated policy copy. Replacing the original checkout
before or after the launcher's open cannot change that copy or the compiled buffers. Tests
attempt rename, symlink, hardlink, bind-mount propagation, descriptor inheritance, proc-fd,
cwd/root escape, and concurrent host replacement at every launch boundary; accepted result
bytes remain bound to the sealed copy, and any setup/allowlist drift refuses before Python.

This source-free namespace supersedes amendment 26's claim that a source audit alone removes
pathname capability. The audit still forbids bytecode/dynamic loaders and catches accidental
source introspection, but namespace construction is the enforcement boundary.

### Runtime profile is content-addressed

`runtime-profile/v1` is canonical JSON plus LF, independently decoded/re-encoded with the
receipt encoder. It has exact scalar fields for CPython implementation, full version tuple,
cache tag, bytecode magic, ABI/SOABI, platform, byte order, and every required `sys.flags`
value. It records the exact invocation flags `-I -S -B -X utf8`, fixed locale/time-zone,
and a sorted manifest of every interpreter executable, dynamic loader/library, encoding,
preloaded standard-library source/extension, and other runtime file mounted in the private
root. Each file row binds role, normalized relative path, regular mode, size, and SHA-256;
unknown files, symlinks, writable runtime entries, late imports, or an unlisted loaded mapping
are unavailable.

Its top-level keys are exactly
`schema,implementation,version,cache_tag,magic_number,abi,soabi,platform,byteorder,flags,invocation,locale,timezone,files`.
`schema` is `agentfold-runtime-profile/v1`; `version` is exactly five bounded values for
major/minor/micro/release-level/serial; `flags` has the closed CPython flag-name registry;
`invocation` is the exact argument vector; and each file has exactly
`role,path,mode,size,sha256`. The canonical manifest is at most 2 MiB, with at most 1,024
files, 4,096 bytes per path, 1 MiB aggregate path bytes, 128 MiB per file, and 512 MiB
aggregate file bytes. Role and scalar strings use closed registries or the existing 8 KiB
string bound. Every count, byte, path, and canonical-output limit has exact and `+1` tests;
derived framing/total values use observed-minus-one controls.

The host launcher verifies the runtime tree before mount and the evaluator rechecks the
reported profile after preload using the sealed paths and loaded-module/mapping registry.
After the closed standard-library allowlist is preloaded, filesystem/zip importers are
removed as in amendment 26. `/proc` is unavailable to classifier code, so loaded native
mappings are attested by the launcher before detach rather than discovered afterward.

Define:

```text
execution-policy/v1 = SHA256(
  ASCII("agentfold-execution-policy/v1") || 00
  || raw32(launcher_policy_sha256)
  || raw32(runtime_profile_sha256)
  || raw32(authority_policy_v2_sha256)
)
```

The canonical result, canary rows, artifact, receipt, and activation verifier carry all four
digests. A runtime/launcher mismatch is a stable incomplete result before graph work; it is
never a different implementation of the same authority digest. Runtime or stdlib updates
therefore require a new dormant canary/receipt rather than relying on source parity. Hash
seed still varies in golden tests and must not change results; it is not treated as hidden
runtime identity.

Launcher work has its own non-overlapping envelope before evaluator exec: 256 MiB address
space, 120-second monotonic deadline, 32 processes, 32 descriptors, 64 KiB streaming chunks,
8,192 runtime-file chunks, a 16 MiB sealed policy-volume quota, 2 MiB retained diagnostics,
and zero network or writable path outside that volume. Runtime files are verified streaming
from the host-attested read-only volume and are never copied into policy scratch. `execve`
replaces the launcher, so launcher and evaluator address-space peaks do not overlap. Every
setup failure closes descriptors, kills/reaps helpers, unmounts the private root, empties the
policy volume, and emits unavailable; fault tests cover each limit, mount stage, partial
copy/hash, interrupted exec, and cleanup residue.

### Adapter totals are derived observations

Authority and adapter framing maxima, adapter payload aggregate, and total digest-input
maxima are checked derived counters, not independent production gates. The independent
source gates are registry row/path bytes, authority payload bounds, and the adapter patch,
manifest, and other-payload categories. Exact/`+1` tests remain on those source gates.

Valid maximum transcripts reach authority framing `27,552`, adapter framing `4,649`, adapter
payload `27,262,976`, and adapter total `27,267,625`. For each derived value, the unchanged
maximum transcript is rerun with a test-only `observed - 1` limit and must refuse before
hashing. There is no claim that framing `4,650` can preserve the 16-row/4,096-path-byte
limits, or that aggregate payload `27,262,977` can preserve all three category limits.
Checked arithmetic, exact reported maxima, unknown/double category tags, and per-source
limit-plus-one damage controls remain.

### Gate boundary

Production remains unopened. The external launcher and sealed-runtime requirements are part
of core/adapter feasibility review; a new immutable SHA needs all three base lenses before
the remaining budget and core-fit gates.

## 2026-09-01 correction amendment 28 — closed execution evidence and rooted launch

Fresh review of `cf2dd89520caec1bb855eb8f7c53516705affaf6` rejected three
cross-layer contradictions: closed result/receipt schemas had nowhere to carry new execution
identities; a worktree installer was not an independent local trust root; and a launcher
cannot enumerate mappings loaded only after `execve`. It also found open JSON representations
and a first-canary receipt cycle. This amendment supersedes all result/canary/publication
schemas affected by execution identity, gives both policy manifests exact encodings, splits
canary-time manifest trust from activation-time receipt trust, and narrows native-runtime
attestation to the sealed root that can actually be proven.

### Launcher policy has one canonical representation

`launcher-policy/v1` uses the existing ASCII canonical-JSON-plus-LF encoder and duplicate-key
refusal. Its top-level keys are exactly
`schema,architecture,executable,argv_schema,environment,kernel_capabilities`.

- `schema` is `agentfold-launcher-policy/v1` and `architecture` is the first-release literal
  `x86_64-linux-gnu`.
- `executable` has exactly `format,mode,size,sha256,static`: `format=elf64`,
  `mode=100755`, size is decimal `1..16,777,216`, SHA-256 uses the lowercase prefixed form,
  and `static` is JSON true. The ELF verifier independently requires no `PT_INTERP`, dynamic
  section, executable stack, or trailing second executable.
- `argv_schema` is exactly this JSON string array:
  `["--authority-manifest-fd=3","--runtime-manifest-fd=4","--git-dir-fd=5","--old=<full-oid>","--new=<full-oid>"]`.
  At invocation the two placeholders are replaced once by lowercase full non-zero
  object-format OIDs; every other byte is literal.
- `environment` is the exact empty object. The host closes the environment and launcher
  synthesizes the evaluator environment from its runtime profile.
- `kernel_capabilities` is the exact sorted string array
  `close-range,mount-namespace,pivot-root,private-propagation,read-only-bind,sealed-tmpfs,user-namespace`.

The manifest is at most 65,536 bytes including LF; scalar strings retain the 8 KiB bound.
Decode/re-encode, exact ELF/manifest agreement, every field/enum/ordering mutation, cap/+1,
and executable size/hash/mode drift are golden cases. `launcher_policy_sha256` always hashes
these canonical bytes, not an informal capability list or the executable alone.

### Runtime profile has exact JSON types

`runtime-profile/v1` retains amendment 27's top-level key set and limits with these exact
representations:

- `schema` is `agentfold-runtime-profile/v1`; `implementation` is `cpython`.
- `version` is an object with exactly `major,minor,micro,releaselevel,serial`. The first
  three and serial are JSON integers `0..65,535`; release level is one of
  `alpha|beta|candidate|final`.
- `cache_tag`, `abi`, `soabi`, and `platform` are nonempty provider-independent ASCII strings
  of at most 128 bytes. `magic_number` is exactly eight lowercase hex characters encoding
  the four bytes in their observed order. `byteorder` is `little|big`; none is nullable.
- `flags` has exactly the integer-valued keys
  `bytes_warning,context_aware_warnings,debug,dev_mode,dont_write_bytecode,gil,hash_randomization,ignore_environment,inspect,int_max_str_digits,interactive,isolated,no_site,no_user_site,optimize,quiet,safe_path,thread_inherit_context,utf8_mode,verbose,warn_default_encoding`.
  Boolean-like values are encoded as integer 0|1; `optimize`, `bytes_warning`, and `verbose`
  are `0..2`; `int_max_str_digits` is `0..1,000,000`. The selected profile must report the
  exact values produced by the fixed invocation, including isolated/no-site/no-bytecode/
  safe-path/UTF-8 requirements.
- `invocation` is exactly
  `["/runtime/bin/python3","-I","-S","-B","-X","utf8","/policy/ref_update.py"]`.
  `locale` is `C.UTF-8`; `timezone` is `UTC`.
- `files` is sorted by strict UTF-8 path bytes. Each exact
  `role,path,mode,size,sha256` object has role in
  `interpreter|dynamic-loader|shared-library|stdlib-source|stdlib-extension|encoding|runtime-data`,
  a normalized relative path in the amendment-25 unquoted byte domain, regular mode
  `100644|100755`, decimal size, and lowercase prefixed SHA-256. No two rows share a path.

The existing 2 MiB manifest, 1,024-row, per/aggregate path, 128 MiB per-file, and 512 MiB
aggregate-file bounds remain. The profile verifier compares every scalar to the running
interpreter after exec; file identity is enforced by the launcher's sealed-root construction.
Independent encoders cover all release levels, flag extrema, null/wrong JSON types,
magic-number byte order, enum/key/order damage, files exact/+1, and byte-identical profiles
from two independently built roots.

### V2 result names every execution identity

The complete canonical classifier result becomes `agentfold-ref-update/v2` with exactly:

```text
schema,execution,old,new,common,state,rows,counters
```

This supersedes the v1 `policy` scalar. `execution` has exactly
`launcher_policy,runtime_profile,authority_policy,execution_policy`; all four are lowercase
`sha256:<64-hex>` strings, and `execution_policy` must recompute from the other three using
amendment 27's fixed transcript. Endpoint/state/row/counter schemas and result-size/delivery
bounds are otherwise unchanged. Minimal incomplete output remains a separate stable
diagnostic with exit 2 and is never decoded as a complete result. Every local/provider
acceptance parser requires v2 and the exact execution object; v1, a fifth digest, reordered
meaning, authority-only identity, or recomputation mismatch refuses.

The canary artifact becomes `agentfold-ref-update-canary-artifact/v3`; its exact top-level
keys are
`schema,tested_commit,execution,adapter_policy,launcher_artifact,fixture,workflow,rows,cleanup`.
The receipt becomes `agentfold-ref-update-canary-receipt/v3` with those keys plus `artifact`.
`execution` is byte/object-equal to result v2, and `adapter_policy` is one prefixed digest.
Existing fixture/workflow/row/cleanup/artifact shapes remain unless superseded here.

`launcher_artifact` has exactly
`repository_id,repository_full_name,workflow_id,workflow_path,workflow_sha,head_sha,run_id,run_attempt,conclusion,artifact_id,name,archive_size,archive_sha256,architecture,executable_mode,executable_size,executable_sha256`.
Repository/workflow/run identities use the existing attempt-specific provider grammar,
match the trusted base repository, and are re-fetched by exact run attempt; workflow/head
SHAs are full OIDs and conclusion is `success`. Name is
`agentfold-ref-update-launcher-v1-x86_64`; architecture and executable mode are the launcher
policy literals; archive/executable sizes and digests are independently bound. The archive
contains exactly one regular non-link entry `launcher` with the recorded `100755` mode and
payload; the existing safe archive grammar/caps apply. Provider metadata must bind the
artifact to that exact trusted build run/attempt and show it unexpired.

Every completed scenario result is v2 and its existing `result_sha256` hashes the full v2
line. The attempt log marker publication becomes
`agentfold-ref-update-publication/v2` and adds exactly one `execution` object to the prior
closed keys; the two per-scenario artifact names use `...-event-v2-...` and
`...-result-v2-...`. Artifact v3, receipt v3, publication v2, scenario row, downloaded result,
and Gate 3 require byte/object-equal execution identities. No field is hidden in numeric
counters or inferred from a job conclusion.

### Canary bootstrap uses manifests; activation uses the receipt

The first-run cycle is split explicitly:

1. Gate 2 lands dormant authority/adapter code, canonical launcher-policy and runtime-profile
   manifests, and the exact trusted-build `launcher_artifact` locator on the default branch.
2. The trusted default-branch canary workflow authenticates launcher/runtime against those
   base-commit manifests and locator. It does **not** require a receipt that this canary is
   being run to create.
3. The independent verifier re-fetches the build artifact and every canary attempt, validates
   the manifests and execution identities, and lands receipt v3 in a separate core-data PR.
4. Gate 3 and every activated production run require the immutable-base receipt v3, re-fetch
   its launcher artifact/provider evidence, and compare launcher/runtime/authority/adapter/
   execution values before evaluator exec. Expiry or provider failure leaves legacy
   continuity active.

A launcher/runtime update returns to step 1 with new manifests and a new canary; an old
receipt cannot start activation or production for it. Manifest trust is permitted only for
the dormant canary that creates the new receipt, never as a production substitute.

### Local placement is not local attestation

`automation/install.py` may copy a launcher and manifests into the Git common directory for
convenience, but the copy and its provenance record establish no authority. Accepted local
execution requires a **host-owned verifier** outside the repository/worktree/Git common
directory. On every invocation that verifier opens the expected launcher with no-follow,
compares it to an immutable host-configured launcher-policy digest, verifies the runtime
profile, and executes the already opened binary by trusted fd semantics. The expected digest
must come from a user-selected trusted default-branch receipt or host image, not from the
current worktree or installer output.

The host verifier may be an immutable-image/container service, fs-verity/IMA-backed runner,
or equivalent implementation of the same protocol; it is an optional local adapter and is
not installed or configured by core. Without it, local Strategy A authority is explicitly
unavailable. A direct staged-launcher command may be documented only as untrusted diagnostic
output and cannot satisfy parity, clear a remote unavailable edge, produce a receipt, or be
accepted by activation. Tests replace the installer, staged binary, provenance record,
expected digest, and binary between verification and exec; only the host-rooted fd execution
can yield an accepted v2 result.

### Sealed-root membership replaces future mapping enumeration

The launcher no longer claims to observe mappings that `execve` has not created. Before
pivot it verifies every runtime-profile file and constructs a private root containing no
other regular file or symlink. Policy, Git-object, and scratch mounts are `nodev,nosuid,noexec`;
runtime is immutable read-only `nodev,nosuid` and is the only executable/file-loader search
root. Loader configuration, absolute dependency paths, invocation path, and sanitized
environment resolve only inside `/runtime`. The original host root is detached before exec.

Consequently CPython's dynamic loader and allowed extension imports can map only files that
already have runtime-profile rows. The evaluator validates scalar `sys`/flag/profile values
and the closed preloaded module names after startup, then removes late filesystem importers;
it does not enumerate native mappings through absent `/proc`. Anonymous mappings, the kernel
vDSO, and already authenticated executable pages are not runtime files and are not falsely
represented as manifest rows. A path resolution outside runtime, late `dlopen`, new file in
the sealed root, writable/remounted runtime, or loader-environment influence is unavailable.
Tests add each unlisted library/config/search path and require failure at construction or
load rather than a post-hoc mapping claim.

### Gate boundary

Production remains unopened. All execution/evidence schemas and trust paths changed, so one
new immutable SHA needs the three base lenses before budget and core-fit review.

## 2026-09-01 correction amendment 29 — durable sealed execution and attempt binding

Fresh read-only review of `c58b038c0e47e10ae0f2c495b1b2100ff3937fb3`
rejected six executable gaps: ordinary release CPython has an empty ABI-flags string; the
launcher manifest's valid representation could not reach its promised 64 KiB boundary;
the exact argument vector omitted `argv[0]`; an open descriptor did not prevent same-inode
mutation between hashing and execution; a rerun's artifact was not bound to its producing
attempt; and activated production depended forever on a retention-bounded provider
artifact even though activation removed the legacy fallback. This amendment supersedes the
affected amendment-28 launcher/runtime, artifact/receipt, bootstrap, and local-execution
clauses. The classifier semantics and result-v2 envelope do not change.

### Launcher policy binds a complete invocation and reachable byte limits

The `launcher-policy/v1` `argv_schema` is the complete `execve` argument array, including
the fixed literal `argv[0]`:

```text
["agentfold-ref-update-launcher","--authority-manifest-fd=3","--runtime-manifest-fd=4","--git-dir-fd=5","--old=<full-oid>","--new=<full-oid>"]
```

No caller-supplied program name is admitted. The launcher refuses a different element,
count, order, duplicate option, missing option, embedded NUL, or placeholder substitution
outside the two endpoint elements. The exact sorted `kernel_capabilities` array becomes
`close-range,execveat,memfd-sealing,mount-namespace,pivot-root,private-propagation,read-only-bind,sealed-tmpfs,user-namespace`.

The raw launcher-policy read ceiling is 1,024 bytes including LF. Under the closed schema,
fixed strings, fixed digest width, and executable size `1..16,777,216`, the largest valid
canonical representation is exactly 578 bytes including LF. An independent encoder must
produce that 578-byte vector. A 1,024-byte raw input is a bounded malformed-input case that
must be read completely and then fail canonical/schema validation; a 1,025-byte input must
refuse during bounded read before JSON decode. Neither is described as a schema-valid
boundary. Valid minimum/maximum executable-size vectors, every single-field mutation, and
the raw 1,024/1,025 damage pair replace amendment 28's unreachable 65,536-byte valid case.

### Runtime ABI has one real CPython meaning

`runtime-profile/v1.abi` is exactly the ASCII value of `sys.abiflags` observed under the
fixed invocation. It is the sole authoritative extractor; `sysconfig` is not allowed to
substitute another ABI label. Empty is valid and encoded as the JSON string `""`; nonempty
values remain limited to 128 provider-independent ASCII bytes. `cache_tag`, `soabi`, and
`platform` remain nonempty. The evaluator compares `abi` byte-for-byte with `sys.abiflags`.
Golden profiles include an ordinary release build with empty ABI flags and a separately
constructed supported build with a nonempty value; null, omission, non-ASCII, 129 bytes,
or a disagreement with the running interpreter refuses.

### Accepted execution always uses an immutable sealed copy

No accepted provider, activation, production, or local path executes a regular-file
descriptor merely because that descriptor was hashed. Its trusted verifier instead performs
this exact single-threaded protocol before every launcher start:

1. open the selected source with no-follow and verify its type, mode, exact length, and
   digest while streaming under the launcher setup limits;
2. create a fresh anonymous executable memfd with sealing enabled, without exporting,
   duplicating, or mapping it; copy exactly the declared bytes while independently hashing
   the copy, then require EOF on the source;
3. require both source and copy hashes and lengths to equal the selected policy/source;
   set the memfd executable mode, add `F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL`,
   and read the seals back exactly;
4. close the mutable source and execute only the sealed memfd with `execveat(..., "", argv,
   empty_env, AT_EMPTY_PATH)` and the complete argument vector above.

On kernels that distinguish executable memfds, the verifier requests the executable form
at creation. Absence of memfd sealing, executable memfd, or `execveat` is unavailable, not a
weaker fallback. It never executes through a pathname or the original descriptor. Creation,
copy, hashing, sealing, mode, and exec-status descriptors are included in the existing
descriptor, time, memory, diagnostic, and cleanup envelopes.

Damage controls overwrite the source by rename and in place before and during copy, retain
a pre-existing writable mapping, attempt write/truncate/grow after sealing, alter mode or
length, exhaust each memfd/exec operation, and interrupt between every two stages. Mutation
before or during copy refuses; post-seal mutation is rejected by the kernel; only the sealed
digest-equal copy may start. Every refusal closes the memfd and leaves no child or mount.

### The durable launcher source is repository data

Gate 2 commits the exact launcher payload as a regular executable Git blob at the fixed path
automation/runtime/launchers/x86_64-linux-gnu/agentfold-ref-update-launcher. It is dormant
repository data, not authority by its location. `launcher_source` has exactly
`path,mode,blob_oid,size,sha256`: the path is that literal, mode is `100755`, `blob_oid` is a
lowercase full non-zero object-format OID, size is `1..16,777,216`, and SHA-256 is the
launcher-policy executable digest. Git blob type, OID, bytes, mode, size, and digest are all
verified from the immutable trusted base before the sealed-copy protocol.

The canary artifact and receipt become
`agentfold-ref-update-canary-artifact/v4` and
`agentfold-ref-update-canary-receipt/v4`. Their exact top-level keys are respectively
`schema,tested_commit,execution,adapter_policy,launcher_source,launcher_artifact,fixture,workflow,rows,cleanup`
and those keys plus `artifact`. The new `launcher_source` object is byte/object-equal across
the trusted base, every scenario result bundle, the aggregate artifact, the independent
verification, the receipt, and Gate 3. V3 artifacts/receipts cannot activate V4 code.

Before activation, the trusted canary reads the launcher blob from its immutable Gate-2
base, verifies it against both manifests, copies it into a sealed memfd, and executes that
copy. Receipt creation and Gate 3 additionally re-fetch and validate the provider artifact
described below. Activation may retire the legacy path only when the base receipt and the
base-tree `launcher_source` match and the activation patch does not change the source,
receipt, manifests, or any digest-covered byte.

After activation, every production update reads the source from its immutable old/base Git
tree and verifies it against receipt V4 before sealed execution. It does not contact the
provider artifact API and does not depend on artifact retention. A missing, non-blob,
wrong-mode, wrong-OID, wrong-size, or wrong-digest source is a stable unavailable result that
fails the continuity gate closed; it cannot silently use current-worktree bytes. Provider
artifact expiry after activation is therefore irrelevant to W0/P1/P2/P3 protection. A
launcher/runtime update repeats dormant Gate 2, canary, receipt, and Gate 3 with a new V4
identity.

### A launcher artifact is bound to the producing attempt

Amendment 28's `launcher_artifact` object adds exact fields
`job_id,job_name,publication_sha256`. `job_id` is a positive provider integer; `job_name` is
the fixed trusted-workflow job name `build-launcher`; and `publication_sha256` is a lowercase
prefixed digest. The independent verifier queries the provider's jobs-for-workflow-run-
attempt endpoint for the exact `run_id,run_attempt`, requires exactly one completed
successful job with that ID/name and the trusted head/workflow identity, and downloads that
job's log.

Only after the upload action returns its artifact ID and digest, the trusted job emits
exactly one LF-terminated canonical marker `agentfold-launcher-publication/v1`. Its exact
keys are
`schema,repository_id,workflow_id,workflow_sha,head_sha,run_id,run_attempt,job_id,job_name,artifact_id,name,archive_sha256,architecture,executable_mode,executable_size,executable_sha256,launcher_source`.
Every value is byte/object-equal to the locator, trusted job, manifest, and base source;
`publication_sha256` hashes the complete canonical marker. The artifact API independently
supplies and validates archive size, expiry, workflow-run ID, repository, head, name, ID,
and digest. The log marker supplies the missing attempt-specific join; neither source alone
is sufficient.

A run-ID replay from attempt 1 into attempt 2, a marker before upload, two matching jobs or
markers, wrong logical job name, artifact replacement, absent log, expired artifact during
receipt/Gate 3, and any locator/marker/API disagreement refuse. Artifact expiry remains a
pre-activation refusal only; it cannot invalidate an already activated durable V4 source.

### Gate boundary

Production remains unopened. Amendment 29 changes launcher bytes, kernel requirements,
artifact/receipt schemas, and lifecycle behavior. One new immutable revision must receive
all three base-lens accepts before budget and core-fit review; no verdict on an earlier SHA
transfers.

## 2026-09-01 correction amendment 30 — immutable deployment slots and control-plane selection

Fresh review of `305fbadf783e0bb2827843cc57de1790215fd9bd` accepted the
classifier and sealed-execution chain but rejected four composition gaps. A task branch's
old tip can predate Gate 2 and therefore cannot select the launcher; a later dormant Gate 2
would overwrite the one active launcher/manifest/receipt location; `launcher_source` was
required in an undefined per-scenario bundle that cannot exist under result v2; and the new
build-job log scan had no byte/token/deadline envelope. This amendment supersedes amendment
29's source-selection, V4 artifact/receipt, scenario-bundle, build-publication, and upgrade
wording. O/N graph semantics and result v2 remain unchanged.

### Execution control plane is independent of classified O/N

Define `A` as the immutable control-plane commit already authenticated by the role's trusted
workflow/host boundary. For an accepted provider run, `A` is the exact trusted default-
branch workflow/adapter checkout commit after the existing repository, workflow path/ref,
numeric-ID, and `github.workflow_sha` checks. For an accepted local run, `A` and the active-
selector digest are explicit host-owned configuration selected from a trusted default-
branch receipt or immutable host image. A candidate-controlled workflow or direct checkout
has no accepted `A` and remains advisory/untrusted as already specified.

The fixed active-selector path is
automation/runtime/ref-update/active.json. Its canonical JSON-plus-LF has exactly
`schema,slot_id,execution_policy,adapter_policy,receipt_path`:

- `schema` is `agentfold-ref-update-active/v1`;
- `slot_id` is exactly 32 lowercase hex characters, not all zero;
- both policies are lowercase prefixed SHA-256 values; and
- `receipt_path` is exactly
  `automation/canaries/receipts/ref-update/<slot_id>.json`, with the same literal slot ID.

The raw selector ceiling is 1,024 bytes including LF. Its fields have the bounds above;
canonical decode/re-encode, exact field order/meaning, missing/extra/duplicate keys, every
digest/slot/path mutation, and raw 1,024/1,025-byte damage inputs are tested. The exact
selector bytes are known at Gate 2 and included in the authenticated activation patch even
though the selector is not installed yet.

An accepted production run reads the selector and named receipt only from `A`, then defines
`T = receipt.tested_commit`. It reads launcher, runtime, authority, and adapter source blobs
only from exact commit `T`, after verifying their path/mode/blob-OID/size/digest contracts.
`O`, `N`, `B`, `C`, the event head, and the current worktree never select executable bytes.
They remain only the unchanged Strategy A and ordinary-check data-plane inputs. If `A`, its
selector/receipt, `T`, or a selected object is missing or mismatched, accepted continuity is
unavailable and fails closed; it never falls back to O/N/current bytes.

This rule covers the central migration case: a task tip `O` created before Gate 2 is still
classified after activation by the control plane selected from `A` and `T`. The old tip need
not contain any launcher path. Stale trusted reruns use their original authenticated `A`,
selector, receipt, and retained `T`; they do not silently adopt a later active slot.

`T` must be a commit in the same authenticated base repository and an ancestor of `A`.
The verifier proves this with one supervised, no-replace, configuration-closed
`merge-base --is-ancestor T A` child under the existing 512 MiB/30-second child envelope;
missing objects, exit 1 for non-ancestry, any other nonzero exit, budget exhaustion, or an
unrelated/detached commit is unavailable. A provider adapter may obtain exact missing T
objects only through the existing bounded read-only base-repository transport. It cannot
fetch from the candidate or
a fork and cannot follow a moving ref.

The host verifier resolves the launcher without a worktree. In a sanitized base object
database it runs one literal-path `ls-tree -z --full-tree T -- <exact-source-path>` and
requires exactly one default-format NUL record with mode `100755`, type `blob`, and the
receipt OID. With a 64-hex object ID and the inherited 4,096-byte path limit, the record cap
is 4,174 bytes including NUL; byte 4,175 refuses. It then uses one no-replace
`cat-file --batch-command --buffer` child admitting only `info <oid>\n`,
`contents <oid>\n`, and `flush\n`. The largest launcher response is a 79-byte header,
16,777,216-byte payload, and one delimiter byte: 16,777,296 bytes; byte 16,777,297 refuses.
The payload streams directly into amendment 29's fresh memfd and is independently hashed.

An ancestry, tree, or batch child never overlaps another Git child. The extraction peak is
the 256 MiB verifier plus one 512 MiB child; stdout/stderr, 64 KiB chunks, monotonic
deadlines, process groups, descriptors, overrun bytes, EOF, termination/reaping, and partial
memfd cleanup use the existing launcher/child envelopes. Before sealed exec, the verifier
closes its base object database and supplies fd 5 only as the already isolated exact-object
source whose role table contains authenticated T plus the separately named O/N data objects.
The launcher may read authority rows only at T and classifier objects only at O/N; equal
object IDs do not merge those roles.

### Every deployment is a create-once opaque slot

A slot ID is chosen before its path-bound authority and adapter digests are computed. It is
an opaque namespace, not a content digest: making it a digest of policies whose transcripts
contain repository paths would be circular. The repository rejects an all-zero ID, a reused
ID, or any Gate-2 diff that modifies a pre-existing slot or receipt.

All Gate-2 executable/configuration/template bytes that may vary live below the literal
root pattern automation/runtime/ref-update/slots/<slot_id>/, including the launcher,
launcher/runtime manifests, authority sources, adapter sources, and dormant workflow and
activation templates. Every existing authority/adapter manifest row uses those physical
slot paths, so the chosen ID is already covered by their path framing. The result execution
digests retain their existing algorithms; no self-referential deployment digest is added.

The canary artifact and receipt become
`agentfold-ref-update-canary-artifact/v5` and
`agentfold-ref-update-canary-receipt/v5`. Their exact top-level keys are respectively
`schema,deployment,tested_commit,execution,adapter_policy,launcher_source,launcher_artifact,fixture,workflow,rows,cleanup`
and those keys plus `artifact`. `deployment` has exactly
`slot_id,selector_sha256,receipt_path`; slot/path match the grammar above, and the digest
hashes the complete future canonical active-selector bytes. `tested_commit` is the Gate-2
commit `T`. `launcher_source.path` must be below that slot root; its existing exact
`path,mode,blob_oid,size,sha256` shape is unchanged and is always resolved in `T`.

V4 cannot activate V5 code. V5 deployment, execution, adapter, source, tested-commit, and
selector values are byte/object-equal across the aggregate artifact, independent verifier,
receipt, launcher publication, and Gate 3. The receipt verifier proves that every source
object exists with the named identity in `T` and that neither the slot nor receipt path
existed with different bytes in any accepted prior deployment.

Initial activation is exactly:

1. Gate 2 adds one new slot; the active selector remains absent and legacy continuity stays
   active.
2. The canary explicitly selects that slot from `T` and never consults an active selector.
3. The records-only PR adds only that slot's V5 receipt; it does not add the selector.
4. Gate 3 reads slot and receipt from its immutable base `A`, reconstructs the exact
   canaried candidate, and validates the candidate selector against `selector_sha256`.
5. One atomic activation creates the selector, installs the canaried live workflow, and
   removes legacy continuity. Any partial or additional change refuses.

A future upgrade uses the same sequence additively: Gate 2 adds a new slot while the old
slot, old receipt, and active selector remain byte-identical; canary and receipt explicitly
target the new slot; existing production continues to select the old slot; and Gate 3
atomically switches only the selector plus any exact canaried live-template transition.
Old slots and receipts are retained. Deleting them is outside this task and requires a
separate retention proof, so in-flight events and stale trusted reruns cannot lose their
control plane during an upgrade.

Candidate-after preservation is separate from source selection. Ordinary changes may not
edit the active selector, an active slot, or its receipt. Gate 3 is the sole transition that
may change the selector, and its candidate manifest proves the exact before/after selector,
live template, and all other activation bytes before the ref can retire or switch authority.

### Per-scenario result remains result v2

The phrase “every scenario result bundle” is withdrawn; no such schema exists. Each
per-scenario archive still contains exactly one `result.json` with unchanged result-v2
keys. Its `execution.launcher_policy` and other execution digests must equal the V5
aggregate/receipt execution object, and scenario publication v2 continues to bind that
object. `launcher_source` and `deployment` occur only in the V5 aggregate artifact/receipt
and launcher publication, where the independent verifier joins their source bytes to the
same launcher-policy digest. An added sidecar, a launcher-source field in result v2, or a
second archive entry refuses.

### Build-attempt publication has the same bounded log grammar

The launcher build marker becomes `agentfold-launcher-publication/v2` by adding exactly one
`deployment` object to amendment 29's closed publication keys. The job emits exactly this
outer line only after upload succeeds:

```text
AGENTFOLD_REF_UPDATE_LAUNCHER_PUBLICATION_V2 <unpadded-base64url(canonical-publication-JSON)>\n
```

Canonical publication JSON includes one LF and has a 65,536-byte raw ceiling. The unpadded
token is at most 87,382 ASCII bytes and the whole marker line at most 87,428 bytes. The
verifier streams at most 8 MiB from the exact build job log, bringing the complete scenario
plus build-log aggregate to 72 MiB, and stays inside the existing 15-minute provider-
verification deadline. It does not retain unrelated log bytes. The literal marker must be
delimited by LF or CRLF; no timestamp/presentation byte may split or enter the prefix or
token. The verifier requires exactly one marker, refuses an overlong token before decode,
decodes/re-encodes canonical base64url and JSON, hashes the complete canonical JSON, and
matches every deployment, job, attempt, artifact, source, and policy field.

Tests place one valid marker at the end of an exact 8 MiB log, reject byte 8 MiB + 1 before
further scanning, exercise token lengths 87,382/87,383 and decoded raw inputs
65,536/65,537, duplicate/split/CRLF markers, invalid base64/UTF-8/JSON, a stalled download at
each boundary, and aggregate byte/deadline exhaustion. Raw exact-cap inputs may fail the
closed publication schema after bounded decode; they are not claimed to be schema-valid
objects. Every refusal closes the response, discards partial evidence, and cannot create a
receipt or alter cleanup.

### Gate boundary

Production remains unopened. Amendment 30 changes control-plane selection, all deployment
paths, selector/source invariants, canary/receipt V5, and launcher publication V2. One new
immutable revision requires all three base-lens accepts before the budget and core-fit
lenses; no earlier vote transfers.

## 2026-09-01 correction amendment 31 — T-only authority and physically split object sources

Fresh review of `6e5978cdf17207b62365abf75e37488e6cef1481` rejected eight
cross-layer contradictions. The old O/N/evaluator policy-file rule made the advertised
pre-Gate-2 migration impossible; a shared fd 5 could not enforce T-versus-candidate object
roles; the selector's adapter digest hashed a patch containing that same digest; deployment
manifests had no locators or aggregate extraction budget; an ordinary commit could change
the live workflow without changing the active slot; launcher publication lacked fields its
join required; receipt landing regressed to records-only; and maximum-token CRLF exceeded
the stated line cap. This amendment supersedes those authority, selector, source-discovery,
FD, V5/V2 evidence, live-projection, receipt-lane, and log-framing clauses. Strategy A's
bounded O/N graph and classification rules remain unchanged for data admitted by the active
policy.

### The selector is not self-referential

The active selector becomes the pointer-only `agentfold-ref-update-active/v2` with exactly
`schema,slot_id,receipt_path`. All policy and receipt-derived digests are removed. Execution
and adapter policies are read from and verified through the selector-named receipt, so the
exact selector can be constructed at Gate 2 without solving a digest equation whose input
contains itself. The fixed selector and receipt paths, opaque slot grammar, canonical
encoder, 1,024-byte raw ceiling, and 1,024/1,025 raw damage pair otherwise remain amendment
30's. Every valid V2 selector is exactly 184 bytes including LF; its independent golden
vector and both raw containment cases are required. V1 selectors refuse.

The canary artifact and receipt become
`agentfold-ref-update-canary-artifact/v6` and
`agentfold-ref-update-canary-receipt/v6`. Their exact top-level keys remain amendment 30's
V5 keys. `deployment` now has exactly
`slot_id,selector_sha256,receipt_path,slot_index`. The selector digest hashes the complete
future V2 selector; receipt `execution` and `adapter_policy` supply all policy values omitted
from it. Production hashes the selector, requires equality with
`deployment.selector_sha256`, and requires its path/slot to equal the receipt. V4/V5
artifacts or receipts and V1 selectors cannot activate or run V6.

### One index and four fixed manifests close a slot

For slot root automation/runtime/ref-update/slots/<slot_id>/, these paths are exact:

```text
slot-index.json
launcher
launcher-policy.json
runtime-profile.json
authority-manifest.json
adapter-manifest.json
```

Each is prefixed by the exact slot root; no alternate name or second instance is admitted.
`slot-index.json` is canonical JSON plus LF, schema
`agentfold-ref-update-slot-index/v1`, raw cap 8,192 bytes, and exact keys
`schema,slot_id,execution,adapter_policy,objects`. Execution is the complete result-v2
object. `objects` has exactly
`launcher,launcher_policy,runtime_profile,authority_manifest,adapter_manifest`; each value
has exactly `path,mode,blob_oid,size,sha256`. Paths equal the fixed literals above. Launcher
mode is `100755`; all four manifest modes are `100644`; OIDs/sizes/digests retain their
closed types. The index does not contain its own locator, selector/receipt/T, or another
derived pointer.

`deployment.slot_index` is the exact locator for `slot-index.json`, with keys
`path,mode,blob_oid,size,sha256`, mode `100644`, size `1..8,192`, and the same strict
identity types. The locator is byte/object-equal across artifact, receipt, launcher
publication, and Gate 3. `launcher_source` must equal `slot_index.objects.launcher`.

`authority-manifest.json` has exactly
`schema,slot_id,authority_policy,files`; `adapter-manifest.json` has exactly
`schema,slot_id,authority_policy,adapter_policy,files`. Their schemas are respectively
`agentfold-ref-update-authority-manifest/v1` and
`agentfold-ref-update-adapter-manifest/v1`. Each file locator has exactly
`role,path,mode,blob_oid,size,sha256`. Adapter rows additionally have exactly
`category,live_path`; category is
`activation-patch|activation-manifest|other`, and `live_path` is JSON null or one normalized
repository path. Every adapter byte executable before sealed launch has one non-null unique
live path; dormant templates/data remain null. Role is one unique member of the existing
fixed registry. Authority paths are below the same slot's authority/ directory and adapter
paths below its adapter/ directory; no path/OID can satisfy two roles or cross the two
namespaces. Rows appear in the exact pre-existing fixed role-registry order used by the V2
digest transcript; role names map one-to-one to those ordinals, and path bytes do not define
a second ordering.

Authority retains 1..32 rows, 4,096 bytes per path, 8,192 aggregate path bytes, and 4 MiB
aggregate payload. Adapter retains 1..16 rows, 4,096 bytes per path, 4,096 aggregate path
bytes, a separate 4,096 aggregate non-null live-path bytes, 27,262,976 aggregate payload
bytes, and the existing mutually exclusive category limits. Both locator manifests have a
65,536-byte raw cap including LF. Launcher policy
retains its raw 1,024-byte cap and runtime profile its 2 MiB cap. Exact raw manifest caps may
be malformed containment inputs; independent valid-schema exact/+1 tests stay on the source
count/path/payload/category gates.

Authority-policy/v2 is recomputed from the authority manifest's exact path/mode/payload
rows. Adapter-policy/v2 is recomputed from its rows and embedded authority digest. Launcher
and runtime objects decode to their closed manifests and match index/receipt execution.
Slot index and locator manifests are deployment metadata, not members of their own policy
row transcripts; their identities are instead bound by T plus index/receipt locators. This
expressly supersedes any earlier claim that those metadata files self-enter adapter-policy
membership. Unknown, missing, duplicate, aliased, unlisted, or policy-mismatched rows refuse;
searching the slot directory is forbidden.

### T is the only authority-policy source

Amendments 3 and 25 required authority files and an equal policy digest independently at O,
N, and the evaluator. That rule is withdrawn. Neither O nor N is an executable-policy
source, and neither is required to contain a slot, manifest, authority file, or active
selector. For every accepted edge the sole authority policy is recomputed from the V6
receipt's source manifest and blobs at exact `T`, then compared to receipt execution and the
sealed evaluator bytes made from those same T blobs.

`policy-version-mismatch` now means only that T source, source-manifest recomputation,
receipt execution, sealed evaluator, or active-selector execution disagree. A policy-looking
file added, removed, or changed at O/N is inert data and cannot affect execution; the active
slot guard separately prevents an ordinary default-branch change from becoming authority.
The build/import audit still rejects any T authority dependency outside its closed manifest.

One required authority role is the closed historical-data-contract registry. It contains
ordered named predicates and parsers for queue/task/evidence bytes, not executable paths in
O/N. The initial slot includes `pre-slot-v1`, whose fixtures are the exact current
pre-Gate-2 repository schemas and path conventions. A historical object must match exactly
one admitted contract before semantic parsing; zero or multiple matches yield
`unsupported-policy-history`. Registry names/order/parser bytes are authority-policy rows,
so adding, dropping, or reinterpreting a contract requires a new slot/canary/activation.
Damage tests relabel data, satisfy two predicates, remove required version evidence, and
change only O/N policy-looking files; none can silently select executable semantics.

This replacement is mandatory for the initial migration. Canary scenarios include an O
created before Gate 2 with no slot or policy source and an N after activation, across W0,
P1, P2, and P3; outputs must equal the accepted POC's clean/blocked results. Presence/absence
of policy-looking paths in any of O-only, N-only, both, or neither is varied and cannot
change one result byte. Ordinary checks continue to inspect their own ranges independently.

A future selector switch is the explicit policy-version boundary. Gate 3 validates that
transition under the old active control plane, then later edges use only the new T. Because
backward compatibility is not promised, historical queue data outside the new policy's
closed input grammar returns stable `unsupported-policy-history` unavailable before graph
work and fails continuity closed; it never falls back to an old or O/N evaluator. Stale
provider reruns keep their original A/selector/T and therefore remain reproducible. Human
instructions distinguish this actionable migration refusal from a deletion Finding and
require a reviewed data migration or an explicitly pinned old-slot diagnostic; neither may
clear the remote gate automatically.

Removing two historical policy recomputations changes the derived authority work. One T
manifest reaches framing `30 + 2 + 32*30 + 8,192 = 9,184`, payload `4,194,304`, and total
digest input `4,203,488`. These supersede the three-source observations 27,552, 12,582,912,
and 12,610,464. Independent source gates remain 32 rows, 8,192 path bytes, and 4 MiB payload;
derived maxima use unchanged-maximum observed-minus-one controls, not independent `+1`.
Adapter framing `4,649`, payload `27,262,976`, and total `27,267,625` remain unchanged.

### Control and candidate objects are physically separate capabilities

The complete launcher-policy argv becomes:

```text
["agentfold-ref-update-launcher","--authority-manifest-fd=3","--runtime-manifest-fd=4","--control-git-dir-fd=5","--candidate-git-dir-fd=6","--tested-commit=<full-oid>","--old=<full-oid>","--new=<full-oid>"]
```

The tested-commit placeholder is replaced exactly once by T. Old/new retain their existing
full-OID rules. This full array's maximum canonical launcher-policy representation is 642
bytes including LF, and maximum actual argument-string storage is 351 bytes including each
element's NUL. The raw 1,024/1,025 envelope and all argument mutation tests remain. The old
single `--git-dir-fd=5` spelling and 578/636-byte vectors refuse.

Fd 5 names a sanitized read-only object database fetched only from the authenticated base
repository and containing only the reduced T/authority control objects described below.
Fd 6 names a physically separate sanitized
read-only database fetched only from the event-named candidate repository and containing
the exact O/N candidate closure. Neither database has alternates, replacements, refs,
hardlinks, shared writable packs, environment/config inheritance, or a path/descriptor to
the other. Missing candidate objects cannot be satisfied from control even when the same
OID exists there.

The static launcher uses only fd 5 and T while verifying the authority manifest and
constructing its sealed policy directory. It then terminates/reaps that Git child, closes
fd 5 and every control descriptor, detaches the control mount, and only afterward exposes
fd 6 to the evaluator. Evaluator/classifier Git commands accept only fd 6 and O/N. No role
table exists or is needed. Tests omit an O/N object that exists under T, swap fd 5/6, add an
alternate/hardlink/shared pack, retain a control descriptor, and request T through the
candidate child; every case refuses or remains missing exactly as the candidate-only oracle.

The control loose-object reservation is at most 4,327,488 bytes for 32 rows/4 MiB and is
charged separately from the 4,194,304-byte sealed authority copy. The split phase enforces
`RLIMIT_NOFILE=32`, one live Git child, a 1 GiB cgroup with swap disabled and `pids.max=4`,
and the existing per-process address-space/pipe/output limits. The descriptor registry adds
fd 6 explicitly and requires every unspecified descriptor closed before child exec; a
test-only observed-open-count minus one must fail the unchanged maximum phase. Every
refusal kills/reaps the child group, closes both role capabilities and partial memfds,
empties the control ODB/policy volume, unmounts them, and proves zero descendant/residue.

### Deployment extraction is bounded as one closed inventory

T extraction has three sequential stages: slot index, its five fixed objects, then the 48
source rows. The closed set has 54 objects total. For each stage the verifier first fchdirs
to the already-open control ODB and runs a no-replace, literal-path
`ls-tree -z --full-tree T -- <sorted-exact-paths>` child. It requires one default-format
record per requested path in the same order and no extra record. With 78 bytes of record
overhead, 521 fixed-path bytes, and the 8,192/4,096 source-path aggregates, cumulative tree
output is bounded by `54*78 + 521 + 8,192 + 4,096 = 17,021` bytes. The existing 4,174-byte
per-record/4,175 refusal remains.

Each stage then starts and fully reaps one no-replace
`cat-file --batch-command --buffer` child. It sends every `info` command then one `flush`,
validates and precharges the stage, and only then sends every `contents` command plus one
`flush`. Across all stages, request bytes are
`54*70 + 54*74 + 6*6 = 7,812`. Each info/contents response uses the conservative 79-byte
header and each content has one delimiter.

Independent body ceilings are 8,192 slot index; 1,024 launcher policy; 2,097,152 runtime
profile; 65,536 each authority/adapter manifest; 4,194,304 authority sources; 27,262,976
adapter sources; and 16,777,216 launcher. Their source-derived body sum is 50,471,936 bytes;
including 54 pairs of response headers plus delimiters yields a transcript containment
ceiling of 50,480,522 bytes. Byte 50,480,523 terminates the child. These sums are not new
schema-valid `+1` promises: the independent source limits keep exact/+1 tests, while the
unchanged maximum transcript runs with an observed-minus-one total.

Tree and batch output are streamed; only decoded index/manifest metadata, one 64 KiB chunk,
bounded diagnostics, and the already charged destination are retained. Adapter bytes are
verified but not copied into the launcher's 16 MiB sealed policy volume. Authority payload,
its locator manifest, and the closed policy copy fit that volume; launcher memfd and
read-only runtime files use separately charged storage. An ancestry child, three tree
children, and three batch children are seven sequential Git children: one-shot limits are
30 seconds, each batch exchange 10 seconds, and the control-extraction aggregate is 210
seconds including 30 seconds setup/cleanup. One 512 MiB child may overlap the 256 MiB
verifier; no two children overlap. Counts 54/55, partial headers, early/late EOF, every
per-file/source cap, both observed-minus-one totals, deadlines, termination/reaping,
descriptor closure, partial memfd/policy cleanup, and scratch residue are golden cases.

The 50 MiB-class traversal occurs in the outer authenticated base ODB and is charged to the
existing 128 MiB extracted-provider/control-source allowance. After it verifies adapter and
deployment bytes, the host constructs a fresh reduced control ODB containing T's required
commit/tree objects plus only the authority rows named by fd 3; its loose-object
reservation is the 4,327,488-byte value above. It verifies that reduced source independently,
destroys/unmounts the outer base ODB, and only then seals/executes the launcher with reduced
fd 5. Candidate fd 6 is constructed separately and is never an alternate or copy source for
either base ODB.

### A includes the exact active live adapter projection

Repository/workflow position and `github.workflow_sha` are necessary but no longer
sufficient to authenticate A. The adapter source manifest at T has unique required roles
for activation manifest/patch, installed live workflow, event/O/N extraction, object
transport, result acceptance, action metadata, and every live helper. The rows with
non-null `live_path` are the exact active projection; the activation manifest's after rows
must install the same source blob/mode at each one and may additionally carry non-executable
contract/test/documentation transitions.

Before any result can be accepted, the trusted adapter and independent verifier require
every active-projection live path/mode/blob in A to equal its T source row and recompute the
receipt adapter digest. A projection mismatch is adapter-unavailable before event bytes can
authorize a result; artifacts/status emitted by mismatched workflow bytes are untrusted.
The reconciler/core-scope/source guard applies the same comparison to every default-branch
candidate: ordinary PRs may not edit selector, active slot, active receipt, live workflow,
event extraction, result acceptance, launch behavior, or another projection row. Only an
exact Gate-3 activation transition may change them.

Future Gate 2 stores new templates under a dormant slot and leaves A's active projection
unchanged. Gate 3 atomically switches selector and every changed live row to the new
receipt's canaried after projection. A later ordinary default-branch commit with different
live bytes is not an authenticated A even when repository/ref/workflow position matches.
Tests change each live row independently, change only mode, add an unlisted live helper,
emit forged artifacts from mismatched workflow bytes, and race A after event capture; none
can produce an accepted continuity result.

Projection validation uses one separate A-tree `ls-tree -z --full-tree` child after T
manifest verification and before event acceptance. At most 16 rows plus 4,096 live-path
bytes yield `16*78 + 4,096 = 5,344` bytes; byte 5,345, a missing/extra/reordered row, or any
mode/OID mismatch refuses. No projection payload is reread: equality to the already hashed
T source blob OID plus repository object-format verification is the byte identity. The child
uses the same 30-second/512 MiB/cleanup envelope and never overlaps extraction or candidate
children.

### V6 evidence and launcher publication V3 are representable

Launcher publication becomes `agentfold-launcher-publication/v3` with exactly these keys:

```text
schema,deployment,tested_commit,execution,adapter_policy,
repository_id,repository_full_name,workflow_id,workflow_path,workflow_sha,head_sha,
run_id,run_attempt,job_id,job_name,artifact_id,name,archive_sha256,
architecture,executable_mode,executable_size,executable_sha256,launcher_source
```

Schema is the V3 literal. `deployment`, `execution`, `adapter_policy`, `tested_commit`, and
`launcher_source` are now actually present and byte/object-equal to V6. Provider/job/artifact
fields keep amendment 29's types and joins; conclusion/archive size remain independently
validated from provider metadata after the job completes rather than fabricated in the
post-upload marker. V1/V2 markers cannot satisfy V6.

V6 withdraws amendment 28's claim that Gate 2 can land a future provider artifact locator.
Gate 2 knows no run/job/artifact IDs. Its trusted canary build job runs at exact head T,
reads the launcher source/index/manifests from T, uploads only the verified payload, then
emits publication V3. Therefore publication `head_sha` and `tested_commit` both equal T;
the aggregate artifact is the first object allowed to carry the resulting locator. The
independent core-data verifier re-fetches and proves that locator before writing the V6
receipt. This ordering has neither a future-ID placeholder nor a receipt bootstrap cycle.

The outer prefix becomes `AGENTFOLD_REF_UPDATE_LAUNCHER_PUBLICATION_V3 `. Decoded raw/token
caps remain 65,536/87,382 bytes. Prefix plus token is at most 87,427 bytes; accepted LF and
CRLF observed lines are separately capped at 87,428 and 87,429 bytes. The scanner's stored
token cap remains 87,382, so CRLF consumes no extra retained token memory. Exact maximum LF,
maximum CRLF, byte 87,430, token `+1`, raw `+1`, duplicate/split markers, and the existing
8 MiB log/72 MiB aggregate/deadline cases are independent fixtures.

Receipt landing is a tested **core-data PR**, not records-only. It may add only the new V6
receipt in its runtime projection, but it runs core-scope, schema, provider-reverification,
cold-clone, selector, manifest/source, live-projection, and provenance tests before becoming
Gate 3's immutable base.

### Gate boundary

Production remains unopened. Amendment 31 changes active selector V2, artifact/receipt V6,
launcher publication V3, policy selection/budgets, launcher argv, object-source topology,
deployment manifests, and active adapter admission. One new immutable revision requires all
three base-lens accepts before budget and core-fit review; no earlier vote transfers.

## 2026-09-01 correction amendment 32 — external acceptance and acyclic projections

Fresh review of `33b52f95e166ed74067f5d9427e9a24c5bf65d27` rejected the
deployment rather than Strategy A. A repository workflow could execute before proving its
own A projection; the first canary could not match a production projection that Gate 3 had
not installed; the reduced control ODB had no commit/tree budget; one 1 GiB scope could not
contain the evaluator's admitted process topology; a projection lookup still interpreted
pathspec magic; the manifest referred to registries that did not exist; result v2 retained
three-source counters; and a breaking selector switch could strand old live edges. This
amendment supersedes amendment 31's acceptance authority, single live projection, manifest
registries, reduced control ODB, launcher argv/resource scopes, policy counters, projection
lookup, unsupported-history timing, and breaking-upgrade wording. Selector V2, slot index
V1, authority-policy V2, result V2, launcher publication V3, T-only authority, candidate fd
6 isolation, and all accepted POC mappings remain unchanged.

### A is evidence; an external verifier alone accepts production

No byte executed from A may authenticate A or publish an accepted continuity result. Every
provider claiming trusted production coverage requires a host-owned
`production-verifier/v1` whose executable image, policy, credentials, and first instruction
are outside the repository being classified. For GitHub this capability is a GitHub App or
equivalent host service with a separately authenticated webhook secret and exact
`metadata:read,contents:read,actions:read,checks:write` permissions. The repository workflow
and its `GITHUB_TOKEN` can publish only evidence. Its stable job is
`agentfold-ref-update/evidence-capture`; it can never satisfy the trusted continuity check.

The host verifier independently authenticates the signed delivery and numeric repository
identity; re-fetches the exact run, attempt, job, workflow, A, selector, receipt, T, and
O/N sources; verifies T ancestry, every slot locator, the complete phase projection, and the
split repository transports; invokes the sealed T evaluator itself; requires byte-identical
agreement with any repository-produced result; and publishes through its own identity. The
only accepted GitHub check is `agentfold-ref-update/verified` issued by the receipt-named App
ID. A same-named check from Actions, another App, a candidate workflow, or a repository token
has no authority. Absence of this external capability leaves remote production unavailable;
there is no in-repository fallback.

The external verifier emits canonical JSON-plus-LF
`agentfold-ref-update-production-acceptance/v1` with exactly
`schema,verifier,repository,control,event,run,result`. Nested objects have exactly:

```text
verifier = policy_sha256,issuer_kind,issuer_id,installation_id
repository = repository_id,repository_full_name
control = control_commit,selector_sha256,receipt_path,receipt_sha256,
          tested_commit,active_projection_sha256,execution,adapter_policy
event = delivery_id,event_name,action,raw_sha256,
        source_repository_id,source_repository_full_name,old,new
run = workflow_id,workflow_path,workflow_sha,
      run_id,run_attempt,job_id,job_name,status,conclusion
result = state,evaluator_exit,result_sha256
```

All existing scalar grammars apply. `issuer_kind` is the provider enum `github-app` for the
GitHub adapter; IDs are positive provider integers. The canonical acceptance excludes the
not-yet-created check-run ID. Its prefixed SHA-256 is the check run's `external_id`; the
provider response independently supplies check ID, App issuer, conclusion, and repository.
Unknown/missing/duplicate fields, absent signed delivery bytes, wrong issuer, projection or
result mismatch, publication failure, or a response/external-ID mismatch creates no accepted
result. The host retains the acceptance body as evidence, but provider success is authoritative
only while joined to the exact issuer response.

Canary artifact and receipt become `agentfold-ref-update-canary-artifact/v7` and
`agentfold-ref-update-canary-receipt/v7`. Their exact top-level keys are respectively
`schema,deployment,tested_commit,execution,adapter_policy,production_verifier,projections,launcher_source,launcher_artifact,fixture,workflow,rows,cleanup`
and those keys plus final `artifact`. `production_verifier` has exactly
`policy_sha256,issuer_kind,issuer_id,check_name,acceptance_schema`; the last two values are
the literals above. V6 evidence cannot activate V7. The verifier image is a host capability,
not an adapter-manifest row. Gate 3 requires a live V7 clean and blocked canary published by
the named external identity before retiring legacy protection. After activation, verifier
absence produces no verified check and therefore fails closed.

The external-verifier canary matrix includes completed-clean, completed-blocked, pending
approval, stale attempt, mismatched A projection, forged A evidence, forged check name,
wrong-App issuer, and publication-response mismatch. Only the first completed-clean row may
be green; the blocked row is a completed negative control, pending remains non-success, and
every forgery produces no accepted check.

### Adapter manifest V2 has separate control and target projections

`agentfold-ref-update-adapter-manifest/v2` has exactly
`schema,slot_id,authority_policy,adapter_policy,files,projections`. A source row has exactly
`role,path,mode,blob_oid,size,sha256,category`; amendment 31's `live_path` member is removed.
`projections` has exactly `control,target`, each an array of exact
`role,live_path` rows. A projection role names exactly one source row. Rows use the fixed
registry order, roles and live paths are unique within a projection, paths retain the
literal normalized UTF-8 domain, and both projections independently cap aggregate live-path
bytes at 4,096.

The complete authority role registry and order is:

```text
evaluator-entrypoint
evaluator-bootstrap
classifier-core
historical-data-contracts
authority-support-00 ... authority-support-27
```

The first four occur exactly once. Present support roles are a gap-free prefix, giving
4..32 authority rows. The complete adapter role registry and order is:

```text
activation-manifest
activation-patch
canary-driver
installed-workflow
event-extraction
object-transport
result-evidence
action-metadata
live-helper-00 ... live-helper-03
dormant-template-00 ... dormant-template-03
```

The first eight occur exactly once. Each optional family is a gap-free prefix, giving
8..16 adapter rows. `activation-manifest` and `activation-patch` use their same-named
categories; every other role uses `other`. The control projection contains exactly
`canary-driver,event-extraction,object-transport,result-evidence,action-metadata` and every
present live-helper role. The target projection replaces only `canary-driver` with
`installed-workflow` and otherwise has the same required set. Thus each projection has
5..9 rows. Activation and dormant-template roles occur in neither executable projection.
Unknown, duplicate, skipped-prefix, reordered, wrong-category, missing-projection, or extra-
projection roles refuse.

The control projection is a manually triggered build/canary driver. It cannot receive a
production push/PR trigger, change the selector, land a receipt, publish a production check,
or use a production credential. The target projection is the complete future repository
adapter, but its workflow still emits evidence rather than accepting itself. For each phase,
the dependency audit starts from that phase's fixed workflow role and requires every
repository byte executable before sealed launch to be one of its projection rows. A local
action, helper, interpreter input, dynamic path search, or checkout executable absent from
the projection refuses. Inert activation/test/documentation data remains in the source
inventory but is not executable.

Authority-policy V2 retains its row transcript. Adapter-policy V2 retains its source-row
transcript and embedded authority digest; projection metadata does not self-enter that
digest. The complete adapter-manifest locator is independently bound by T, slot index, and
V7, so admitted adapter identity is the pair `(adapter_policy, adapter_manifest locator)`.
Both manifests retain their 65,536-byte raw caps, source-count/path/payload limits, and the
54-object outer extraction inventory. V1 adapter manifests refuse.

For either projection define its canonical digest as SHA-256 of:

```text
ASCII("agentfold-ref-update-projection/v1") || 00
|| ASCII("control" or "target") || 00
|| uint16be(row_count)
|| for each registry-ordered row:
     uint16be(len(UTF8(role))) || UTF8(role)
     || uint64be(len(UTF8(live_path))) || UTF8(live_path)
     || uint64be(6) || ASCII(source_git_mode)
     || uint16be(len(source_blob_oid_ascii)) || source_blob_oid_ascii
```

The displayed value is the lowercase prefixed digest. With at most nine rows and 4,096
live-path bytes, each exact tree query is capped at `9*78 + 4,096 = 4,798` bytes; byte 4,799
refuses. The digest, tree rows, source rows, object format, and payload identities must all
agree.

### Canary and activation form an acyclic lifecycle

Define K as the immutable host-owned fixture-repository commit containing the exact target
projection. The lifecycle is:

1. Gate 2 lands the slot and its manually triggered control projection at exact T while
   leaving the active selector and current production target projection unchanged.
2. Before launcher publication V3 is accepted, the external verifier requires every control
   path at T to equal its named T source row. Publication still has `head_sha=tested_commit=T`.
3. The host fixture controller constructs K with every target path/mode/blob equal to T's
   target source row. It grants no candidate write or credential path. Provider canaries run
   the installed target workflow and helpers from exact K.
4. The external verifier authenticates K, validates the complete target projection, re-fetches
   every attempt/artifact, re-executes the sealed evaluator, and creates V7 evidence.
5. Gate 3 reads V7 from its immutable base and requires its candidate after-tree to contain
   that exact target projection. It atomically switches selector and target paths; it does
   not require the pre-Gate-3 A tree to equal the new target.
6. Every later production acceptance requires A's target projection to equal the selected
   receipt's T rows before interpreting A's evidence.

V7 `projections` has exactly `control,target`; each value has exactly
`repository_id,repository_full_name,commit,projection_sha256`. Control names the production
base repository at T; target names the configured fixture repository at K. Both identities
are independently authenticated and use T's object format. Control publication workflow
identity must name a control row at T; every completed or pending canary row must name the
same installed K target. Gate 3 candidate-after and later production A match the target
digest and rows. A different K, phase substitution, mode-only drift, or one mismatched blob
refuses.

This phase rule replaces amendment 31's universal A comparison:

```text
canary/build: T.control and K.target match
activation:   candidate-after.target matches
production:   A.target matches
```

Initial legacy A and future old-slot A therefore do not need to equal a not-yet-installed
target. Stale canaries retain their original K; stale production reruns retain original
A/selector/receipt/T. Gate 3 may remove the old control projection after receipt creation;
its source remains in retained T. Ordinary changes cannot alter an active target or a
dormant slot/control projection. Tests change every row/mode/blob independently, add an
unlisted helper, swap phases, forge evidence from mismatched workflow bytes, and race each
commit after capture; none creates an accepted result.

### A sealed authority transcript replaces the reduced control ODB

The outer host verifier alone resolves T through its temporary authenticated base ODB. It
verifies the slot index, four manifests, source paths/modes/OIDs/sizes/digests, and streams
the authority rows into one non-executable sealable memfd containing exactly the complete
authority-policy V2 digest transcript. Its maximum length is the already derived 4,203,488
bytes. It independently verifies length, Git blob identities, and the authority digest,
then applies and reads back
`F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL`. No commit, tree, ref, pack, config,
alternate, or other Git object enters this capability.

The complete launcher argv becomes:

```text
["agentfold-ref-update-launcher","--authority-manifest-fd=3","--runtime-manifest-fd=4","--authority-bundle-fd=5","--candidate-git-dir-fd=6","--old=<full-oid>","--new=<full-oid>"]
```

Fd 3 is the sealed authority manifest, fd 4 the sealed runtime manifest, fd 5 the sealed
authority transcript, and fd 6 the physically separate candidate O/N ODB. T is provenance
owned by the outer verifier and receipt; a launcher with no control ODB receives no
`--tested-commit`. The launcher requires exact seals/length, canonically parses fd 5 with no
trailing byte, matches every role/order/path/mode/size/SHA-256/Git blob OID to fd 3,
recomputes authority-policy V2, constructs the private read-only policy directory only from
those payloads, and then closes fd 3/fd 5. The evaluator sees only that policy mount and fd 6.
The outer verifier destroys its complete base ODB before releasing the launcher.

The 4,327,488-byte control loose-object reservation and every reduced-ODB clause are
withdrawn. The replacement storage counter is `authority_bundle_storage_bytes=4,203,488`;
the separate sealed policy payload remains 4,194,304 bytes within the 16 MiB policy-volume
quota. Retained non-source metadata is independently bounded by 8,192 slot-index + 1,024
launcher-policy + 2,097,152 runtime-profile + two 65,536 manifests = 2,237,440 bytes.

Cold-clone control acquisition has explicit independent containment:

```text
network/pack bytes                 134,217,728
private outer base-ODB quota       268,435,456
transport child address space      536,870,912
transport deadline                        120s
```

The two byte/quota limits have exact/+1 damage controls. Address-space containment instead
uses exact installation/readback plus page-granular allocation refusal, and the deadline has
exact monotonic expiry/cleanup controls; neither makes a fictitious byte-level OOM promise.
The outer extraction retains its 54 objects,
17,021 tree bytes, 7,812 request bytes, 50,471,936 body bytes, and 50,480,522 transcript
ceiling. Arbitrarily large unrelated T tree data never enters launcher storage; source
transport beyond the explicit outer limits is unavailable rather than unaccounted.

Launcher-policy canonical size is now at most 614 bytes including LF and actual argument
storage at most 271 bytes including every NUL. The old control-Git/tested-commit spellings,
642/351 vectors, missing/extra/reordered bundle rows, seal damage, trailing bytes, retained
writable mappings, fd swaps, or a candidate lookup through fd 5 refuse. The raw 1,024/1,025
launcher-policy containment remains.

### Setup and evaluation use different enforced process scopes

A host-owned supervisor remains alive outside the sealed evaluator. The whole transaction
has an ancestor scope with `memory.max=2,684,354,560`, swap disabled, and `pids.max=8`. It
creates three non-overlapping child scopes:

```text
control extraction  memory.max=1,073,741,824  pids.max=4  deadline=210s
launcher setup      memory.max=1,073,741,824  pids.max=2  deadline=120s
evaluator           memory.max=2,147,483,648  pids.max=4  deadline=120s
```

The control worker returns only sealed fds through one bounded `SCM_RIGHTS` socketpair and
exits before launcher creation. After mount/pivot/readback, closure of fd 3/fd 5, and zero
launcher descendants, the launcher emits one fixed ready record and blocks. The supervisor
moves that exact PID from setup into the pre-created evaluator scope, reads back membership
and every limit, destroys the empty setup scope, and sends one fixed continue byte. Only then
may the launcher exec CPython. The evaluator scope contains the existing admitted peak of one
512 MiB evaluator plus two simultaneous 512 MiB Git children. A third child refuses before
spawn.

The transaction deadline is 480 seconds: 210 extraction + 120 setup + 120 evaluation + 30
transition/cleanup. A cap, move/readback, socket/ready, deadline, exec, or cleanup failure
kill-alls current and ancestor scopes; closes fds 3..6 and partial memfds; unmounts policy,
runtime, candidate, and temporary base views; reaps all children; and requires empty scopes
and scratch before unavailable. Per-process RLIMIT, output, descriptor, and child-group
limits remain additive defenses.

### Result-v2 counters and literal projection lookup are exact

All old three-source policy counter names and aliases are deleted. Every result-v2 object,
including fast-forward, contains these authority registry entries exactly once:

```text
authority_sources             limit=1
authority_rows                limit=32
authority_path_bytes          limit=8,192
authority_payload_bytes       limit=4,194,304
authority_source_chunks       limit=95
authority_framing_bytes       limit=9,184
authority_total_hash_bytes    limit=4,203,488
```

Used values are respectively literal one; row count; aggregate UTF-8 path bytes; aggregate
payload; the sum of `ceil(file_size/65,536)` for nonempty files; recomputed framing; and
framing plus payload. Rows/path/payload retain independent exact/+1 gates. Chunk, framing,
and total maxima are derived observations with unchanged-maximum observed-minus-one controls.
O/N policy-looking files charge none of these counters. An old name, limit, or three-source
golden vector refuses.

Every T, K, A, and activation projection lookup uses the global literal option. The exact A
form is:

```text
git --git-dir=. --no-replace-objects --literal-pathspecs \
  ls-tree -z --full-tree A -- <registry-ordered exact live paths...>
```

Equivalent T/K/candidate-after commands substitute only the authenticated commit and exact
projection. Sanitized environments remove pathspec variables. Literal fixtures include
`:(literal)helper`, `:(glob)*`, `:/top`, `:!drop`, `:^drop`, and `:`; no valid path may be
silently widened, excluded, or treated as magic.

### Unsupported history is transactional; breaking switches require another task

The claim that every unsupported contract is detected before graph work is withdrawn. After
control authentication, the evaluator derives C, enumerates the bounded O/N graph, and
requests snapshots in canonical graph/OID order. Before semantic parsing of each snapshot,
its bytes must match exactly one T historical-data contract. Zero or multiple matches raise
`unsupported-policy-history`, discard every retained row/proof, close all children, emit no
complete result, and return exit 2. Endpoint detection may short-circuit as an optimization,
but counters report work actually done. A restored endpoint with one unsupported intermediate
commit must perform bounded graph/snapshot work and still refuse transactionally.

This task does not authorize a breaking active selector switch. Gate 3 may switch S1 to S2
only when S2's historical-data-contract registry is a semantic superset of S1's admitted
registry. Identical names are insufficient: predicate/parser bytes and result semantics must
be identical or covered by an independently reviewed compatibility proof. Otherwise Gate 3
leaves S1 and legacy protection active and reports `breaking history migration required`.

Dropping a contract requires a separate migration task with publication authority. That
task must use a temporary dual-root verifier for retained T1 and proposed T2, a canonical
per-action preservation/resolution mapping, an externally enforced ref freeze or exact-lease
inventory, one externally verified receipt per protected base-repository ref, explicit open-
fork treatment, and an honest refusal to claim coverage over closed/private/deleted or other
unobservable forks. Only those receipts may authorize a breaking switch. The final T2 need
not retain T1 compatibility; the temporary verifier can be removed after cutover while its
evidence remains. Deleting/recreating refs, rebasing away the edge, or running an old-slot
diagnostic cannot clear the production gate.

### Gate boundary

Production remains unopened. Amendment 32 makes a host-owned verifier and fixture repository
mandatory for trusted provider activation and deliberately permits dormant core completion
while those adapter capabilities remain unavailable. The next immutable revision needs all
three base-lens accepts on this exact text, followed by independent budget and core-admission
acceptance. No earlier verdict transfers and no production implementation may start first.

## 2026-09-01 correction amendment 33 — portable core before provider enforcement

Fresh review of `e7032e758e0d4f2efe0b232e2c0bf8e4ecf68be8` unanimously
rejected amendment 32's provider activation while accepting its phase split. A check was not
bound to the commit it protected; no authenticated App-bound ruleset or cumulative edge-debt
store made a missing check fail closed; V7 could not carry post-publication evidence and
selected its own authenticator; canary acceptance still depended on a not-yet-created
selector/receipt; the launcher lost O/N at evaluator exec; its cross-process handshakes were
open; and the public counter registry remained incomplete. Two repair panels independently
concluded that GitHub App identity, ruleset administration, merge-queue association, durable
debt, and write-recovery form a stateful provider service, not portable AgentFold core.

This amendment therefore supersedes amendments 27 through 32 wherever they specify a trusted
launcher/host verifier, execution receipt, deployment slot, selector, provider acceptance,
A/T/K production authority, Gate 2/3, live projection, or GitHub publication/enforcement.
Those sections remain rejected design history only; none is an implementation requirement or
completion claim for this task, and no verdict on them transfers to a future service. Strategy
A's two-arm O/N graph, old-side continuity proof, new-side causal authority, final N frontier,
ordinary-check separation, bounded Git/object model, and accepted POC mappings remain selected.

### Delivered boundary is core plus optional advisory evidence

This task may implement only:

1. the provider-neutral Strategy A classifier over one immutable candidate Git object source
   and exact non-zero O/N commit IDs;
2. its read-only local reconciler entrypoint and canonical advisory result;
3. deterministic budgets, transaction cleanup, and mapped regression/fault tests; and
4. an optional repository workflow that captures the same immutable edge evidence without
   publishing an authoritative conclusion.

The core trusts the caller to select the executing code and candidate object source. It does
not claim that code in a mutable checkout authenticates its own first instruction. Local and
repository-workflow output is diagnostic/advisory for exactly one O/N edge. It proves neither
cumulative branch continuity nor merge eligibility and cannot authorize a ref update. A
future trusted host may call the core only after a separate adapter establishes its own
execution and object capabilities.

No `agentfold-ref-update/verified` check, GitHub App private key, webhook secret,
`checks:write`, administration credential, provider receipt, active selector, deployment
slot, or external debt database exists in this task. It installs no ruleset, performs no
Gate 3 transition, and retires neither the current workflow nor legacy `--displaced-tip`
protection. Missing, stale, failed, or suppressed advisory evidence is `no-observation`; it
never becomes clean, mergeable, or activation-ready. Existing legacy behavior stays active
as a safety boundary, not as a backward-compatibility promise.

The provider-service dependency is owned by the required-server-side-admission step in
`2026-08-03-plan-multi-worktree-safety-remediation`. Before trusted GitHub activation, a new
child task and PR must own the host-pinned verifier root, GitHub App/webhook receiver, durable
per-ref/PR edge-debt ledger, check publisher and uncertain-write recovery, App-bound ruleset
controller, merge-queue association, canaries, credential rotation, rollback, and human
operations. That service receives its own provider-specific admission review. Repository
receipts may not select its App, policy, rule, credential, or storage root.

### Core CLI and result do not depend on the deferred launcher

The dormant entrypoint is the already selected local composition:

```text
python3 automation/reconcile/reconcile.py --check \
  --range <B>...<N> --ref-update <O> <N>
```

`--ref-update` occurs exactly once with two non-zero full OIDs of the opened repository's
object format; the range is non-root and has head N. The parser, endpoint commits, and
unique-C preflight complete before the global snapshot, Finding, output, retry, generated
index, open-actions, queue fold, or writer state is read or changed. The implementation may
factor one automation/reconcile/ref_update_core.py module, but no separate executable,
sealed launcher, fd protocol, or runtime-profile contract is part of this task. Current
workflow call sites do not invoke the new option.

The canonical advisory result is JSON-plus-LF `agentfold-ref-update-core/v1` with exact keys
`schema,old,new,common,state,rows,counters`. `state` is `clean|blocked`; fast-forward has
`common=old`, `rows=[]`, and clean. Divergent rows retain the exact
`identity,paths,status,reasons,finding` shape and `preserved|valid|none|invalid|ambiguous`
semantics already selected. Unknown/missing/duplicate keys or wrong JSON scalar types refuse.
Structural/history/resource failure emits no result object, one bounded stable diagnostic,
and exit 2. Complete clean/blocked exits are 0/1. A serialized result is evidence for tests
and humans, never a provider acceptance envelope.

### The core counter registry is complete and smaller than execution policy

The old three-source policy counters and amendment-32 authority-source counters are outside
this unsealed core boundary and do not appear. `CORE_COUNTER_LIMITS_V1` has exactly these 67
ASCII names and limits, emitted in ASCII sort order; every complete result contains each
exactly once as `{used,limit}` and no other name:

```text
additional_parent_subprocess_queries=0
authority_validations=512
batch_reader_restarts=8
carry_proof_edges=262144
carry_proof_nodes=262144
causal_roots_per_identity_peak=512
causal_roots_total=65536
certificate_anchors=8192
certificate_obligations=8192
certificate_peak_serialized_bytes=4194304
certificate_projection_rows=65536
certificate_serialized_bytes=33554432
diagnostic_bytes=262144
discovered_support_paths=8192
distinct_object_reads=65536
distinct_queue_subtree_oids=4096
dynamic_support_traversal_paths=65536
endpoint_commits=2
flattened_path_bytes=8388608
flattened_tree_entries=131072
git_children_live_peak=2
git_children_spawned=512
git_stderr_bytes=262144
graph_commit_records=4096
graph_parent_oid_fields=8192
graph_peak_line_bytes=532545
graph_stdout_bytes=798720
historical_checker_invocations=8192
historical_helper_nodes=4096
identity_carry_transitions=262144
identity_derivations=262144
identity_mutation_checks=262144
immutable_peak_result_row_bytes=1048576
immutable_result_references=524288
immutable_result_rows=262144
immutable_retained_result_bytes=33554432
merge_base_peak_line_bytes=65
merge_base_rows=2
merge_base_stdout_bytes=130
merge_base_tokens=2
object_cache_hits=262144
object_header_bytes=4194304
obligation_replays=65536
occurrences_per_identity_peak=16
peak_object_payload_bytes=4194304
production_helper_calls=16384
production_helper_input_bytes=8388608
production_helper_output_bytes=16777216
production_helper_output_records=262144
production_identities=2048
queue_blob_bytes=33554432
queue_path_bytes=4194304
queue_snapshot_cache_hits=262144
queue_snapshot_entries=65536
queue_snapshot_requests=262144
queue_subtree_reads=4096
raw_tree_entry_name_bytes=8388608
result_peak_serialization_chunk_bytes=1048576
result_serialization_bytes=33554432
shallow_probe_peak_line_bytes=6
shallow_probe_rows=1
shallow_probe_stdout_bytes=6
shallow_probe_tokens=1
support_adoption_checks=8192
support_certificates=512
support_path_bytes=1048576
unique_object_payload_bytes=33554432
```

`used` is an integer, never Boolean/float, with `0 <= used <= limit`; a zero limit therefore
requires zero. Fast-forward performs endpoint/preflight/result work and reports zero for all
unexercised graph/action families. Structural counters remain independent gates. Derived
byte observations retain their observed-minus-one controls and do not invent unreachable
schema-valid +1 fixtures. Wall-clock, OS fragmentation, cgroup, transport, and provider work
are absent from canonical counters.

`result_serialization_bytes.used` equals the final canonical line length. The encoder finds
the unique length-field fixed point by bounded iteration from zero before allocating output,
then encodes once into the precharged cap and verifies the measured length. Peak serialization
uses deterministic logical chunks of at most 1 MiB, never pipe fragmentation. Unknown,
missing, duplicate, legacy, negative, over-limit, or inconsistent counters make an advisory
result invalid and cannot be projected as clean.

### Human and workflow effect of the split

- A developer can run the paired local command to distinguish a valid inherited resolution
  from a genuine or ambiguous queue loss before pushing.
- An optional CI job may attach the canonical edge result and exact O/N to a workflow artifact
  named as evidence. Its UI may be green only for successful artifact capture; it must display
  the classifier state separately and must not use a required-check or `verified` name.
- A pushed clean advisory edge does not clear an earlier blocked, unavailable, or missed edge.
  This task has no debt store and makes no cumulative statement.
- A genuine deletion remains actionable in the local result: restore the action or complete
  one valid lifecycle. Re-running or pushing a later commit is not documented as clearance.
- Provider/fork/no-observation behavior is reported honestly as unavailable evidence. No
  branch-protection, live trusted canary, or automatic publication claim is in scope.

Verification for this task may prove the 167 accepted semantic scenarios, 34 damaged-mode
controls, 4 aliases, 68 evidence attacks, local CLI/reconciler parity, every core exact/+1
budget, zero partial result/mutation, child cleanup, ordinary-check composition, targeted and
full suites, reconciler, and cold clone. It may not cite a trusted provider check, V7 receipt,
live cumulative coverage, App issuer, ruleset, merge queue, or legacy retirement as passed.

### Core implementation gate

Production activation remains unopened, but provider-neutral **dormant core implementation**
may begin after one immutable revision containing amendment 33 receives the three fresh base
lens accepts followed by budget and core-admission accepts. Those reviews judge Strategy A,
the local transaction, exact result/counter contract, and the explicit scope split; they do
not approve the rejected provider/launcher history. Provider adapter/service implementation,
selector activation, workflow replacement, and legacy retirement remain separate PRs and
cannot borrow this task's review or POC receipt.

## 2026-09-01 correction amendment 34 — separate advisory commands and unique bytes

Fresh review of `c0bdc44ae10bfa65a25b961ab5e3970b5bfb6107` rejected the
amendment-33 executable contract without reopening Strategy A or the core/provider split.
Two independent reviewers found that amendment 33 reintroduced a combined
`reconcile.py --ref-update` mode even though amendment 15 still forbade it. The combined
mode also had no truthful result for continuity-clean plus ordinary-blocked, did not reject
existing writer flags despite calling itself read-only, and left the canonical peak
serialization counter dependent on an unspecified logical partition.

This amendment supersedes amendment 33's CLI/result subsection, its "paired local command"
wording, and its implementation-gate revision. It also supersedes amendments 15–16 only
where their authority-policy field, result schema, or row shape conflicts with the unsealed
core result below. Amendment 15's two-command boundary and read-only option rejection,
amendment 16's `preserved` semantics and stable identity-based Finding, amendment 33's
67-name counter registry, and the amendment-33 core/provider scope split remain selected.

### Continuity and ordinary checking remain separate processes

The only dormant Strategy A CLI is:

```text
python3 automation/reconcile/ref_update.py \
  --git-dir <absolute-path> --old <full-oid> --new <full-oid>
```

It is read-only and Linux-only. Its custom parser accepts exactly one occurrence of each of
the three displayed options, except that `--help` may appear alone. Before opening the object
source it rejects missing, duplicate, positional, syntactically partial, zero, or
unequal-width endpoints and every range, worktree, index, branch, task, provider,
compatibility, publication, or writer option. After opening the source, its object format
determines the required full OID width; abbreviated or non-commit endpoints then refuse
before graph/action work. `--git-dir` must be an absolute path naming the single candidate object source;
replace refs, lazy fetch, alternates, network and remote helpers remain disabled by the
selected object boundary. On a host without the selected Linux containment primitives the
command emits the canonical incomplete diagnostic and exits 2 before history work.

`automation/reconcile/reconcile.py` does not gain `--ref-update`, import the new CLI, or
change its parser, output, writers, `--range B...N`, `root:N`, `--displaced-tip`, workflow,
or cross-platform behavior in this dormant task. A separate `ref_update_core.py` library may
hold the classifier, but only `ref_update.py` calls it in this task. The recursive
`automation/reconcile/` spawn guard and tests still discover both new files.

A developer who needs both judgments runs two explicit commands with the same inspected N:

```text
python3 automation/reconcile/ref_update.py \
  --git-dir <absolute-path> --old <O> --new <N>
python3 automation/reconcile/reconcile.py --check --range <B>...<N>
```

The first result answers only whether the exact O→N replacement has one valid continuity
explanation. The second answers only the existing ordinary candidate checks. They retain
independent stdout, stderr, and exits: continuity 0/1/2 means clean/blocked/incomplete under
the contract below, while the ordinary process keeps its current contract. A human or
non-authoritative wrapper reports the two named results separately; it may summarize the
pair as usable only when both complete clean, but it may not mint a third canonical result,
hide either output, reinterpret incomplete as clean, or let either clean result clear the
other blocked/unavailable result. There is therefore no mixed-result stdout or overloaded
exit code to define.

An optional evidence-only repository workflow may capture the continuity command's exact
O/N invocation, stdout, stderr, exit, and artifact digest. If it also runs ordinary checks,
those bytes remain a separately named artifact/result. Current workflow call sites remain
unchanged, and neither result is authoritative, cumulative, or merge-enabling.

### The standalone advisory envelope is closed

Every complete continuity result is exactly one canonical UTF-8 JSON line on stdout plus LF,
with sorted keys, ASCII escaping, compact separators, and empty stderr. Its schema is
`agentfold-ref-update-core/v1` and its exact top-level keys are
`schema,old,new,common,state,rows,counters`. Complete clean/blocked exits are 0/1. A
fast-forward has `common=old`, `rows=[]`, and `state=clean`. Structural, platform, history,
resource, child, delivery, or serialization incompleteness produces no accepted result,
attempts one bounded stable JSON-plus-LF diagnostic on stderr with exact keys
`schema,state,reason`, `schema=agentfold-ref-update-core/v1`, `state=incomplete`, and one
closed ASCII reason code, and exits 2; partially accepted transport bytes retain amendment
16's debris rule and can never be decoded as a result.

Every divergent row has exactly `identity,paths,status,reasons,finding`. Rows sort by full
domain-separated identity digest; paths and closed reason codes are sorted unique values.
Status is exactly `preserved|valid|none|invalid|ambiguous`. `finding` is null exactly for
`preserved` and `valid`; otherwise it is amendment 16's exact stable identity-based
`check,subject,message,fix` object. Full retained proof remains an internal immutable test
value rather than an open CLI field. Unknown, missing, duplicate, legacy, or wrong-typed
keys at any level refuse strict decoding. This explicitly replaces amendment 16's `policy`
top-level field and row `evidence` digest: an unsealed advisory cannot authenticate its own
executing policy, and tests bind the internal proof directly.

`counters` contains every amendment-33 `CORE_COUNTER_LIMITS_V1` name exactly once in ASCII
sort order as exact `{used,limit}` objects and no other name. The 67 names, limits, type
rules, exact/limit controls, fast-forward zeros, and invalid-result behavior remain
unchanged.

### Serialization counters use one exact logical partition

Let `L` be the length in bytes of the final canonical JSON line including LF. Its logical
serialization partition is uniquely the consecutive half-open slices
`[0,1048576)`, `[1048576,2097152)`, and so on, truncated at `L`; no caller-, write-, pipe-,
or platform-sized partition is permitted. Because a result is nonempty,
`result_peak_serialization_chunk_bytes.used = min(L,1048576)` and
`result_serialization_bytes.used = L`.

The pre-allocation size calculator solves the two self-referential integers jointly. Starting
with `(length,peak)=(0,0)`, it counts the exact canonical bytes that would be encoded with
those two provisional `used` values without allocating the result buffer, sets the next pair
to `(count,min(count,1048576))`, and repeats. The first pair equal to its successor is the
canonical pair selected by this algorithm; failure to converge within 16 counted passes is incomplete. The
encoder then precharges `L`, allocates once, writes exactly the fixed-point line in the
defined slices, and verifies both measured length and peak before delivery. Tests cover each
decimal-width transition around both counters, `L=1048575`, `1048576`, and `1048577`, the
32 MiB exact/plus-one boundary, a deliberately nonconverging calculator double, alternate
4 KiB/caller chunking, short writes, and re-encoding under different hash seeds, locales,
time zones, and pipe fragmentation.

Amendment 33's `local CLI/reconciler parity` verification phrase is withdrawn. Verification
instead requires standalone CLI/library byte parity, explicit proof that `reconcile.py` and
current workflow bytes and behavior are unchanged, the two independent-result human matrix,
and all other in-scope semantic, fault, budget, cleanup, targeted/full-suite, reconciler, and
cold-clone evidence listed there.

### Corrected implementation gate

Production activation remains unopened. Dormant provider-neutral core implementation may
begin only after one immutable revision containing amendment 34 receives three fresh base
lens accepts, followed on that same revision by independent budget and core-admission
accepts. Those reviews cover the separated CLI, standalone bytes, 67-name registry,
Strategy A semantics, local transaction, and explicit provider-service boundary. No verdict
on `c0bdc44ae10bfa65a25b961ab5e3970b5bfb6107`, no incomplete review, and no verdict on the
rejected provider/launcher history transfers.

## 2026-09-01 correction amendment 35 — close the standalone core contract

Fresh review of `7f36270552fd0035f27e0119a19030a1ff20f1ae` accepted the human
two-command workflow and core/provider boundary, but rejected two executable ambiguities.
Authority-policy rules retained from amendments 4, 17, and 18 made one policy-changing
fast-forward exit both 0 and 2, and amendment 34's JSON adjectives still allowed distinct
escaping bytes and therefore distinct serialization counters. Review also exposed that
amendments 33–34 withdrew trusted execution and provider work only from selected amendment
ranges instead of from the complete active contract.

### Supersession and retained behavior are closed by subject

This amendment supersedes every earlier clause in this design, regardless of amendment
number, wherever that clause:

1. requires the dormant core to load, compare, hash, emit, or validate an authority,
   adapter, execution, launcher, runtime, deployment, selector, receipt, or live-projection
   policy;
2. makes namespaces, cgroups, memfds, sealed roots, descriptor protocols, a host verifier,
   a trusted launcher, or a provider capability a condition for running or completing the
   local advisory core;
3. specifies a provider transport, credential, workflow authority, canary, artifact,
   receipt, check publisher, ruleset, merge-queue association, debt store, Gate 2/3, or
   provider acceptance as an implementation requirement or completion gate for this task;
4. permits a core result to become trusted, cumulative, merge-enabling, ref-update
   authority, or evidence for retiring the current workflow or legacy `--displaced-tip`;
   or
5. permits the recursive `automation/reconcile/` source guard to exempt an adapter network,
   remote-helper, credential, provider API, or publication path.

Those clauses remain rejected design history and are not revived because a selected
semantic or budget rule once appeared beside them. Receipt, launcher, adapter, and provider
schemas do not govern `agentfold-ref-update-core/v1`.

The selected contract is only Strategy A's two-arm O/N graph, old-side continuity proof,
new-side causal authority, final-N frontier, production queue identity and lifecycle rules,
typed historical retry evaluators, deterministic logical Git/object/result budgets,
amendment 34's standalone CLI and separate ordinary command, and amendment 33's 67-name
`CORE_COUNTER_LIMITS_V1` registry. Amendment 34's row semantics, stable Finding, independent
exits, logical serialization partition, and evidence-only optional workflow remain selected
except where the exact encoder below replaces its encoding sentences.

### The caller selects advisory code; the core authenticates no policy

The future local `ref_update` CLI calls the future `ref_update_core` module in process using
the code the caller selected and the one immutable Git object source named by `--git-dir`. It does not
authenticate its own first instruction, compute or compare a policy digest, inspect a
selector or receipt, or require provider state. The parser and bounded object reader still
validate exact O/N syntax, repository object format, and commit types before classification.

A fast-forward returns after the bounded ancestry check and before queue identity, snapshot,
or causal-root work. A divergent edge applies the executing core's shipped queue identity,
mutation, deletion-authority, and historical-evaluator rules to immutable O/N history.
Those rules define diagnostic behavior for this invocation; they are not an authenticated
execution policy. No complete or incomplete core envelope has a policy, execution,
provider, selector, receipt, or coverage field.

The CLI runs on AgentFold's existing Python-and-Git platforms. It enforces every selected
logical counter, bounded child stream, deadline, termination, reap, descriptor closure, and
zero-partial-result rule, but claims no OS-level address-space, namespace, cgroup, or
first-instruction containment. A future authoritative caller must supply and verify those
guarantees outside core. Missing platform containment is therefore not a core failure;
failure to obtain one complete accepted line remains no result and never becomes clean.

The recursive source guard discovers `ref_update.py` and `ref_update_core.py`, permits only
their closed local Git/object subprocess shapes, and grants no network, remote-helper,
credential, provider API, publication, or filesystem-writer exception.

### Fast-forward and ordinary results remain independent

For the concrete mixed case, let O contain a live action and let direct descendant N delete
it without the lifecycle evidence ordinary queue checking requires:

```text
O -- N
     deletes the live action without evidence
```

The continuity command observes `O <= N` and returns `state=clean`, `common=O`, `rows=[]`,
and exit 0. It means only that displaced-tip continuity is inapplicable to a fast-forward.
The separate `reconcile.py --check --range O...N` command examines the real deletion edge,
emits the ordinary `queue-resolution` Finding, and exits 1. Continuity clean cannot clear
ordinary blocked. The outputs stay separately named; no combined exit, canonical aggregate,
merge-eligibility statement, or cumulative clearance exists. No earlier policy-changing
fast-forward exit-2 rule remains active.

### One Python-standard-library core encoder

The sole complete-result and incomplete-diagnostic encoder is one unmodified encoder:

```python
json.JSONEncoder(
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=False,
    sort_keys=True,
    indent=None,
    separators=(",", ":"),
)
```

No subclass, custom `default`, alternate encoder, or post-encoding rewrite is permitted.
For an admitted value `v`, define `E(v)` as the strict ASCII encoding of the concatenation
of that encoder's `iterencode(v)` fragments followed by exactly one LF. Fragment boundaries
have no semantic or counter meaning. `E(v)` must be byte-identical to:

```python
json.dumps(
    v,
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=False,
    sort_keys=True,
    indent=None,
    separators=(",", ":"),
).encode("ascii", "strict") + b"\n"
```

The admitted in-memory tree uses exact built-in types only: `dict` with exact `str` keys,
`list`, Unicode-scalar `str`, nonnegative `int`, and `None`. No subclass is admitted.
`bool`, `float`, tuple, bytes, non-string key, unpaired surrogate, cyclic value, or other
Python value refuses before encoding. Strings are not normalized, trimmed, or case-folded.
No JSON Boolean occurs in a core envelope. `None` occurs only as an allowed null `finding`.

A counter is an exact built-in dictionary with exact keys `limit,used`. Both values have
exact type `int`, never `bool`; `limit` equals `CORE_COUNTER_LIMITS_V1[name]`, and
`0 <= used <= limit`. Complete-result fields retain amendment 34's exact schemas, ordering,
enums, digests, paths, reasons, and state consistency. The incomplete diagnostic retains
only amendment 34's three exact string fields.

Strict acceptance removes one final LF, decodes the rest as ASCII, rejects duplicate object
keys and every floating-point or nonstandard constant token, and accepts an integer token
only when it matches `0|[1-9][0-9]{0,7}` and is at most 33,554,432. It then validates the
exact field grammar and built-in types and requires `E(decoded)` to reproduce the original
bytes. Whitespace, CRLF, alternate escaping, reordered keys, negative or oversized integers,
and noncanonical numeric spellings therefore refuse.

### Serialization counters use that exact encoder

Let `V(length,peak)` be the frozen complete result with only
`result_serialization_bytes.used=length` and
`result_peak_serialization_chunk_bytes.used=peak`; their limits remain 33,554,432 and
1,048,576. Starting from `(l0,p0)=(0,0)`, compute:

```text
encoded_i = E(V(li,pi))
li+1      = len(encoded_i)
pi+1      = min(li+1,1048576)
```

A counting pass may consume the exact encoder fragments without retaining their
concatenation. The first pair equal to its successor is selected. More than 16 passes, or
any counted length above 33,554,432, is incomplete. For selected `(L,P)`:

```text
final_bytes = E(V(L,P))
L = len(final_bytes) = result_serialization_bytes.used
P = min(L,1048576) = result_peak_serialization_chunk_bytes.used
```

Logical serialization chunks remain the consecutive 1,048,576-byte slices of
`final_bytes` beginning at byte zero, with only the final slice shorter. Iterator, caller,
pipe, and write boundaries cannot change P. After the fixed point is selected, the encoder
precharges L, allocates the final buffer once, encodes once, and verifies every equality
before delivery.

Golden tests cover forbidden Python types, duplicate keys, unpaired surrogates, exact slash,
quote, control, and Unicode escaping, integer boundaries, every decimal-width transition of
both self-referential values, L at 1,048,575/1,048,576/1,048,577 and 33,554,432/plus one,
convergence refusal, and byte identity across `iterencode`, `json.dumps`, library, and CLI.

### Corrected dormant-core gate

Dormant core implementation may begin only after one immutable revision containing
amendment 35 receives three fresh base-lens accepts, followed on that same revision by
independent budget and core-admission accepts. Those reviews cover the standalone advisory
classifier, separate ordinary composition, canonical result/counters, logical resource
transaction, tests, and explicit trust boundary. Provider service work, trusted execution,
activation, workflow replacement, and legacy retirement require separate tasks, designs,
reviews, and PRs and cannot borrow this task's verdicts or POC evidence.

## 2026-09-04 amendment — cap at the acceptance criteria and implement the continuity-edge repair

**Amendment status:** closes this task at its six acceptance criteria. The repair lands in
`automation/reconcile/reconcile.py` and its tests; amendments 1–35 and the dormant `ref_update`
standalone core stay in this file as parked design history, neither required by any acceptance
criterion nor deleted.

### Whether the missing guard was deliberate (acceptance criterion 4)

`git log -S'divergent update discarded a live old-tip action'` and
`git log -S'def committed_queue_deletion_events'` each return only `91e0ad2` (2026-07-23,
"harness: preserve queue actions across revisions", task `2026-07-23-first-class-message-queue`),
whose body carries no rationale: the constant and its two-tree event source entered together.
`git log --all -m -S'def candidate_paths_match_other_parent'` lists only the two-parent merge
`d7eefcee` (2026-07-24), against both parents and no non-merge commit, so the guard entered in
that merge's own resolution a day later and reached `main` through `2372e48` (pull request #7);
no ADR, test, or comment excludes it from the continuity edge. Reading: the continuity edge was
structurally deliberate as a raw preservation check with no parent set to consult, and the later
guard's absence there is not evidenced as a deliberate exclusion. The asymmetry is repaired.

### The continuity-edge repair meets the six acceptance criteria

`continuity_deletion_problem(old_tip, new_head, path)` replaces the constant problem for one
path the displaced tip `O` carries and the new head `N` lacks: (1) exactly one merge base `C`
of `O` and `N` from `git merge-base --all`, otherwise the constant finding; (2)
`git_tree_path_entry(O, path)` equal to `git_tree_path_entry(C, path)`, otherwise the constant
finding, because an action the old lineage authored or changed is still the branch's to answer
for (acceptance criterion 2); (3) every real parent→child edge in `C..N` on which the path's
tree entry disappears, located by tree entry per parent edge from one `rev-list --parents` walk
with no activation skip, minus an edge where `candidate_paths_match_other_parent` proves a
merge adopted another parent's real deletion, and following an identity-preserving timing move
to its destination; (4) `queue_deletion_problem` on each located edge, the first problem
reported as `inherited deletion <commit> lacks its own lifecycle evidence: <problem>` with the
fix `repair or revert the base deletion; force-pushing this branch cannot resolve it`
(acceptance criterion 3); (5) silence only when no located edge was invalid and at least one
validated edge deleted the action identity `C` carried (acceptance criterion 1; the task's
reproduction is `test_continuity_edge_accepts_a_restack_over_a_valid_base_resolution`). The
check id stays `queue-resolution` with the path as subject; a continuity verdict repeating an
ordinary-range finding for the same path and problem is one finding. Authorship is never
consulted; no `M`, pull-request API, provider state, or mutable `HEAD` participates; a Git
failure raises `GitSnapshotError`. Eleven continuity tests beside the two existing
displaced-tip tests cover the reproduction, an evidence-free base deletion, the old lineage's
own claim, a mixed drop, a merge-shaped base, a timing move, reintroduction then bare
re-deletion, a pre-activation base deletion, criss-cross merge bases, de-duplication, and a
base-side identity rewrite; scratch mutations dropping the identity requirement, the lifecycle
call, the tree-entry guard, the merge skip, or the move-follow each turn at least one of them
red (acceptance criterion 2). `verification.md` carries the real commands and output of those
runs and of the full suite (acceptance criterion 5) when they are folded.

### The production-contract line is parked

The v11–v15 production-contract prototype line is parked, not repaired. v15 at
`7e47b5b66b579e01e82bb4cbb9e5e622580d4800` received three fresh BLOCK verdicts on 2026-09-04:
its public audit verdict is computed under a frozen fixture clock, its evidence audit passes
only where the first-found Git binary is byte-identical to one machine's, and its audited path
leaves the reconciler's `HEAD` object unbound so deletion authority reads the repository's
current `HEAD`. No repair round is opened; the resume item
`message-queue/needs-agent/requests/future-blocking-resume-v15-production-contract-review.md`
records the hold.

### Corrected receipt lines

The `Thin adapter` line of the original receipt (the `## Core fit` section above) describes
GitHub resolving a pull-request base SHA and deriving `M`; the repair needs neither, writes
only repository files, and calls no provider API. The receipt reads correctly as:

```text
**Agent substitution:** pass — the rule consumes only committed repository objects and existing queue authority, so another agent runtime preserves the behavior
**Provider substitution:** not-applicable — no hosted-provider state participates in identity, authority, or attribution
**Repository substitution:** pass — any adopted repository using AgentFold's queue and rewritten-history gate needs the same false-accusation protection
**User-global writes:** none
**Why AgentFold core:** rewritten-history queue preservation and lifecycle authority are reconciler invariants, not local configuration, a product service, private overlay, or separate plugin
**Thin adapter:** none
```

### Two accepted differences from the parked classifier design

Byte-identical delete-and-recreate on the old lineage, and reintroduction followed by a valid
re-deletion, are silent under the repair where the parked classifier blocked both: the queue
contract treats an evidenced real-edge deletion of the same action text as a resolution, and
neither case is required by an acceptance criterion.

### Follow-ups outside this task

Two defects remain for separate tasks and are untouched here: `claimed_lifecycle_problem` can
borrow a claim from any parent across a merge's absence boundary (an ordinary-path defect, not
restack-specific), and `committed_queue_mutation_events` on the continuity edge has the same
missing guard for the mutation group, so a base-side identity change the base's own gate
admitted can be attributed to the rewrite.

### 2026-09-04 addendum — after the fresh panel

The base design's `## Chosen` and `## Verification design` sections describe the parked
classifier line; from this amendment on, only the continuity-edge repair above binds
implementation. The `git log -S` sentences above hold with two qualifiers a reviewer asked for:
the constant and `committed_queue_deletion_events` return only `91e0ad2` when the search is
limited to `automation/reconcile/reconcile.py`, and the guard's arrival is visible only with
`git log --all -m`, where merge `d7eefcee` is the single commit listed against both of its
parents. The two follow-ups named above are filed as backlog tasks
`2026-09-04-judge-inherited-queue-mutations-on-their-real-edges` and
`2026-09-04-stop-a-merge-from-borrowing-a-claim-across-an-absence`.
