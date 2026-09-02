# Exact candidate-side deletion witness POC

This POC proves that a restack can stop blaming a task for a base-owned resolution
without excusing an unauthorized deletion; nobody needs to act on this POC alone,
because it changes no production behavior.

Before this prototype, the continuity check saw only the synthetic displaced-tip to
candidate edge, so a legitimate base resolution and a lost action both looked like one
path deletion. The prototype now finds the candidate-only parent/child edge that actually
deleted the same action, then asks the reconciler (the script that checks repository
invariants) to validate the claim and evidence on that real edge. Twenty-nine real-Git
scenarios passed, including the reported good restack, three missing-history failures,
deletion at the candidate head, activation laundering, and synthetic-edge evidence
laundering. Nine executable controls also passed, including seven observed-red reproductions
of verifier-found incarnation bugs. The prototype deliberately fails closed on repeated
incarnations, so it is evidence for a design direction rather than production code.

## Canonical semantic evidence versus run telemetry

`semantic_boundary.py` proves that operational budget observations cannot be part of the
authoritative result. Before this module, a tempting result shape could carry every scan,
cache, subprocess, allocation, retention, and serialization counter alongside the finding.
That shape is not unique: an implementation may request each identity/node and cache by
shared object, while another may resolve the shared object once and batch the remaining
work. Now both implementations must emit byte-identical semantic result bytes, while each
run emits a separate receipt whose bytes are allowed to differ. This module changes no
production behavior.

The semantic result is exactly one JSON value plus one LF with these top-level keys in this
order, and no others:

```text
schema, old, new, common, state, rows
```

`old` and `new` bind the invocation's full `O` and `N` object IDs. `common` is the sorted,
duplicate-free list of full shared-boundary object IDs. `state` is `clean` only when `rows`
is empty and `blocked` only when at least one row exists. Each row has exactly
`path,kind,old_blob,new_blob,reason` and identifies an unauthorized deletion or rewrite.
No counter, implementation name, runtime value, limit, cleanup claim, or cardinality field
is accepted in these bytes.

The strict codec has one representation: ASCII JSON produced with non-ASCII characters
escaped, no optional whitespace, canonical key and row order, and exactly one trailing LF.
The decoder parses with duplicate-key detection, validates exact Python/JSON types, then
re-encodes and compares every byte. It rejects duplicate keys; unknown and legacy keys;
wrong types (including JSON booleans where integers are required); alternate escapes; key
reordering; whitespace and CRLF; prefix or suffix bytes; a missing LF; inconsistent rows,
kinds, reasons, or state; and `old`/`new` values that differ from the invocation.

### Executable non-uniqueness counterexample

The synthetic and real-Git controls each bind `O`, `N`, and their one common commit to the
same immutable queue subtree. The two evaluators observe different work while emitting the
same semantic bytes:

| Evaluator | Snapshot requests | Cache hits | Semantic bytes | Receipt bytes |
|---|---:|---:|---|---|
| identity/node cache | 6 | 5 | identical | implementation-specific |
| shared-object batch | 1 | 0 | identical | implementation-specific |

The exact synthetic semantic result is:

```json
{"schema":"restack-queue-semantic-result/v1","old":"7a82f44ff34aa6db4cb1bb8de2b12f77332c68d1","new":"386ce74febd5dc07082d2cbed833e10e15c4b180","common":["663682aad5cdc7cb63caa74f8f4c976b4d001376"],"state":"clean","rows":[]}
```

The terminating LF is part of the bytes. Both receipts bind the SHA-256 of those bytes, but
the receipts differ because they identify the evaluator and preserve its `6/5` or `1/0`
observations. This is the concrete counterexample to putting operational counters in the
semantic digest: both implementations conform and reach the same authoritative answer, so
neither counter pair may make one answer a different result.

### Execution receipt and incomplete runs

The run-scoped receipt is a separately canonical JSON transport with schema
`restack-queue-execution-receipt/v1`. It records `result_sha256` or `null`, implementation,
Python/Git/platform, budget profile, limits, used counters, exit, incomplete reason, and
cleanup observations. A provider projection (the provider-facing clean/blocked/incomplete
view) accepts a semantic result only when the strict result decoder succeeds and the
receipt digest matches. Receipt counters never alter the rows or state.

An absent result plus a valid incomplete receipt projects to `incomplete`, never `clean`.
There is no incomplete semantic result: budget refusal, provider failure, serialization
refusal, injected fault, digest mismatch, or failed cleanup produces no accepted result
bytes. A receipt claiming completion without a digest, or incompleteness with a digest, is
itself invalid.

### Deterministic budgets and cleanup

The POC charges each bounded operation before its callback: snapshot request, read,
allocation, child spawn, retained bytes, result write, and written bytes. A run with every
limit set to its observed use succeeds. Seven observed-minus-one controls lower each
reachable maximum independently and prove that the run refuses before accepting a partial
result. Seven direct `N+1` controls also prove that the rejected callback is never invoked.

Result bytes remain staged until evaluation and cleanup succeed. On every complete or
incomplete path, the transaction clears its cache, terminates and reaps live children,
closes process streams and explicit descriptors, and compares repository refs, worktree
status, and index bytes with their pre-run fingerprints. The fault controls interrupt after
the first cached snapshot, after a real child spawn, after a real descriptor open, and
immediately before result commit. Every interruption emits only an incomplete receipt and
leaves the real-Git fixture unchanged.

### Cardinality decision

No proof-derived set cardinality belongs in the semantic result at this boundary. The
provider consumer needs the actual sorted `common` identities to bind and replay the proof,
and it needs the actual finding rows to project `blocked`; it consumes no count. A count is
derivable from those semantic members, while snapshot counts, witness-set sizes, cache
sizes, and scan totals depend on implementation strategy. Until a consumer demonstrates a
decision that cannot use the members themselves, every such count remains receipt-only
telemetry.

### Replayable verification

The new self-test preserves the existing 29-scenario test and independently covers strict
round trips, the `6/5` versus `1/0` counterexample, fast-forward, divergent clean and
blocked, provider projection, incomplete runs, exact and `N+1` budgets, observed-minus-one
maxima, cleanup/fault injection, a 2,048-row result, serialization byte/row bounds, and two
absolute fixture roots:

```sh
python3 docs/designs/restack-queue-provenance/pocs/edge-witness/prototype.py --self-test
python3 docs/designs/restack-queue-provenance/pocs/edge-witness/semantic_boundary.py --self-test
```

The second command emitted 51 named damage-control records followed by this exact summary
on 2026-09-02 with Python 3.14.7 and Git 2.55.0:

```json
{"checks_passed":82,"checks_total":82,"counterexample":"6/5-vs-1/0","damage_controls_passed":51,"damage_controls_total":51,"large_rows":2048,"real_git_cases":4,"summary":"PASS","synthetic_cases":4}
```

The 51 controls are 17 strict-transport rejections; two serialization-bound refusals;
seven observed-minus-one incomplete runs; seven `N+1` pre-charge refusals plus seven
callback-not-run checks; nine fault/cleanup checks; and two provider incomplete/digest
checks. The self-test prints each name and `PASS`, so no grouped total can hide a skipped
control.

Cross-implementation comparison:

```sh
PYTHONPYCACHEPREFIX=/tmp/edge-semantic-pycache python3 docs/designs/restack-queue-provenance/pocs/edge-witness/semantic_boundary.py --emit-semantic-suite --implementation identity-node-cache > /tmp/edge-semantic-identity.jsonl
PYTHONPYCACHEPREFIX=/tmp/edge-semantic-pycache python3 docs/designs/restack-queue-provenance/pocs/edge-witness/semantic_boundary.py --emit-semantic-suite --implementation shared-object-batch > /tmp/edge-semantic-batch.jsonl
cmp /tmp/edge-semantic-identity.jsonl /tmp/edge-semantic-batch.jsonl
shasum -a 256 /tmp/edge-semantic-identity.jsonl /tmp/edge-semantic-batch.jsonl
```

The comparison exited 0. Each file contained six results and 1,803 bytes with SHA-256
`14ee3bb1901fb2a767184cf6b22cdc33ba60acb65fca6f0f2501635f55a15b2c`.

Two-environment comparison, changing hash seed, locale, timezone, Python cache root,
implementation, and absolute fixture root:

```sh
PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/edge-semantic-pycache-env1 python3 docs/designs/restack-queue-provenance/pocs/edge-witness/semantic_boundary.py --emit-semantic-suite --implementation identity-node-cache > /tmp/edge-semantic-env1.jsonl
PYTHONHASHSEED=777 LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/edge-semantic-pycache-env2 python3 docs/designs/restack-queue-provenance/pocs/edge-witness/semantic_boundary.py --emit-semantic-suite --implementation shared-object-batch > /tmp/edge-semantic-env2.jsonl
cmp /tmp/edge-semantic-env1.jsonl /tmp/edge-semantic-env2.jsonl
shasum -a 256 /tmp/edge-semantic-env1.jsonl /tmp/edge-semantic-env2.jsonl
```

That comparison also exited 0 with the same six lines, 1,803 bytes, and SHA-256 above.

## Result

**VERIFIED:** the exact command below exited 0 on 2026-08-31 in the unit worktree with
Python 3.14.7 and Git 2.55.0:

```sh
python3 docs/designs/restack-queue-provenance/pocs/edge-witness/prototype.py --self-test
```

The command printed one JSON object per scenario, followed by this exact summary:

```json
{"controls_passed":9,"controls_total":9,"git":"git version 2.55.0","observed_red":7,"passed":29,"python":"3.14.7","summary":"PASS","total":29}
```

I also retained a fresh set of all 29 disposable repositories with this exact command:

```sh
python3 docs/designs/restack-queue-provenance/pocs/edge-witness/prototype.py --self-test --fixtures-dir /Users/quentinmiao/code/agentfold/.git/agents/runs/2026-08-31-prove-the-correct-restack-queue-201c/scratch/edge-witness-poc/verified-29-scenarios
```

That retained run also ended with the same 29/29 and 9/9 summary. The scratch path is run
evidence, not a durable PR artifact; a reviewer can regenerate the deterministic object IDs
with the first command.

## Worked example: the distinction this POC proves

S1 starts with one live action at `C`. The old task tip `O` changes only a feature file.
The candidate side commits a claim, changes the declared non-queue evidence, deletes the
action at `M`, and replays the feature at `N`.

```text
C 3f07eff257fe21311d0da2b1ca1fe57fb6e34f6a
O 97db2eff747dbe84c3119b3bca4410bef3c43ef2
M 11128f74e4636c8288a7dcf00b9527b0af6bd3c0
N 9b53f36b908350c62e749529b7745da31945baa3
real deletion edge fe3c76ea75a08ad636256c11694b9d307be16d8a
                -> 11128f74e4636c8288a7dcf00b9527b0af6bd3c0
real-edge lifecycle/evidence problem: null
verdict: no finding
```

S2 has the same old-side ownership shape, but the candidate deletes the action while it is
still `open` and changes no evidence. The prototype locates the deletion but returns
`agent action was not committed as in-repair before deletion`, so the push remains blocked.
This is why ancestry can locate a supplier but cannot authorize it.

## Scenario evidence

Every row below is **VERIFIED** by an executable assertion in `--self-test`.

| Scenario | Result | Deciding evidence |
|---|---|---|
| S1 valid base resolution | no finding | exactly one matching candidate-side deletion edge passes the existing validator |
| S2 invalid base deletion | blocking finding | the real deletion edge has no committed `open -> in-repair` claim |
| S3 branch-owned action loss | blocking finding | the old tip authored the action and the candidate side has no matching deletion edge |
| S4 changed action | blocking finding | the candidate resolves the base incarnation, not the branch-authored identity |
| S5 mixed actions | exactly one finding, for Q2 | Q1 has a valid witness; old-tip-authored Q2 has none |
| S7 unrelated restack | no finding | the same action identity remains live at `N` |
| S8 fast-forward replacement | no finding | `O` is an ancestor of `N`, so no divergent continuity edge exists |
| S9 unrelated tip | snapshot error | `O` and `N` have no merge base |
| S9 non-commit tip | snapshot error | the supplied full OID names a blob, not a commit |
| S9 missing tip | snapshot error | the supplied full OID is unavailable |
| S10 pre-v1 old-tip action | blocking finding | activation on the new history cannot erase an old-tip obligation |
| compact valid deletion at N | no finding | the only valid witness child is exactly `N` |
| activation laundering | blocking finding | the pre-v1 real deletion edge is force-validated and lacks a claim |
| claimed-tip synthetic laundering | blocking finding | synthetic `O -> N` validation returns `null`, while the real edge lacks a claim |
| independent byte-identical incarnation | blocking finding | the old-tip action was authored after `C`, so a separate candidate lifecycle cannot borrow it |
| old delete/recreate with equal endpoints | blocking finding | the old-side parent walk sees both the deletion and byte-identical reintroduction |
| legal old resolve/recreate with equal endpoints | blocking finding | both side resolutions pass the lifecycle validator, but they resolve different incarnations |
| old rename away and back | blocking finding | two old edges expose the alternate path, so rename ambiguity cannot borrow authorization |
| old identity mutation and reintroduction | blocking finding | equal `C`/`O` blobs cannot hide the intervening action rewrite |
| candidate side delete, merge undo, mutate, delete | blocking finding | the only locally valid deletion is undone before `N`, so it is not causally responsible for final absence |
| merge-parent occurrence ambiguity | blocking finding | the raw production helper returns `null`, but two parent occurrences can supply the claim receipt |
| witness-child sibling with conflicting same ID | blocking finding | the claimed parent resolves A, but another parent of the deletion commit contributes different B under the same logical ID |
| disconnected byte-identical parent origins | blocking finding | equal path/bytes from independently created A and B have disjoint continuous origins |
| shared continuous parent origin | no finding | both carrying parents trace without interruption to the same earlier occurrence |
| three-parent shared-component deletion | no finding | three valid parent edges into one deletion child share exactly one continuous origin, so they form one causal event |
| three-parent disconnected component | blocking finding | two parents share one origin but the third is independent, so no single event component is proven |
| three-parent invalid edge | blocking finding | all parents share the origin, but one parent never committed the required claim |
| repeated incarnation | blocking finding | two valid deletion edges match, so the prototype refuses to pick one |
| 35-commit candidate history | no finding | one valid witness survives a multi-commit rewrite |

The claimed-tip case is the strongest security control. A claim reachable only from `O`
plus unrelated evidence bytes at `N` makes the synthetic edge look valid. The actual
candidate parent still carries the action as `open`, so real-edge validation refuses the
deletion. Replacing the current constant continuity finding with a synthetic-edge call
would therefore create a bypass.

The fresh verifier found a second bypass after the first milestone. `O` could author Q after
`C`, while the candidate independently authored byte-identical Q, claimed it, resolved it,
and omitted it at `N`. Real-edge validation passed, but that lifecycle belonged to a separate
incarnation. The repaired classifier now requires the old-tip action identity to equal its
state at every merge base before a valid candidate-side edge can authorize disappearance:

```text
C 5bc182839c03e7486d81839160129e86e325bd75
O 9dc0b5af6a1d047534d1a8cf8f64bff3332f873e
M 21bc63d1c4fac0fc724623d868c8474c9d1ea01e
N 507e8703b953c2dfc8262c5fe3b7c0c0f0b43840
candidate real-edge problem: null
old-tip provenance: old-tip-authored
verdict: blocking finding (different-incarnation-witness)
```

The next fresh verifier showed that endpoint identity is still insufficient. Q can exist
unchanged at both `C` and `O` while the old side legally claims and resolves the `C`
incarnation, then creates a new byte-identical Q at `O`. The candidate can also legally
resolve the original `C` incarnation. Both deletion edges pass the current lifecycle
validator, but the candidate must not resolve the new old-tip obligation. The classifier
now walks every old-only parent edge from each merge base to `O`; any deletion/recreation,
rename ambiguity, or identity mutation/reintroduction makes provenance discontinuous:

```text
C bfe9ba307457ca45cea3d6aa1b7dc9875481d8d4
O 4b0fecd47ab9f67692473c86a8312ab570c3cb98
M 22eba505f87e5883ba71a409e9c7f617eb4da8d9
N 2601032ebd3fb339533035bac0e69486957535cb
C/O queue blobs equal: true
old valid deletion f8162fbfd11a7476c816ab6ba48b1de0b1d6d064
                -> 1a18d1cade6246832c5cbee36c507faf7079af00
candidate valid deletion 22eba505f87e5883ba71a409e9c7f617eb4da8d9
                      -> 2601032ebd3fb339533035bac0e69486957535cb
old-edge events: deletion, reintroduction
verdict: blocking finding (different-incarnation-witness)
```

The third fresh verifier found the candidate-side mirror of that bug. A reachable side
branch can validly resolve Q, while a later merge keeps a carrying main parent's Q. The
merge therefore undoes the side deletion. A later commit mutates Q and `N` deletes that
different identity, so the earlier valid edge exists but did not cause final absence. The
repaired classifier now requires every state on every ancestry path after a witness child
to remain absent, and inspects every parent of a descendant merge rather than only the
parent on which the witness was found:

```text
C 97c4da1d6eed422292d5b4681834ac7671b2f9ab
O bd98e58c620c645505f4d3570b04f30443bcc773
M 0041220d2132c884410884e3e2f0f64fdee16a78 (merge)
N cd9d4ad48498a943489fcbc94fdd583b6f042486
locally valid side deletion 712c41ccf8426376a0c4d0848acf1c9b7479daf4
                         -> b6de978a29f87a1357c22d53c798feff7837b65f
carrying merge sibling a53107b2bd466461eb3b7f4dac0d7fd3125be834
post-witness events: merge-sibling-carries-action,
                     merge-result-reintroduction-or-survival,
                     identity-mutation-or-reintroduction,
                     later-deletion
verdict: blocking finding (invalid-post-witness-continuity)
```

A second merge attack showed that post-witness continuity is not enough if the claim receipt
before the witness is ambiguous. The merge result can carry byte-identical `in-repair` bytes
from an independently created root while another parent carries the original occurrence's
valid claim transition. The current production deletion helper walks both parents and returns
`null`, even though it cannot prove which occurrence the merge result selected. The POC now
walks backward from each witness parent and fails closed whenever more than one merge parent
can supply the same action occurrence:

```text
C 1910c07f289cecedd06775d194f40812b438de5d
O 4e70a05a587ecfc99638f6f472a49f3604150cc0
M fe6b8cae47062c5ba03d2b8d136adef30077082f (ambiguous merge)
N bdf696ec206e8a396f13508e7a670046a892f59b
independent in-repair parent c9614f211fa9e9be2f6b1ad3a3a5a1ceecc8ef26
original claimed parent      3e3b8857e3690b809f5e70fe6793a00529d4ecee
raw production deletion problem: null
pre-witness event: multi-parent-occurrence-ambiguity
verdict: blocking finding (invalid-witness-occurrence-ambiguity)
```

A fourth fresh verifier exposed a boundary neither the pre-witness nor post-witness walk
covered: the deletion commit itself. In this fixture, `C` adds inherited A with the POC's
explicit logical `Action-ID: Q`; one parent legally claims A, while a sibling based on `R`
independently adds unclaimed B at a different path with the same ID and different payload.
The merge deletes both. The raw production deletion helper considers only the selected A
edge sufficiently authorized and returns `null`. The POC now inspects every parent of the
deletion child and rejects any same-ID conflict, multiple copy, rename, or non-absent parent
that cannot be proved to carry the selected continuous occurrence:

```text
C  2944da8d4ea42b0452742ee28cfed7a91f7e42e1
O  a291d43b7a6a553de3db8cc8170d7cce0cc0a93c
P1 db0b7290718d6559c33afbc2c50eca61d426f04d (legally claimed A)
P2 91cc142371a42a130eb16024644fe76914ef57a2 (conflicting B)
M  57b7f889f254461869b6877c62e9cccb9a7f2eb3 (deletes A and B)
N  9a525559f19be56125aa791a66cf9ec3590149c9
raw production deletion problem: null
witness-child event: witness-child-sibling-same-id-conflict
verdict: blocking finding (invalid-witness-child-parent-ambiguity)
```

`Action-ID` is an experimental POC field used to make the cross-path collision explicit;
this repository has not yet accepted it as a production queue schema. The result proves the
need for a stable logical key or equivalent occurrence proof, not that this spelling is the
right production representation.

The next counterexample separates byte equality from occurrence origin at the shared old/new
boundary. In the negative DAG, root `R` lacks Q; A and B independently add byte-identical Q
at the same path, and merge `C` keeps one copy. The old tip and candidate both descend from
`C`; the candidate legally claims and deletes Q. Endpoint and lifecycle checks all pass, but
A and B are separate occurrences. The origin proof walks through merge base `C`, assigns A
and B their actual creation commits, finds an empty intersection, and blocks:

```text
A f6127dd2a049c78f5b0a026e0e9d41f957826d39
B eb5d36f7f9ce0760079e52823ea566b1d4c7bf76
C 8f56fe726c9d9a363dfd700bb34e3eaf0a04df1a (merge/shared boundary)
O 361ebbf50847e15f53bbc716ab88497e4f0c877b
M 344a9360f73f7a3276f06940c657da22697d2bbe (valid deletion)
N 8eab6a20addc9061be8ea64e49588f3546c0ebdd
parent origins: A -> A, B -> B
shared origin intersection: empty
raw production deletion problem: null
verdict: blocking finding (invalid-witness-occurrence-ambiguity)
```

The positive comparison starts with Q already present at S. Two parents fork from S and
carry Q unchanged before merging at `C`. The same recursive proof finds S in both origin
sets, so the later legal candidate deletion remains eligible instead of being conservatively
overblocked:

```text
S a89e24f18e466c1d9d439ae1b89f74c988dff26d (shared Q origin)
A 1058dab2f3dc2d6f49d2996838cfe3e393d9b3be
B b26e3ed41e860b1c1ed4f89378fe005e87af56b3
C ad47765e5e860146b0a8687f1c32e72bdda3d9d0 (merge/shared boundary)
O c9c23aa38e53e0ba6f698095f5e26ad56fd503e0
M 8b2f5481e445a0bf1684f9f222dbecac7f7fb8d8 (valid deletion)
N e665400d0b600622ec0ce26bc512418034e9a7f2
parent origins: A -> S, B -> S
shared origin intersection: S
verdict: no finding (valid-real-edge)
```

The same origin-intersection helper is used when the deletion child itself has multiple
carrying parents. Pre-witness traversal cannot stop at byte-equal merge boundaries. After a
deletion, post-witness continuity remains stricter: every relevant parent and result must be
absent, so a carrying parent is never made safe merely by sharing an origin.

The latest positive counterexample showed why raw parent-edge cardinality is also too
conservative. Q is created at `C`, claimed once at common commit `K`, and carried unchanged
through three forks. A three-parent merge `M` deletes Q and changes its declared evidence.
All three real parent-to-`M` edges independently pass the current lifecycle/evidence
validator, and each parent traces to the same continuous origin `C`. Those are three edge
observations of one causal deletion event, not three competing events:

```text
C 09c120b6af1878f676db2e7f1098bf37c992909d (shared origin)
K b6cadf1e8197a8c56f38dcb692ef0894254594bb (common claim)
P fe54887592b6e964b26feba9be1de859fd1b39e3
  0e188be74cc8fa9c9fc83213b307d452c2a16b0a
  0b48e5771d65e6eb5b0092027dd2dab247c45eea
M 1e777dee4d59f3baa1238bda3787073e35aac639 (one deletion child)
N 7d7c52c833a5c31ed2e7b976b8b1e5750026e053
real-edge problems: null, null, null
shared continuous origins: C, C, C
raw parent-edge verdict: blocking finding (ambiguous-real-edges)
grouped causal-event verdict: no finding (valid-real-edge)
```

The grouping key is the deletion child plus exactly one proven continuous-origin component.
It is admitted only when every carrying parent belongs to that component and every real
parent-to-child lifecycle/evidence check passes. Two executable negatives keep those
conditions sharp. With two C-origin parents plus one independently created occurrence, all
three edge validators return `null`, but the shared-origin intersection is empty and the
verdict is `invalid-deletion-event-component`. With three C-origin parents but one unclaimed
parent (`5316e913dd17da4d14dfcd6a166adbd048b659d8`), the component is proven but that edge's
real validator reports `agent action was not committed as in-repair before deletion`.
Repeated deletion children remain two events and therefore remain ambiguous.

## Executable negative controls

These controls run inside `--self-test`; they do not rely on another POC's summary.

The first control disables only the new incarnation-provenance condition. The new fixture
then returns the former `no-finding` false negative, so the run records one observed red:

```json
{"control":"observed-red-incarnation-provenance","damaged_classification":"no-finding","expected":"blocking-finding","status":"OBSERVED_RED"}
```

The second disables only the old-edge continuity guard. Despite byte-identical `C`/`O`
blobs and valid deletion edges on both sides, the stronger reincarnation fixture becomes
false-green. The emitted deletion and reintroduction events show the evidence the damaged
classifier ignored:

```json
{"control":"observed-red-old-edge-continuity","damaged_classification":"no-finding","endpoint_blob_equal":true,"endpoint_lineage":"inherited-unchanged-on-old-tip","expected":"blocking-finding","old_edge_events":["deletion","reintroduction"],"status":"OBSERVED_RED"}
```

The third disables only post-witness continuity. The scanner still emits the merge sibling,
merge-result survival, identity mutation, and later deletion, but the damaged classifier
accepts the earlier side deletion and becomes false-green:

```json
{"control":"observed-red-post-witness-continuity","damaged_classification":"no-finding","expected":"blocking-finding","merge_commit":"0041220d2132c884410884e3e2f0f64fdee16a78","post_witness_events":["merge-sibling-carries-action","merge-result-reintroduction-or-survival","identity-mutation-or-reintroduction","later-deletion"],"status":"OBSERVED_RED","witness_child":"b6de978a29f87a1357c22d53c798feff7837b65f"}
```

The fourth disables only pre-witness occurrence provenance. The raw production helper still
returns `null`, the scanner still emits `multi-parent-occurrence-ambiguity`, and the damaged
classifier becomes false-green:

```json
{"control":"observed-red-pre-witness-occurrence","damaged_classification":"no-finding","expected":"blocking-finding","merge_commit":"fe6b8cae47062c5ba03d2b8d136adef30077082f","occurrence_events":["multi-parent-occurrence-ambiguity"],"raw_production_problem":null,"status":"OBSERVED_RED"}
```

The fifth disables only deletion-child parent validation. The same scanner output still
names the conflicting parent and the raw production helper still returns `null`, but the
damaged classifier becomes false-green:

```json
{"conflicting_parent":"91cc142371a42a130eb16024644fe76914ef57a2","control":"observed-red-witness-child-same-id-conflict","damaged_classification":"no-finding","expected":"blocking-finding","merge_commit":"57b7f889f254461869b6877c62e9cccb9a7f2eb3","raw_production_problem":null,"status":"OBSERVED_RED","witness_child_parent_events":["witness-child-sibling-same-id-conflict"]}
```

The sixth disables only continuous-origin intersection and substitutes endpoint equality.
The two independent origins remain visible in the control output, the production lifecycle
helper still returns `null`, and the disconnected negative becomes false-green:

```json
{"control":"observed-red-disconnected-identical-parent-origins","damaged_classification":"no-finding","disconnected_origins":["f6127dd2a049c78f5b0a026e0e9d41f957826d39","eb5d36f7f9ce0760079e52823ea566b1d4c7bf76"],"expected":"blocking-finding","merge_commit":"8f56fe726c9d9a363dfd700bb34e3eaf0a04df1a","origin_mode":"endpoint-equality-only-disabled-guard","raw_production_problem":null,"status":"OBSERVED_RED"}
```

The seventh restores the old raw-edge cardinality rule. It false-blocks the valid
three-parent fixture as three ambiguous witnesses. The corrected grouping admits exactly
one event, while the disconnected-component, invalid-edge, and repeated-incarnation
negatives remain blocked:

```json
{"control":"observed-red-raw-edge-cardinality","disconnected_component_verdict":"invalid-deletion-event-component","green_classification":"no-finding","grouped_event_count":1,"invalid_edge_verdict":"invalid-real-edge: one or more real parent-to-child deletion edges are unauthorized: 5316e913dd17da4d14dfcd6a166adbd048b659d8: agent action was not committed as in-repair before deletion","legacy_classification":"blocking-finding","legacy_event_count":3,"legacy_verdict":"ambiguous-real-edges","repeated_event_count":2,"repeated_verdict":"ambiguous-real-edges","status":"OBSERVED_RED"}
```

The eighth calls the current production `candidate_paths_match_other_parent` helper against
S2. The helper accepts the evidence-free supplied deletion, while real-edge validation names
the missing claim:

```json
{"accepted_evidence_free_deletion":true,"control":"production-other-parent-is-evidence-blind","real_edge_problem":"one or more real parent-to-child deletion edges are unauthorized: bc2947eb5f97a3f68ac286a7e685883fd2936b66: agent action was not committed as in-repair before deletion","status":"PASS"}
```

The ninth computes its own queue-tree replay signature for S1 and S2. Both old deltas avoid
the queue, both replay deltas avoid the queue, and both candidates omit the path; only the
real-edge evidence verdict distinguishes them:

```json
{"control":"replay-tree-cannot-authorize","s1_evidence":{"message-queue/needs-agent/requests/non-blocking-s1.md":"valid-real-edge"},"s2_evidence":{"message-queue/needs-agent/requests/non-blocking-s2.md":"invalid-real-edge: one or more real parent-to-child deletion edges are unauthorized: bc2947eb5f97a3f68ac286a7e685883fd2936b66: agent action was not committed as in-repair before deletion"},"signature":{"candidate_path_absent":true,"old_queue_delta_empty":true,"replay_queue_delta_empty":true},"status":"PASS"}
```

## Cost

The prototype counts actual Git child processes and logical path-entry reads during
classification; fixture construction is excluded.

| Fixture | Old c/e | Candidate c/e | Witness-child e | Pre-witness c/e | Origin-proof c/e | Post-witness c/e | Path reads | Git processes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1, one action | 1 / 1 | 3 / 3 | 1 | 2 / 1 | 0 / 0 | 1 / 1 | 22 | 40 |
| S5, two actions | 2 / 2 | 3 / 6 | 1 | 2 / 1 | 0 / 0 | 1 / 1 | 36 | 46 |
| legal old resolve/recreate | 3 / 3 | 2 / 2 | 1 | 2 / 1 | 0 / 0 | 0 / 0 | 25 | 46 |
| candidate merge undo | 1 / 1 | 6 / 7 | 1 | 2 / 1 | 0 / 0 | 3 / 4 | 40 | 56 |
| merge occurrence ambiguity | 1 / 1 | 4 / 4 | 1 | 1 / 2 | 3 / 1 | 0 / 0 | 30 | 48 |
| witness-child same-ID conflict | 1 / 1 | 4 / 5 | 2 | 2 / 2 | 0 / 0 | 1 / 1 | 33 | 46 |
| disconnected parent origins | 1 / 1 | 3 / 3 | 1 | 2 / 3 | 2 / 2 | 1 / 1 | 34 | 56 |
| shared continuous origin | 1 / 1 | 3 / 3 | 1 | 3 / 3 | 3 / 2 | 1 / 1 | 36 | 60 |
| three-parent shared event | 1 / 1 | 6 / 8 | 9 | 9 / 6 | 15 / 12 | 3 / 3 | 124 | 142 |
| three-parent disconnected | 1 / 1 | 7 / 9 | 9 | 8 / 8 | 18 / 18 | 3 / 3 | 148 | 166 |
| three-parent invalid edge | 1 / 1 | 6 / 8 | 9 | 8 / 5 | 15 / 12 | 3 / 3 | 122 | 140 |
| long history, one action | 1 / 1 | 35 / 35 | 1 | 34 / 33 | 0 / 0 | 1 / 1 | 150 | 168 |

**VERIFIED:** these numbers came from the JSON emitted by the retained 29/29 run. Here `c/e`
means commits/parent edges scanned in that phase. **INFERENCE:** this straightforward
prototype costs `O(B + Hc + Q*(Ec + Eo + Ew + Epre + Eorigin + Epost))` logical reads, where
`B` is merge bases, `Hc` is candidate-only commits, `Q` is disappeared actions, and the `E`
terms are candidate, old, witness-child, pre-witness, origin-proof, and post-witness parent
edges. The process count is linear in the histories but repeats pre-witness and origin scans
for each carrying parent edge, which is visible in the three-parent rows. Grouping itself is
in-memory and adds no Git child process. A production implementation should enumerate
commit/parent pairs once and share cached immutable `(commit, path)` entries and origin sets
across all edges of one deletion child; this POC did not measure that optimized form.

## Strongest self-counterexample

The repeated-incarnation fixture legally claims and resolves one action, recreates the
same bytes, then legally claims and resolves it again. Both real deletion edges pass the
current validator:

```text
d8a34e362a57409cfe77b629e7e978579df92926
  -> fbbf7be8f8ee6810fa5dd60e9c2035df4eacc407
ff20bf79a817ce9fb7898f2e83aebfb49ac3b25a
  -> 99f867bc57f23dbb4de7b995a265bf4a732d1832
```

The prototype reports `ambiguous-real-edges` instead of choosing the final incarnation.
That conservative false positive is intentional, but it is also the clearest reason this
code must not move into production unchanged. Production selection needs an explicit
incarnation-causality rule and a fresh-agent attack against delete/recreate/delete histories.

## What is verified, inferred, and proposed

**VERIFIED:** this prototype works for linear restacks, fast-forward extensions, candidate
histories with 35 commits, mixed actions, full-OID object failures, a valid deletion at `N`,
the two laundering controls, a byte-identical cross-lineage incarnation, old-side legal
resolve/recreate, rename round trips, identity mutation/reintroduction, and one two-parent
candidate merge that undoes a valid side deletion. It also reproduces a raw production
false-green where two merge-parent occurrences can lend one claim receipt to another. It
also rejects a deletion whose sibling parent contributes a different payload and path under
the same explicit logical ID, even though the current production deletion helper returns
`null`. The POC's `Action-ID` is experimental evidence, not an accepted queue schema. It
distinguishes disconnected byte-identical parents from a positive merge whose parents share
one earlier continuously carried origin; both comparisons cross the old/new merge boundary.
It never unions origin components merely because the merge result's bytes match. It also
distinguishes three component-equivalent parent edges into one deletion child from three
edges split across disconnected origins or containing one unauthorized lifecycle. The
positive is admitted as one causal event only after all three real edge checks pass; the two
negatives and the repeated-incarnation control remain blocking. It imports the current
`queue_deletion_problem` authority instead of paraphrasing its lifecycle
and evidence rules. It emits full `C`, `O`, `M`, and `N` OIDs, every candidate witness, old
continuity edge, deletion-child parent, pre-witness parent occurrence, recursive origin proof,
and post-witness parent edge, plus the evidence verdict, expected verdict, human-readable
reason, and measured cost as JSON lines. Any mismatch exits nonzero.

**INFERENCE:** an exact candidate-side witness is a smaller and safer production boundary
than replay, patch similarity, or direct-parent state because it explains the result from
immutable Git objects and reuses the repository's existing authority. Confidence is high
for the linear scenarios, four exact two-parent merge attacks, one positive shared-origin
merge, and the focused three-parent comparison. General merge causality remains unknown
because one positive and two negative three-parent fixtures are not a proof for arbitrary
octopus, criss-cross, or multiple-merge-base histories.

**PROPOSAL:** a production helper should validate object availability, require the old-tip
action/path identity to match every shared boundary and remain uninterrupted over every
old-only parent edge, enumerate every candidate-only parent edge, match the complete old-tip
action incarnation, force the existing validator over the causal deletion edge even before
schema activation, inspect every parent of the deletion commit and reject conflicting or
unproven logical IDs, and prove the witness parent has one occurrence lineage across every
ancestor merge. Count causal deletion events, not raw parent edges: edges into the same child
may form one event only when every carrying parent belongs to exactly one shared continuous
origin component and every real edge independently passes lifecycle/evidence validation.
Any missing, conflicting, disconnected, or invalid parent fails closed. Equal child bytes
never join disconnected sets. After
the deletion, the occurrence must remain absent on every descendant result and every parent
of descendant merges through `N`. The helper should return a structured witness for
the human-facing finding and fail closed on unreadable, ambiguous, or unproven history.
The selection rule for multiple valid witnesses remains open and must be settled by the
merge/incarnation POC plus fresh-context review before implementation starts.

## What this does not establish

- It does not alter or test the production continuity call site.
- It proves a rename away and back fails closed; it does not prove an authorized one-way
  timing-prefix move.
- It proves one merge-parent survival attack fails closed and one exact three-parent
  merge-only deletion works; it does not prove arbitrary octopus, criss-cross, or
  multiple-merge-base behavior.
- It proves origin intersection for focused two- and three-parent fixtures; it does not
  establish a complete occurrence algebra for arbitrary merge histories.
- It uses an experimental `Action-ID` field to expose cross-path payload conflicts; it does
  not establish that field's schema, allocation, uniqueness, or migration rules.
- It does not choose the correct witness across repeated action incarnations.
- It does not simulate a shallow clone with both tips present but intermediate objects missing;
  it covers unavailable, non-commit, and unrelated supplied tips.
- It does not benchmark a production cache or representative large repository.
- It proves structural claim/evidence transitions, not the truth of evidence prose.

Before production implementation, a fresh verifier must reproduce this 29/29 command and all
nine controls, then attack the repeated-incarnation false positive and broader merge cases.
