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
**Thin adapter:** GitHub may resolve and stabilize one exact same-repository PR base SHA,
fetch exact event objects, and derive local `M`; it owns no identity, lifecycle, authority,
or fallback decision

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
