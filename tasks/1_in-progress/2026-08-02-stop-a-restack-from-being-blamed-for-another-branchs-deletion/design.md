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
