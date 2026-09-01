# Production-contract provenance POC

No reader action is needed: this isolated POC passes all 49 prescribed real-Git
scenarios, 68 focused contract regressions, and all fourteen damaged-mode controls,
without changing production code.

Before this POC, the proposed restack exception had no executable proof that it
could distinguish a branch's own deletion from an already-resolved deletion on
another branch. The POC now classifies one occurrence rooted at the unique merge
base `C`, calls AgentFold's production identity and deletion validators, and
keeps supplier authority separate from merge propagation. It is evidence for a
future production change, not that change itself.

## Result

The executable is [prototype.py](prototype.py). It creates temporary Git
repositories, commits real queue items, and imports these functions from the
worktree's current `automation/reconcile/reconcile.py`:

- `queue_action_identity(path, text)` supplies every action identity. The POC
  emits the full returned tuple and a diagnostic hash; the hash never decides
  identity or authority.
- `queue_deletion_problem(path, text, parent, child)` decides every lifecycle
  authority edge. The POC does not synthesize a claim, evidence, retry, pickup,
  or deletion verdict. A separate contract gate described below binds concrete
  old-tip human responses to those production-authorized edges.
- `queue_parent_state_regression_problem(old_text, new_text)` validates mutable
  lifecycle state when the exact production identity persists from `O` to `N`.
- `queue_mutation_problem(source, destination, before, after, parent, child)`
  validates every real carrying edge of a persisted candidate occurrence.
- `queue_frozen_skeleton`, `introduces_final_retry_notes`, and
  `pure_first_human_response` apply the production frozen-byte complement to
  those same edges.

The final self-test produced this summary and exited `0`:

```json
{"aliases_passed": 4, "aliases_total": 4, "controls_passed": 14, "controls_total": 14, "failures": [], "git": "git version 2.55.0", "passed": 117, "python": "3.14.7", "summary": "PASS", "total": 117}
```

Environment: macOS 26.5.1 on arm64, Python 3.14.7, Git 2.55.0.

## Contract proved by the harness

The POC first requires exactly one merge base and requires it to equal the
declared `C`. It enumerates only `O N ^C`, once, with `git rev-list --parents`.
It never opens parents of `C` for normal classification. A dedicated damaged
control proves that reopening pre-`C` genealogy creates a false block.

The declared selected range base `M` is a separate mandatory input. Immediately
after that one graph enumeration, and before snapshots, per-action identity
calls, deletion-authority calls, or event selection, the classifier verifies
that `M` is an available commit in the enumerated `C`-rooted ancestry through
`N`. Therefore `M` must descend from or equal `C` and be an ancestor of or equal
`N`; the contract explicitly permits both endpoint equalities. Missing and
non-commit objects return `unreadable`; readable commits outside the region
return `ambiguous`. Both failures emit `range_base_validation` with the full
`M` OID and reason, zero selected events, and zero identity or authority calls.

Each immutable production identity maps to a list of paths in every snapshot.
Counts and paths remain visible, so duplicates cannot collapse into set
membership. Carrying histories must remain uniquely present from `C`; absent
histories must remain absent from the chosen deletion through `N`. Missing Git
objects, shallow required history, unrelated tips, and multiple merge bases
return structured `unreadable` or `ambiguous` results rather than absence.

When the old-tip occurrence at `O` has a concrete human response, every real
carrying parent implicated in the event must preserve every concrete
response/binding field from `O`. This includes each direct authority parent and
both the authority and propagation parents of a supplier adoption. For a
decision this is the response field and value. For a review it
also includes the local review target and its content revision, plus the bound
`Reviewed revision` and terminal `Review outcome` when those were already
concrete at `O`. Fields that were still pending at `O` may be filled by the
candidate lifecycle. For `Review target` and `Review revision`, plain
case-insensitive `pending`, after outer whitespace is stripped, is the only
explicit pending sentinel. Backticks, blank or generic placeholders, suffixes,
and Unicode lookalikes are binding values and are preserved exactly. `Reviewed
revision` and `Review outcome` retain the production lifecycle's existing
pending/placeholder fill rules. The comparison is anchored to `O`, uses the same
production identity, and runs after the production edge validator. Candidate
parents may add values only for fields pending at `O`, and all concrete
candidate values must unify across the implicated parents. A mismatch turns the
event invalid while retaining the production edge verdict, full parent and `O`
OIDs, and both bindings. An unanswered review parent is neutral only when its
target and revision are still exactly production-pending. Once it publishes a
concrete target or revision, those fields participate even without a response.
An unanswered `O` likewise anchors any concrete published target and revision;
an ordinary unanswered decision still has no binding to copy.

Endpoint preservation is checked separately from Git rename detection. If the
same production identity remains at `N`, the classifier requires exactly one
occurrence at `C`, `O`, and `N`, then traces the live occurrence backward from
`N` through every implicated candidate carrying parent to `C`. Every real edge
calls `queue_mutation_problem` and the frozen-skeleton complement. A merge needs
at least one independently valid source edge; its other live carrying parents
must preserve protected bytes, committed state, and every concrete human review
field, while a truly pending review parent may accept a lifecycle fill supplied
by the valid source. A deleted gap, recreation, transient regression, conflicting
merge carrier, or protected hidden-byte change blocks even when `O` and `N`
look identical. The separate `O`-anchored comparison still prevents the
candidate lineage from replacing old-tip committed state. Production-valid
publication, retraction, pending fill, first response, and terminal transitions
remain allowed; multiplicity fails closed.

The two event modes are disjoint:

| Mode | Authority | Propagation |
|---|---|---|
| `direct` | Every carrying parent-to-child edge independently passes the production deletion validator. | None. Neutral parents that never carried the identity are listed but do not supply authority. |
| `supplier` | Exactly one earlier real deletion event supplies authority to every continuously absent parent. | Every carrying parent-to-merge edge proves adoption only. A claimed carrier remains propagation and cannot lend its claim or evidence. |

Nested supplier events retain the original authority event and stable-deduplicate
the prior plus current propagation, neutral, and absent parent lists. Later
adoption cannot erase ancestry evidence recorded by an earlier adoption. For
each absent parent, the classifier first locates its closest causal-source
wrappers, then intersects and unions the wrappers' canonical root keys. A direct
root key contains the tagged verdict, deletion child, and complete authority-edge
component. A valid supplier wrapper inherits that root unchanged; its adoption
child is evidence metadata, not a new root. Equal root keys arriving through
multiple wrappers merge every wrapper's ordered propagation, neutral/absent
ancestry, and reason/source-child records. A sole common valid root with no
competitor may authorize. A sole common invalid root stays invalid. Multiple
valid roots, multiple invalid roots, or mixed valid and invalid roots are
ambiguous. Invalid and ambiguous descendants remain traceable for later evidence
but never enter the authorization set.

Event selection computes the final-absence frontier before considering a sole
valid event. When the action is absent at `M`, every continuous causal root
that feeds that absence participates. Authorization requires exactly one
canonical valid root and no invalid or ambiguous competitor. Several supplier
wrappers of that same root merge their evidence and may authorize; distinct
valid, invalid, or ambiguous roots block. A branch that is already absent and
joins only after an authorized `M` is not retroactively causal. If the identity
actually reappears, or a later carrying parent otherwise breaks continuous
absence after `M`, the frontier extends to `N`. Reintroduced earlier and later
occurrences both participate.

If a supplier-authorized occurrence is later reintroduced and deleted again,
the classifier does not select only the last deletion. It finds the events in
the final-absence causal history and stable-aggregates every authority edge,
supplier propagation edge, absent/neutral parent, canonical root, and
reason/source-child record. Any reintroduction makes the result ambiguous even
when the later deletion independently passes production authority, so two
different occurrences can never authorize each other.

A result emits `valid`, `invalid`, `none`, `ambiguous`, or `unreadable`, plus
full `C/O/M/N` OIDs, the `range_base_validation` verdict, the production
identity tuple, endpoint paths and multiplicity, event OID, authority-edge
validator results, propagation edges, persisted mutation edges with production
and frozen-byte verdicts,
neutral and absent parents, canonical roots, stable reason/source-child records,
reason code, and measured counters.

### Worked supplier example

P12 starts with one action at `C`. One candidate branch claims and deletes it;
another keeps the same `C`-rooted occurrence. The merge adopts the first
branch's absence. The POC returns `no-finding` in `supplier` mode with these
disjoint edges:

```text
C  3a01d100e676a9a20f8dc545fed19be3419fb759
O  bc433c8ed8cda37d3813042f730b2f23d8e8d778
M  5f5714f1c3661031e2200b1e1a346f236055b90f
N  8dc6dbc10535cb058ee49c63a979d75966b7f248
authority   34af1523579ea4589da0f84550d509d34271129c -> 64a032aa6cab8206bedfaefb1dbee32ebe867942 (valid)
propagation bacb6b431fc91e0c51137a1f5d16f789f5ddecde -> 5f5714f1c3661031e2200b1e1a346f236055b90f
```

## S1/S2/S3/S12 executable aliases

The adjudication's S-labels are aliases for four existing P fixtures, not extra
scenarios. `--self-test` emits a `scenario_alias_inventory` record and compares
every observed field below with the literal expectations in
`SCENARIO_ALIASES`. An alias mismatch fails the whole self-test while the
scenario total remains 117.

| Alias | Maps to | Classification | Evidence status | Mode | Authority / propagation edges |
|---|---|---|---|---|---|
| S1 | `P1-direct-linear-valid` | `no-finding` | `valid` | `direct` | 1 valid / 0 |
| S2 | `P2-direct-linear-invalid` | `blocking-finding` | `invalid` | `direct` | 1 invalid / 0 |
| S3 | `P3-genuine-old-loss` | `blocking-finding` | `none` | `none` | 0 / 0 |
| S12 | `P12-merge-supplier-valid` | `no-finding` | `valid` | `supplier` | 1 valid / 1 |

The executable comparisons include the per-action finding boolean and the count
of invalid authority edges. S1 and S2 therefore prove opposite verdicts over
the same direct-event shape. S3 proves that absence with no candidate event
cannot be authorized. S12 proves the opposite supplier outcome: one valid
earlier authority edge plus a separate propagation edge returns no finding.

## P1-P22 coverage

Every row below is an asserted self-test case; an edge-role or verdict drift
makes `--self-test` exit nonzero.

| Contract | Executable case | Observed result |
|---|---|---|
| P1 | `P1-direct-linear-valid` | `valid direct`; one authority edge |
| P2 | `P2-direct-linear-invalid` | `invalid`; production validator names the edge |
| P3 | `P3-genuine-old-loss` | `none`; blocking finding |
| P4 | `P4-pre-C-identical-origins` | no finding; one post-`C` enumeration |
| P5 | `P5-duplicate-at-C` | ambiguous; multiplicity 2 and both paths emitted |
| P6 | `P6a-old-delete-recreate`, `P6b-candidate-delete-recreate` | both block on discontinuity |
| P7 | `P7-immutable-payload-change` | changed immutable payload is a distinct production identity |
| P8 | `P8-path-timing-move` | one-to-one permitted move preserves identity; paired payload mutation does not |
| P9 | `P9-direct-two-parent-valid` | `valid direct`; both parent edges validate |
| P10 | `P10-direct-invalid-parent` | blocks; retains one valid and one invalid parent verdict |
| P11 | `P11-direct-three-parent-valid` | `valid direct`; all three parent edges validate |
| P12 | `P12-merge-supplier-valid` | `valid supplier`; one authority and one propagation edge |
| P13 | `P13-merge-supplier-invalid` | `invalid supplier`; invalid authority edge is emitted |
| P14 | `P14-supplier-reintroduced` | ambiguous discontinuity |
| P15 | `P15-competing-suppliers` | ambiguous; both authority events emitted |
| P16 | `P16-PCX-08-invalid-supplier-claimed-carrier` | invalid supplier; claimed carrier remains propagation |
| P17 | `P17-post-event-reintroduction` | ambiguous discontinuity through `N` |
| P18 | fifteen `P18a`-`P18o` cases | tip/history/object failures plus missing, non-commit, unrelated, and after-`N` `M` values fail structurally; `M=C` and `M=N` pass the range gate |
| P19 | `P19-production-identities` | path-independent ordinary identity, payload distinction, typed generated retry, and duplicate multiplicity 2 emitted as blocking ambiguity |
| P20 | `P20-lifecycle-types` | ordinary agent, human decision, generated retry, and task pickup use four production validator leaves |
| P21 | `P21-PCX-17c-squash-erasure` | invalid; squash contains no surviving claim edge |
| P22 | `P22-PCX-18-one-pass-many-actions` | 16 actions across 133 enumerated commits; one graph walk, eight valid and eight findings |

### Selected-range-base boundary regressions

P18h-P18o make the `M` gate executable. The first six rows return before action
classification with no event and `identity_calls=0`, `authority_calls=0`. The
last two preserve the queue action and prove that the contract's endpoint
equalities pass the gate without claiming a deletion event.

| Case | C / O / M / N | Observed result |
|---|---|---|
| `P18h-missing-M` | `d06a8e1f62d588293f3bf70a91e8f1900aca1edc` / `3c929150f394845dad6e969d058706c5dc878be8` / `ffffffffffffffffffffffffffffffffffffffff` / `70d6e8e514a7e81d6a91a799fcfa66e0eae162de` | `unreadable`; missing `M` named |
| `P18i-noncommit-M-blob` | `9c80ff6bb92b21e4e2206832a0080f34730d303d` / `3dbbaa22aa15be990b38094b5172de55e436adcb` / `f3fd2c414ebecbd374165a57fb97777d7854881f` / `e2f94048ffe0bb5fea0b4fcfabfbf4cc93a26285` | `unreadable`; blob named |
| `P18j-noncommit-M-tree` | `06bad3cc92638141b3f5f528b1b191e909bdbf29` / `8eea7da51b06c93ff0be6ab37d90644249993f26` / `4b825dc642cb6eb9a060e54bf8d69288fbee4904` / `5d8fd9eaa9152b6cf9bc2df1506e01c8abb9c2ea` | `unreadable`; tree named |
| `P18k-noncommit-M-tag` | `79cd0a510242ca533cd60cc19dbd7486483ec5d0` / `b631c4387527a69c216c988af10f997629ee21e6` / `d04b0f4cb2a439d32b7025e18869178554ce9609` / `110ee672efbfe974b199b21f485d6d0d5bd0070d` | `unreadable`; tag named |
| `P18l-unrelated-M` | `5deac7dbb2f7af1347528f202d2dea6305a7eed0` / `c66670d8212839c869bfe1e669e5d883d47eb2e8` / `d4a8acb5380c5835b7dbc237a3e0042d2905eec6` / `530b2c8c7e8d9ec4ef440a046e37b58db35d5981` | `ambiguous`; outside `C..N` |
| `P18m-M-after-N` | `e4e34696b271e37e86dde938c3f771c9cfe4bb2b` / `31f51f6be37d39d514b002a0c290a8fd6299d9c8` / `3794feb6c65bb4e6f541ddc3c2fb1e4e15434a39` / `8043519a0136308dc2f1218806192609d3b74a26` | `ambiguous`; not an ancestor of/equal to `N` |
| `P18n-M-equals-C` | `7b3cf8dd0cfc307a8b957b539f71033e92063a4b` / `ae6ec2647ed53b0c6c516952e1db0fa2c1feb96c` / `7b3cf8dd0cfc307a8b957b539f71033e92063a4b` / `8f3df0dee8d186622cb4b9f8da6d0a575a3f6d03` | range `valid`; `none`, no finding |
| `P18o-M-equals-N` | `740bcad8cc95b46955d8d112d070d93646351a6d` / `bc321981f1a4d3b740ce79454ccaa0ccb474e31c` / `4fda9e18664e3ae611b1d17877b03fa941783cc5` / `4fda9e18664e3ae611b1d17877b03fa941783cc5` | range `valid`; `none`, no finding |

## PCX-01-PCX-20 attack coverage

The independent attack matrix is also encoded as assertions, not only fixture
names.

| Attack | Observed result |
|---|---|
| PCX-01 neutral parent | valid direct; two carrying edges validate and the neutral parent is listed |
| PCX-02 neutral plus invalid carrier | invalid direct; both carrying verdicts and the neutral parent are retained |
| PCX-03 foreign exact identity | ambiguous because the foreign occurrence is not rooted at `C` |
| PCX-04 several absent parents | valid supplier; two absent parents trace one authority event |
| PCX-05 competing later supplier | ambiguous `{D1,D2}`; both independently valid authority edges are emitted |
| PCX-06 nested supplier over direct | one original two-edge authority event remains disjoint from two propagation edges; both neutral parents and both absent-source OIDs survive in stable order |
| PCX-07 overqualified propagation | valid supplier; claimed carrier remains one propagation edge |
| PCX-08 invalid supplier plus claimed carrier | covered with P16; invalid supplier edge blocks |
| PCX-09 recreated claimed bytes | ambiguous discontinuity; the old claim cannot cross recreation |
| PCX-10 transient multiplicity | ambiguous at multiplicity 2; both transient paths appear in the reason |
| PCX-11 different payload, same path | Q-A supplier validates and distinct Q-B remains a separate finding |
| PCX-12 timing rename | valid supplier by production identity, independent of the permitted path move |
| PCX-13 conflicting human response | three-level invalid continuation retains the original conflict, one authority edge, three ordered propagation edges, and all neutral/absent ancestry |
| PCX-14 valid human supplier | valid supplier through the production human validator |
| PCX-15 generated retry | valid supplier through the generated-retry special authority |
| PCX-16 task pickup | valid supplier through task-pickup special authority |
| PCX-17 cherry-pick versus squash | complete K-then-D cherry-pick validates; D-only cherry-pick and squash block |
| PCX-18 one-pass many actions | covered with P22; measured counters are below |
| PCX-19 missing claim blob | first result `unreadable`, restored-object result `valid` in the same Python process |
| PCX-20 budget overflow | at limit returns normal `valid`; limit plus one returns `ambiguous` with zero selected events |

PCX-05's recorded OIDs make the competing events reproducible:

```text
C   d297f8d7d5f3557c94f944194e6da99c1c092c81
O   39f138bf6fdf1db76fe12a652664dbdd3fcb33e6
M   6bc1b1aa685794aa4f4c17625c59319fe8264ec1
N   5cc308cff656d4866cfd255d968e65ee17b58271
D1  d9b25781fbe23756d17ddd9c6e6f9c80167642ec
D2  80c729b26bdc5c57e7fd7fc3c1416edb84ebbeb9
```

PCX-06's two-level result emitted all nested ancestry with full OIDs:

```text
C          4fef7d2a64023363e13a455eddeac016838f651a
O          db0f6a1bdc43a8bccc8184e323867f7ed9aa04a0
M          ed75b619d125655b117d22c8cd53c268e8693b5d
N          2513214e5beaae7f3a289d4fae4018a00971c21c
authority  4740e90b648bb75107b039e0d603fe789dc57311
adoption1  c0b33ad455675edb5aa627274086f711e5582849
neutral1   70a2426569179f6772b355fde27e417cd08f9a94
neutral2   d897fdd58c0b376da50fff77b289b5b3d0e1d2e0
carrier1   0b50fc379841872baad3a4426a40e735d6d05810
carrier2   5a49655189c80be66569d2c9d0f9f28a513aa030
```

The final event's absent parents are the authority event then `adoption1`; its
neutral parents are `neutral1` then `neutral2`. Its propagation edges are
`carrier1 -> adoption1` and `carrier2 -> M`. Both authority edges share the one
authority-event child above, and neither overlaps a propagation edge.

PCX-13 exercises the invalid path through three supplier adoptions. Its final
reason retains `conflicting-human-response` at `adoption1`, then names each
later `upstream-invalid-supplier` adoption:

```text
C          58e15401aaba3e6f056f7dbaf6789c10d35ae553
O          1e790e17e8d0ba21ab1a7213d6e0e0fa2d12f047
M/adopt3   52419f64aecef7454ed6a37a29d085583ff75eaf
N          14707f668aecd10bb531aa6fa0ec57700d26844b
authority  bceaeebe51c25436265952f3b9afa6c9a7745a6c
adoption1  8e72a13292b567ab5d5d8ece80c4c232f14d1899
adoption2  819fc8dd0712aad77810b9ac82c7c1624214fd89
carrier1   6a0d26ac7cf32e178357f6d85d49dd3981026b98
carrier2   87e0359c1f7bb3578cf78ca24c42d0ea5b451244
carrier3   6cb0a022a513d3c72d0df2d5f80352fbe71bb9d0
neutral1   efed253a1c01456840b916c81818d8c08ad10399
neutral2   aff11ce760bd2ec6d93cdeef39a450cc6998c48c
neutral3   0cac705b7eb426e12e80d835cf76e71d75920851
```

The final invalid event emits absent sources `[authority, adoption1,
adoption2]`, all three neutral parents, and propagation edges `carrier1 ->
adoption1`, `carrier2 -> adoption2`, and `carrier3 -> M`. The original valid
human deletion edge remains the only authority edge and cannot override the
conflicting response carried by the invalid lineage.

### Mixed causal-source regressions

Three additional asserted real-Git graphs exercise the causal-source union that
the prescribed P/PCX fixtures did not isolate:

| Case | Observed result |
|---|---|
| `R3-01-two-invalid-causal-sources` | ambiguous; two independent `conflicting-human-response` sources retain two authority edges, three ordered propagation edges, three neutral parents, and four absent-source OIDs |
| `R3-02-invalid-valid-causal-competition` | ambiguous; one invalid adoption and one valid direct source both retain their authority, propagation, neutral/absent ancestry, and reason lineage |
| `R3-03-unrelated-invalid-does-not-poison` | valid supplier; an invalid deletion outside the absent ancestry appears nowhere in selected evidence |

The two-invalid output used these full OIDs:

```text
C           73373ac5106e43d8643b5b616268d77a5ca1d264
O           8f89d0fc4c063c0bbabb284434f74bcf244fb5d3
M           e7f081a1bf94edfa0f7bec6f5cd0953631515354
N           8ed846d60715d845a5e19ab6b299ce853a592614
authority1  3298fff9fce2f3fc3ebbd376028cae9ded66c7b5
authority2  8e26d51c111af7adbbe07af7017e319279d97c9c
source1     554be4701af24ac290d8bd6c5c3cc2917c415092
source2     9c6e72444535b5fcdb3d936d1ef4e0261514e0fe
carrier1    16d3a0e951f19c1537db4170ea1433d586c93eb4
carrier2    9da752810d7adfe967d48ea1a3451e256166f1ac
carrier3    e920f2aaef840688a8352d3f796a14ebd8c82b03
neutral1    291fae01a5ce5d6d601a6892ac0c5d76ccf974ba
neutral2    fd4e2a2d7ead4cba18280c374682fd597eb988d2
neutral3    e87aa1ec0d4a309775906d27669ebae40bc6b861
```

Its reason names
`conflicting-human-response@554be4701af24ac290d8bd6c5c3cc2917c415092`
and
`conflicting-human-response@9c6e72444535b5fcdb3d936d1ef4e0261514e0fe`.
The mixed invalid+valid result analogously names
`conflicting-human-response@d1035891cfb898b501d4c4358e0cda42fa0cfefc`
and
`valid-direct-authority@86400c66cf071a7d6d02a7391373b2ca471ecb91`;
its final adoption is `212aed04a9840447658dd22d468fbe33fd2867d8`.
The unrelated-source positive selected supplier
`2fe1bf184c6d0626a1622012129c5801c47d31f5` and excluded invalid commit
`a8ae4e0bf33ab580216e0ce83a4c5d79e66b7555` from its selected evidence even
though the invalid commit is reachable from `N` and its production authority
verdict was evaluated.

### Canonical-root diamond regressions

The r4 fixtures distinguish one deletion root wrapped twice from two genuinely
different roots:

| Case | Observed result |
|---|---|
| `R4-01-same-root-valid-diamond` | valid supplier; one root and one authority edge, with three ordered propagation edges and both wrapper envelopes retained |
| `R4-02-distinct-valid-root-diamond` | ambiguous; two valid roots and both complete envelopes remain visible |
| `R4-03-equal-root-plus-invalid-diamond` | ambiguous; the shared valid root collapses across wrappers, while the additional invalid root remains distinct with its failing production verdict |

The positive diamond produced these full OIDs:

```text
C           4e831314d34c2897a072cca5b58303d8fd0e7ddd
O           2ae7f29324bd8d6b29c1f7640602fe7ec9193b1e
M           01eb3e5ec92cb370e449ab8788842c6da54c8c80
N           a7bbf4b40d0a3322205e3d8407eee73b9b11ccc9
root        0d870542d2a2a42b5093b146d2245740fa456437
adoption1   05eb28ca77abe9062af6b586812bf1d5826523e6
adoption2   2e9c1be263ae8ef2e8a8b2d0aea9f9280688c3f8
carrier1    d70acd9d9fbb16b7690db3870d991831ac7c4471
carrier2    0126791301359b150774ad66054cab13f133d7b3
carrier3    5c1cf625b6c4b9894b0d9c32dec182853253961b
neutral1    de6e2d9ee44f6cb1603502078b88542ee4c2cdd7
neutral2    3a89de69ac2eb966fa10f51c60f10a98b64f34d2
neutral3    f855f6e72bab04fdd85ba2f25a4a76c7a1a966ac
```

Its single emitted `causal_roots` record is tagged `valid`, names `root`, and
contains the root's authority component. Its stable `reason_records` name
`[root, adoption1, adoption2, M]`. The absent ancestry is `[root, adoption1,
adoption2]`; propagation is `carrier1 -> adoption1`, `carrier2 -> adoption2`,
then `carrier3 -> M`.

The distinct-root negative retained valid roots
`294a23354c2b7009f017a0853af22b10223a9336` and
`7fc7a0d2d0d55eb62722301bd958f574d41347b2`. The mixed negative retained
valid root `c7e6eed4001a36d03480ed64b6cb67c3bbbe7e76` and invalid root
`94140cd414a88d470dba443360d8b55c35f02844`, including the production
validator's missing-claim problem for the invalid authority edge.

### Reintroduced-occurrence history regressions

The r5 fixtures isolate the final-history aggregation. Both begin with real
authority `K -> D`, adopt `D` through supplier propagation `P -> M`, reintroduce
the action, and delete the new occurrence. Both return `ambiguous` and retain
two authority edges, one propagation edge, absent source `D`, canonical roots
for both deletions, and reason/source-child records for `D`, `M`, and the final
deletion. The later invalid fixture records the production missing-claim
problem; the later valid fixture records a second passing production verdict,
but still cannot collapse two occurrences into one authorized deletion.

```text
R5-01 invalid later deletion
C          1e5dad973b3278ca8c12f3dd74f72250eaaf9f09
O          c63664276a141f3f60f61c9d404de201e6f8cf16
M          3b07620bd6ed19324c9ee2dc55474f10854dc1e1
N          d40a531fd9a0dacb986f9259ac6f94ec0d248faa
authority1 d097d2d4349754253439ed58633b35fbf5853341 -> 657f1c682a87519967522b7cdae62f344c3a4925 (valid)
propagation 88436bd443f79b863ddce9b04c9610992955e68a -> 3b07620bd6ed19324c9ee2dc55474f10854dc1e1
authority2 44cc5668629790c721576756a38b630d563c746a -> 4338a7869360b2e539dd905c7204c948d573f06b (invalid)

R5-02 valid later deletion
C          79b338b3ef54382a0ec95e87a7ba962b1ec7c20a
O          9c8b1418effb6889d14466e278a7987b7e7cfbc3
M          3b0a6316833b818079a00141bb5ef27df4a4bc36
N          fb0bff9778f436aed2a46f887eafb84e1c74ea5f
authority1 287db35c723666b4f76026d4df9a4957eb700fb6 -> 70c42629ff66371a7d94eca7e18596d5e0dc631b (valid)
propagation 295eee5d213e52511863f8a3208b832941959e86 -> 3b0a6316833b818079a00141bb5ef27df4a4bc36
authority2 e1127dd93fc3b2324b7181086232ce6946e44cbe -> b51f3158e90132b85b13544e650101185228505a (valid)
```

### All-absent frontier regressions

The r6 fixtures prove that a sole passing edge cannot hide another root feeding
the same absence at `M`:

| Case | Observed result |
|---|---|
| `R6-01-valid-plus-invalid-all-absent` | ambiguous; both authority edges, their valid/invalid root tags, event OIDs, reasons, and the invalid production verdict remain visible |
| `R6-02-valid-plus-ambiguous-all-absent` | ambiguous; the valid `C`-rooted edge cannot override a foreign/discontinuous root |
| `R6-03-two-invalid-all-absent` | ambiguous; both invalid roots and both missing-claim verdicts remain visible |
| `R6-04-same-valid-root-all-absent-wrappers` | valid supplier; two wrappers of one canonical valid root merge to one authority edge, two propagation edges, two neutral parents, and one absent root |

```text
R6-01  C 566072d117ff7a1e4309949f6a885bd8e26d65d2
        O 5dc5378fdc316aa30dce282d0388a438d755b067
        M c1d92f49ddecd5097d7db52863c2b8e990b43810
        N abe68c6bcfb89b4194e7d9f3ace08a58e985a450
valid     7a1ee6b0fe01d25adab3131239ad4f7728bae45b -> b3c7cbbaeba2bfa439cd71dea95572e8a2a29d31
invalid   566072d117ff7a1e4309949f6a885bd8e26d65d2 -> f94d0c965cca8ea6a8405fd160219a9f4ee6fee2

R6-02  C f61617485ff0160e37de559fe752c56ff3bcb5f7
        O 10a37a2bc559519d6d84f70850b0a78445c3d5ec
        M bae78a9473f3a719563bfac05f9a815f8003917b
        N 4ab46009954bb98c5f22629274722667dc21ca37
roots     59faf341cb5439564cb32ab17c841f121673c12b (valid)
          5e7f50d8bb733603dbe6f33ff13411f7090c5036 (ambiguous)

R6-03  C f5141f92b29541282cf1ec520470e8c604aeaa6b
        O eb354df4fb54776834a9dff53f51f496a2bb338f
        M b5c24e5f55b7a8e0a89d51599153e77ebbbf85b8
        N 8f769727f1c641bd2587115f2fbcda5fdda816d1
roots     dc00143829641a9ff403c040c4f3e1f864587df5 (invalid)
          2ec9cda06efaf587cc9a124d78ad122c947171c1 (invalid)

R6-04  C c4ad2cb41bff8803f0f3d5b81ea0cfd785c9aa59
        O c3b9fb54026383a350146fb2f25243c9e8c7cb01
        M 82463b399db3f3fb0aabd0ca1e0b82a61afb96fc
        N 7bf74330f432155c3c39eedbfc81fa72bface489
root      dbd3a072a00de50212cd93e44a31cb731ce70360
wrappers  b858978bbda2e6e8492f2678070a6ce9c34ec176
          4edb5c9b80bd4504e87b8381e8cb99521552faa1
```

## O-anchored human binding and adapter input

Seven real-Git fixtures exercise the added human binding. In all four conflict
cases, the candidate edge independently passed `queue_deletion_problem` with
`problem: null`; the POC blocked because the concrete response at `O` did not
match the authority parent. The identical-binding controls prove that the gate
does not block lifecycle-valid direct or supplier deletion.

| Case | C / O / K / D / M / N | Observed result |
|---|---|---|
| `R8-direct-human-response-conflict` | `92c80d9c65c7be349d0a6c663a6a2ea9c3c2397c` / `1dc4f0dc77aae1eefaef0bb443ec187ff1efb23d` / `986f7667dcc5b01542c1194c72cc446c4c45e5ae` / `2b7dacb87e24c729b4948de47f6d473c153fc210` / `2b7dacb87e24c729b4948de47f6d473c153fc210` / `cb29049ff107a9a11a4ec7babbdee21819518dd6` | `invalid direct`; `O=reject`, authority parent `approve`; blocking |
| `R8-direct-human-response-identical` | `2b79814b0bce6f1556c0b2724ade9d7bbb4bf939` / `b3879039d6d7168e89b3046e6e60e056460907c1` / `3a37fb283da1ae126bf4f24c7d08215f30d88bc5` / `f345727f01fdf252be3f622bac93c727f2c24605` / `f345727f01fdf252be3f622bac93c727f2c24605` / `2c2289035cfc91c73564f6a97b326ebca02be132` | `valid direct`; identical `approve`; no finding |
| `R8-supplier-human-response-conflict` | `255e448f3c735fefdcee3c07071c3d6bb6abb312` / `27927fe11bdeee043660e700c81e8cb3853c56bf` / `9d999de926a3b726c4f17fa4c1aa5f0ae1a9d036` / `d3616075eb04bd2c9b5208aceb05ca8e0b3e78c7` / `04af3169e321f7615236785dd2834296aff6748b` / `1fb9fc40da2d44e839830611cc20d0aee23c560e` | `invalid supplier`; `O=reject`, authority parent `approve`; blocking |
| `R8-supplier-human-response-identical` | `800658fac71a8c7fbc2d257bde57964cc96dcef9` / `f33b095abbf3c3e3225e0fbfc663b0a7f52d312b` / `80a4c49c8bc87882eaf02fc3e5b5a82dd2aac42e` / `da001fa3334685155798eb17efdee7b17ff02ae9` / `08a3ec18a07b71e5aa95e1651ae93ce0f0e6a8d7` / `e94946d2990fe3c67bc61676f66f90fab1b7a26a` | `valid supplier`; identical `approve`; no finding |
| `R8-review-binding-divergent` | `9b4889771f49a83cd02600a2de58fc5e6e8b8259` / `e3c594800cfe94f4f23c58060ae4ab31f50c078c` / `f78c058e2bf8e307365640a89d8dee7aaac1ae22` / `8f4cb69d5a3f4eac8d69165b54f73f45e53d1f98` / `8f4cb69d5a3f4eac8d69165b54f73f45e53d1f98` / `dc70864ec5e13a399d4966356b9803075681a0e6` | `invalid direct`; same response, different target and content revision; blocking |
| `R8-review-binding-identical` | `45b7550dbdc799efed73af109da57c6906d428a0` / `a3f97a3b22945e663eb10180bde5de3b7bf790fa` / `aeef03ecb0d57aac9c9d323ed80d7c4552c1b1be` / `92295fde0ac2b1fed4b26a6efbc0cbae86e81411` / `92295fde0ac2b1fed4b26a6efbc0cbae86e81411` / `b2dbe65f89982fb586b0fb5349454d80c7c53310` | `valid direct`; identical target, revision, and approval; no finding |
| `R8-review-binding-terminal-conflict` | `cd64224f775f16bc2099816c594012a9592f8536` / `356f3f37cdffaf8f6c568a158a32c478f55a0e13` / `f56e612abf60bdf946f45bb1e7e1454c59aa0956` / `317ee20aba90b31295ed5626eb1bd37f1926a011` / `317ee20aba90b31295ed5626eb1bd37f1926a011` / `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | `invalid direct`; same response/target/revisions, but concrete `O` outcome `rejected` versus candidate `approved`; blocking |

The divergent review compared fixture-local target A at
`sha256:2ab16346393dd555c10887e02261d9fa80124206e31437260fb5d50cc7185bd3`
with fixture-local target B at
`sha256:5ac4dea8ba9a26fa2e56de8e4ffb2d7fe0cf688e57fb6eeeb0091f9a399115bc`.
The positive fixture bound both sides to its fixture-local target A at
`sha256:371e751cdca327cb53062048f641bba3263084738230bdd8b24ae6cc4aecb484`.
The terminal fixture preserved both `Reviewed revision` values at
`sha256:2159f135c15139aa0fdbd35362a3dd949c47c2627bee2aae17edf746e6ba5b75`
and exposed the exact `rejected` versus `approved` outcome mismatch. The
identical fixture leaves those terminal fields pending at `O`; the candidate is
therefore allowed to fill them once during its production-valid folding claim.

### Pending review target and revision

Four r9 real-Git cells prove that an explicit pending target or revision at `O`
does not become a false immutable binding. Each candidate fills the field,
commits the same human response, folds the review, and deletes it on a real edge
for which `queue_deletion_problem` returns `problem: null`.

| Case | C / O / K / D / M / N | Observed result |
|---|---|---|
| `R9-direct-review-target-pending-fill` | `a4262ccefc9ede4932475bc002285d2a50c8ad90` / `a7ca8baea31e18d5a66c9866590838aa61b01c76` / `2bcdbeb26265a2e08394d310b3a46a41833a5133` / `b55151e1a8c959e07397fd35006ab4b98e466972` / `b55151e1a8c959e07397fd35006ab4b98e466972` / `7406c126a4a04f22492f7e1677d05be0f2c5951f` | plain target `pending` -> concrete target; `valid direct`, no finding |
| `R9-direct-review-revision-pending-fill` | `323d65ca92bcab39b2c0612a27b148e391cce838` / `ea123742664bc85265ab6385a846c020a8ca3e8c` / `a9e99679ebb7750092bd7ca6cf2dad939a4c510b` / `310feea03d098ab049b5b5c0c781134aef3281b1` / `310feea03d098ab049b5b5c0c781134aef3281b1` / `6f11bd5de26dda0bbf565ba63d829a72ef51360b` | plain revision `pending` -> immutable sha256; `valid direct`, no finding |
| `R9-supplier-review-target-pending-fill` | `a88ea4ed82ce9d444b54742625a56bdc9abad2ab` / `20cb6a6f44d996a53ee5b1885bc53f6ab176aa68` / `90de9bf54ef6fa4f307d424e1a40a3c730cb0a49` / `ec7e67775fd8b8569b164a34a42a6b8baefa8d82` / `7c9db45a3c694b3b6c80b01c1eec00d70a584caa` / `601d084d2fb4d533d8794dbfa14d530d1bd19dce` | plain target `pending` -> concrete target; `valid supplier`, no finding |
| `R9-supplier-review-revision-pending-fill` | `fe04e4837703b729500127432fb439f8714c4f95` / `e76da4ccabd64cc1cfa96050fff7486272a3336e` / `949c4fd1f3f130306e4182946157bcf81d01849b` / `34c2c8878a6abcd9b06b183029e57a69b3bf9e81` / `da736296c1764ede66977136251d3e78dca23f5b` / `77cebbd7a8d42d98fdb88db9452ced1cd3a27bb5` | plain revision `pending` -> immutable sha256; `valid supplier`, no finding |

Each direct cell enumerated eight commits and seven parent edges once, made five
production identity calls and two authority calls, and selected no propagation.
Each supplier cell enumerated ten commits and ten parent edges once, made five
identity calls and two authority calls, and retained one propagation edge. The
revision values filled by the direct and supplier cells were respectively
`sha256:7b0d8084905c6e81c7f74bf50eb38a2c22eac406092088111603b64855fc1575`
and
`sha256:5706f8e796fc78b6bf7465c994523dec4fe9240309bbdb51c0bda69dfe0e5b70`.

The executable assertions accept only outer-trimmed plain, case-insensitive
`pending`. They reject balanced or partial backticks, suffixes, blank/generic
placeholders, dotless-i lookalikes, and unrelated invalid values. The
pre-existing divergent target/revision and terminal-outcome fixtures still
block, proving genuinely binding old-tip bytes remain fail closed.

### Malformed review target and revision

Two r10 real-Git negatives prove that the narrow production sentinel cannot be
broadened. In both cases the deletion edge independently passed
`queue_deletion_problem` with `problem: null`, but the old value was not the
plain `pending` sentinel and therefore remained bound to `O`.

| Case | C / O / K / D / M / N | Observed result |
|---|---|---|
| `R10-direct-review-target-backtick-dotless-rejected` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` / `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` / `0f7fa628b211648e7f8d22e11e753ffdfe26e3ab` / `32c6405daf9887441afff5bc7ec846e3fb3e2096` / `32c6405daf9887441afff5bc7ec846e3fb3e2096` / `ba4edb8f323adba9645e47c2536f2b621bed7855` | backticked `pendıng` (dotless i) -> concrete target; `invalid direct`, blocking |
| `R10-supplier-review-revision-generic-placeholder-rejected` | `b13043f4864a963aee7af4e3e3a913313f9f7b19` / `9d96a7eecc2b34704ef588142e4b48111849f3a9` / `a4688c89cf2a68edd653dd3b8778713293d1c0b8` / `8b761c2ffd576357e869f02a2463d9b50f8f45dd` / `acbdd1a98c4ab70bf53867515f0fb86a2e1b8b0e` / `02371c1e8f0eebe4e567694cfe6677c8b872a7a8` | generic `______` revision -> immutable sha256; `invalid supplier`, blocking with one propagation edge |

The direct case enumerated eight commits and seven parent edges once, made five
production identity calls and two authority calls, and selected no propagation.
The supplier case enumerated ten commits and ten parent edges once, made five
identity calls and two authority calls, and retained propagation
`d2692c17d6bd2be654ebea449d86a841a08ad86e` ->
`acbdd1a98c4ab70bf53867515f0fb86a2e1b8b0e`. Its concrete replacement revision
was `sha256:62b8e9ca2b243a2fc6baf048001d518d73455c3829217d3703fede4cd2f524b9`.

### Implicated-parent and persisted-state regressions

Eight r13 review fixtures bind all concrete review fields across every parent
that carries the occurrence into a direct deletion or supplier adoption. The
three supplier negatives reproduce the independent target, revision, and
terminal-outcome false greens: the source authority edge still has
`problem: null`, but the propagation parent conflicts and the result is
`invalid supplier`. The matching direct fixtures block through either the same
O-anchored unification or the independently invalid production deletion edge.
Both identical-binding fixtures remain valid.

| Case | C / O / M / N | Classification / evidence / mode |
|---|---|---|
| `R13-direct-review-binding-identical` | `d6d18f0c56d196748c9a94adad1191e68722eb4a` / `7e0284f9a2354f44218502da59ca365cff918285` / `429a42042f2544e7c6a64e1cdd4085cd88f12118` / `88dc201a2aae2ad0b8984b58fff19f45c78d7859` | `no-finding` / `valid` / `direct` |
| `R13-direct-review-binding-target` | `8454b9025487d126acbb3eb278584199e4d93bc2` / `75d9c282afe629e2fee58b878ffe93481926e719` / `550cce0661417e0b707d14904559142d585333fb` / `74f92dd03eaf05333a9e7168644bbae38b7bb50f` | `blocking-finding` / `invalid` / `direct` |
| `R13-direct-review-binding-revision` | `f7d60f4ef43874a6e2045634265a8bb7968e07f4` / `e51c37206f2fa3f2d3a5ee9ff92aeaedc0aa431b` / `37fbca351cfb6d4d34d8fe2e8ad7c9a9e499cd5e` / `a4d2d52e8f40a5ba80cf350bd00db494c92c2eae` | `blocking-finding` / `invalid` / `direct` |
| `R13-direct-review-binding-terminal` | `32a00d09012a40145f9abdaedea2734348c68e5f` / `d784ca71704ac0bd18e1a70b45c18d1994353eb9` / `9bb9aeeaf1479c58354889ebbc41eb7c6a61cb95` / `6677edfd8778a755904939d01b070af66f32bcaa` | `blocking-finding` / `invalid` / `direct` |
| `R13-supplier-review-binding-identical` | `14976a93658e5bcfe9339368e77f82e77f31830d` / `ffc5d33bc00724fa377f13ce6ed824f6dc9fc02b` / `afc8edcc93e5de5da648126ad821357cd8500d2d` / `962821fb4d4faabe72c3b8e86823a5367aa3294f` | `no-finding` / `valid` / `supplier` |
| `R13-supplier-review-binding-target` | `874d2e356033d133cd409bc9deb8e93198d0ec78` / `adf1ce7876b84e595992f5865f871b59ea892234` / `d1e6f44ef7736fc9d695c8f5a4339e71216270d7` / `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | `blocking-finding` / `invalid` / `supplier` |
| `R13-supplier-review-binding-revision` | `52fe1848f1536143161e717bf436ee8c8b07df59` / `e7a884697094e9be1c876b78fc33d9e259d92149` / `200871b889045e16a784c3de722863123881f7af` / `8fd2e814f38bf145bd7c84d9e22a355056d40649` | `blocking-finding` / `invalid` / `supplier` |
| `R13-supplier-review-binding-terminal` | `e93ff6925d5008e9c95866628b410dda5b293e91` / `60538a926a9acd01f898ba0371ad5249c912f7fc` / `128875ca6b9fff728b2f964bd81eb8841229bcdc` / `1031e6315881cdc99376df52bcddc86a4427e920` | `blocking-finding` / `invalid` / `supplier` |

Nine more fixtures move one persisted identity without relying on rename
classification. The two response-removal/change negatives use large response
fields and make ordinary `git diff --name-status -M` report separate add and
delete records. The other fixtures use identity matching even when Git detects a
rename. Every candidate carrying edge is production-valid; the six negatives
block only at the independent `O` anchor. Unchanged state, pending review fill,
and a production-valid terminal transition remain clean.

| Case | C / O / M / N | Classification / evidence / mode |
|---|---|---|
| `R13-persisted-same-state` | `0d4f188e038977d78c48829a48b12354ffc8aa32` / `a3edb26d4a2069954d0459dd9ea503cc27833f61` / `6ed596b6e32ca919ed3622089a9a1217602659a5` / `edee50f1fe44db9136335db0de7e27ad442f4eca` | `no-finding` / `none` / `none` |
| `R13-persisted-response-removal` | `49d500f64d51f720b0decb65db3ad5163d4f72e4` / `69bbf3a1bec29fcf92121c581925bb092d1535ab` / `d7c174ae5a575350b4c3fcc426a89ceb15119b69` / `24126e616db515f5ee1d08d4f2da297b50e02f3a` | `blocking-finding` / `invalid` / `none` |
| `R13-persisted-response-change` | `68dfa83702f8aa1a82181785ff40b9e0eb0f2958` / `af35b452b83aa6f8fee2d3dcf01a951a83cc0f19` / `69a46a9c107d10ae18cef7347e0f0f832a1bd7ef` / `464115d4c500dda036c5592c6c8f21fe9a959e15` | `blocking-finding` / `invalid` / `none` |
| `R13-persisted-review-target-change` | `de7f303a3f48d8d27eb65e7388d0f8dd934b4e96` / `2c37567f76cece330ee8c4997c96aa2bcd1764e0` / `73f686b71fc4503ed9319e814339a8f086c79c40` / `4f6be0576ef37c17b25b0268542bf4003a7b56bb` | `blocking-finding` / `invalid` / `none` |
| `R13-persisted-review-revision-change` | `952a03b6b34abb531365195232acd149ec51e221` / `cc3bf0c5664ca51a1c1df82759aaa607efd30550` / `eec9f2c2db8266f1f219bb1a656ebd3d9f01a11f` / `344c8d4e0333b14fb5b21550528242614812a55b` | `blocking-finding` / `invalid` / `none` |
| `R13-persisted-review-outcome-change` | `103fdd9bd623d90d09b2193e9272b3980c80906a` / `2c3f7acfeeb385de256074091a38c9953ce7f1f9` / `0c32f4efcc0c588a53c02e34064c1013163f2921` / `c8a8b37e924d1e18c54dd5bea09d07191b6b0be6` | `blocking-finding` / `invalid` / `none` |
| `R13-persisted-claim-loss` | `5604e77ef241630dd284448a224de046d2caf460` / `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` / `215f27a473f8476dc01cc01efe69516a76346385` / `8702850ba2e7f56c29b16557c496adcaa627829b` | `blocking-finding` / `invalid` / `none` |
| `R13-persisted-pending-fill` | `6b710008b02a5c4b970a282ad2624b0384727292` / `5218487e636b8519c69f49d146acd9b7f8b25948` / `457f5f699f2bbe03994adec75f5a5bebca91125b` / `31a21eb1595bd8ebe46e55bb235d8d677edd6d58` | `no-finding` / `none` / `none` |
| `R13-persisted-terminal-fill` | `ba73b784939318c875041e869d49a08cfd88f440` / `b5ea69a78713ea41e8229125a90fa2718088c6f9` / `3e711d2f2bb5de235a037e4675fe93f3d124c9d5` / `8250a2475da8b2c1a0dfffd5ecbe3e73fdd9b838` | `no-finding` / `none` / `none` |

### Unanswered review and continuous persisted-state regressions

The r14 review matrix treats concrete Review target/revision fields as binding
even when the review response is still absent. A completely production-pending
carrier stays compatible, as does an unanswered carrier that publishes the same
binding. A different target or revision blocks. The independent 17-record r12
oracle now reports 14 safe controls as `PASS` and all three former false greens
as `NOT_REPRODUCED`; the independent six-case carrier oracle returns the expected
three no-findings and three blocking findings.

| Case | C / O / M / N | Classification / evidence / mode |
|---|---|---|
| `R14-direct-old-unanswered-carrier-same` | `c1a83b69fb7f04ea375aca7027b157dd9cc266ef` / `37d577cc2c265e8e7082bfd86dd156172db98c5c` / `23bfa540b7b2b710bc71dc8de3aa9cb7c8aeaeb7` / `ae63528ae1af829ced9c2f1b763cc6aeb8c054ec` | `no-finding` / `valid` / `direct` |
| `R14-direct-old-unanswered-carrier-target` | `0f221025b8224d465679596d3dfd44b6023371ca` / `d39ee31be16db2789928827c2e132a31e22b828f` / `ff2c698bac44b2bfb79623769f79914b9bb74216` / `9c07f77ec2836ec0f4222313e315b3ddc31c4ccd` | `blocking-finding` / `invalid` / `direct` |
| `R14-supplier-old-answered-carrier-pending` | `7f104616c4fd6c3d1f15d7467a7e0da9e164f6e7` / `6f1dba05d9dca3e3776da3c7005a83807190ae74` / `e3876d1bfc361db4849cbb0205ff484aa10633a2` / `0662f0827db1ad2e39f59626dd8d87f316b73421` | `no-finding` / `valid` / `supplier` |
| `R14-supplier-old-answered-carrier-same` | `d87b23dffb37c46a64f0f37fd10db886fc100532` / `a6ff10d32896ec2d87dad1696b24e07cc73ead65` / `8765211171ea8284a872f854a9bed3268e0d60ab` / `9f1c795a2f4fd1450d4d524f3f7adbdf0c496c52` | `no-finding` / `valid` / `supplier` |
| `R14-supplier-old-answered-carrier-target` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` / `8a2de576d9304a51988bfbd943749129f828f882` / `d5e3f69c296bcc8b6e99aefd9590e8012b85b37e` / `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | `blocking-finding` / `invalid` / `supplier` |
| `R14-supplier-old-answered-carrier-revision` | `9121f39bba512fa9fd762c3d07c93d1c11d5bc42` / `6d9c8b1bfed15a512d68db494efb71a2d0577f33` / `98e0e2378d9bb06282339cbc3a6a0e67c8154f53` / `0b0243e67b4d4635716eb2113f81419da982ba3c` | `blocking-finding` / `invalid` / `supplier` |
| `R14-supplier-old-unanswered-carrier-same` | `186d0ffca8ab62c6de1677780cb4153eced4fe53` / `b6e124010b1f74882864bdc3dc1fbd289fd5305c` / `6a00e16a8416c1572149fd45d4102d87cea7832b` / `e9e33f66742ae613b738497753ffb4957610b85e` | `no-finding` / `valid` / `supplier` |
| `R14-supplier-old-unanswered-carrier-target` | `9109e916c44dbeaa2bfe0e3b5497e9d98ef3e9a3` / `a09f2f2ed771008847609d177c72e0b1f62d8084` / `d76ee4b89ef81e391e3b7ce4265919166fe070f7` / `0c38b44e67a3ad27238aed8c8a667837aa7fc444` | `blocking-finding` / `invalid` / `supplier` |

The eight persisted-state fixtures below prove that the classifier follows the
live `C` occurrence through the candidate DAG rather than trusting endpoint
identity. Every result emits the real mutation edges, production mutation
verdict, frozen-byte verdict, roles, and full parent/child OIDs. The negative
cases catch hidden protected bytes, transient claim/review regressions,
delete/recreate, and conflicting merge carriers. The positives preserve the
production-valid review retraction, large first response followed by a D+A path
move, and a merge where another source supplies a pending carrier's lifecycle
fill.

| Case | C / O / M / N | Classification / evidence / mode |
|---|---|---|
| `R14-persisted-hidden-bytes-low-similarity` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` / `d115e7063e3ffad24a495c9ffae5d70ffaf81928` / `9d5788eb19005f0df4a1314b8ce08d5733b7a4cb` / `a47b7307d654cb07612ccd7b04f1c32ab874c475` | `blocking-finding` / `invalid` / `none` |
| `R14-persisted-intermediate-claim-regression` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` / `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` / `d5fff1649859ee16ec88b1c71a4b8a1cade69e03` / `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | `blocking-finding` / `invalid` / `none` |
| `R14-persisted-intermediate-review-regression` | `5fe7bc2ba01136ca7e91068de3c21394628d8616` / `ceeb45bc58cb8e6726517130e20fff034db993f3` / `6937469bf807de32150751925eab9747c97b9801` / `b7e814f11797fcf8cc10f0a41b0dd8f0849718cc` | `blocking-finding` / `invalid` / `none` |
| `R14-persisted-delete-recreate` | `32c778b5ec16afe676bcd2ce898c89388b28ea0e` / `68f01125491f31f259d6cc636bc2f818c9529571` / `e7d51374356e1865109e6556047a4bb02919e46e` / `0d272d85cea3703f4fdc3aedfa7e821374de51ab` | `blocking-finding` / `ambiguous` / `none` |
| `R14-persisted-valid-review-retraction` | `58a66e99ff34cdfa5e2bd150d68d5d6121b0cd71` / `03f6cd5ee859d98e6110b2554606ba655ea9b66c` / `ba95216a82bb0d53f1116f7e57f6f1499459a40c` / `75f7c3689154b3ecf8e5c67d467e338ab24a47cb` | `no-finding` / `none` / `none` |
| `R14-persisted-valid-first-response-low-similarity` | `b14ffe7afbd09ecdcf3fcdecbf99fcd42e5f9e59` / `dafb69000967fde6234bce7999767113def81c5c` / `44680a86ed369e379a1cd20eb759c8fa1005e019` / `690a6c7b5a5425bcd8a3abfa90b75c77ecbde966` | `no-finding` / `none` / `none` |
| `R14-persisted-merge-carrier-pending` | `01b493c655badddcf6641e8a7d21d3594a0cb5c3` / `74442946b6639f57e7167838a13cc286f39d3519` / `d9dd6fac07cb976806b98aa75b872664d32c899b` / `ca8939b406b7b2323fd08b044625639f5e80cb6b` | `no-finding` / `none` / `none` |
| `R14-persisted-merge-carrier-conflict` | `00a09440e320c344f9840d7939f97b5a72654aa1` / `521e76aa7253b7dc1214c2bbdca5c788a601e21d` / `efba97f7919902dbe9b3c7ffc9550918dae871a6` / `e2f3eacb8b4a86f383f8a76be26dac7e4966edad` | `blocking-finding` / `invalid` / `none` |

`R8-adapter-M-input-variants` runs three classifiers over the same committed
graph rather than changing the real adapter. Its OIDs are:

```text
C 4355a7786719d4f001028cb4d39a6348f5563a72
O 36143d1a641c4b1233ed872cf99c36a171a4d929
K 31a1e933998db49628eeb9621479a3cb984a7fb2
D bdb42c6aa3dbb72a2d9c1af9d6f83a0f021944a1
N a8e46d197e36d38637dfc0e22d7d1ce6d01d820e
```

| Declared M | Range / result | Identity / authority calls | Selected evidence |
|---|---|---:|---|
| `O=36143d1a641c4b1233ed872cf99c36a171a4d929` | `ambiguous`; blocking because `O` is not in candidate ancestry through `N` | 0 / 0 | no event or edge |
| `D=bdb42c6aa3dbb72a2d9c1af9d6f83a0f021944a1` | `valid`; no-finding direct | 2 / 2 | one real authority edge |
| `N=a8e46d197e36d38637dfc0e22d7d1ce6d01d820e` | `valid`; no-finding direct | 2 / 2 | the same authority edge |

Each run enumerated the five-commit, four-edge graph exactly once. This proves
the endpoint-equality behavior on that simple graph, not that `M=N` is a safe
general adapter fallback. A genuine restack that still supplies `M=O` fails
the POC gate; the explicit candidate-side `M` produces the expected safe
verdict. The POC does not alter the real workflow or adapter.

`R8-adapter-M-N-frontier-counterexample` replays the existing unrelated-invalid
source graph. The explicit candidate selection excludes an invalid source that
joins later, whereas substituting `M=N` widens the causal frontier and correctly
blocks. Both runs use this one graph:

```text
C                1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd
O                ba83bd926d133cee0384ae4b8fd577de5d14e835
valid deletion   2fe1bf184c6d0626a1622012129c5801c47d31f5
explicit M       15688654c25ae26d20dd9d4c248f7dbbafee0d15
unrelated delete a8ae4e0bf33ab580216e0ce83a4c5d79e66b7555
N                433bb31a23f524c2a61cd0084e0a1ecda0af8c3c
```

| Declared M | Result | Calls / retained evidence |
|---|---|---|
| explicit `15688654c25ae26d20dd9d4c248f7dbbafee0d15` | `valid supplier`; no finding | 2 identity, 4 authority; one valid authority and one propagation edge |
| endpoint `M=N=433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | range `valid`, evidence `ambiguous`; blocking | 2 identity, 4 authority; valid and invalid authority edges plus the propagation edge |

Each variant enumerated eight commits and nine parent edges once. Therefore the
adapter contract must supply the explicit selected candidate-side `M`; it must
not automatically substitute either `O` or `N`.

## Cost and budget evidence

The cost fixture made 128 unrelated commits and disappeared 16 actions. Eight
actions had real claims and eight did not. The POC classified the expected eight
as valid and emitted eight findings. These are measured counts from that run:

| Counter | Count |
|---|---:|
| Graph commits | 133 |
| Graph parent edges | 132 |
| Graph enumerations | 1 |
| Per-action history walks | 0 |
| Queue snapshots requested | 10,924 |
| Snapshot cache hits | 10,921 |
| Distinct queue subtree reads | 3 |
| Git object reads | 297 |
| Object cache hits | 21,595 |
| Production identity calls | 32 |
| Production authority calls | 32 |
| `cat-file --batch` processes | 1 |
| Actual Git child processes, including production validator calls | 135 |

The fixture OIDs were:

```text
C  df53962cd25ebbb38830454e977caf65252ce009
O  8533fdc2d343b168d822c683379bfabbb49c0d28
M  1e7ca201682935795c94620176f77dd50b6ec769
N  466dae5f060fd0aa74cf71db38fa694686afd7ae
```

The budget fixtures use a measured demonstration limit, not a proposed launch
ceiling. At 10 graph commits, the classifier returned its normal valid verdict.
At 11 graph commits with a limit of 10, it returned structured ambiguity,
selected no event, and made zero identity or authority calls. The result carries
`limit_is_launch_ceiling: false`; this POC does not guess a production ceiling.

The zero `Per-action history walks` counter is scoped to POC-owned traversal;
zero POC-owned per-action history walks is not a claim of zero total per-commit
history queries. Independent OS-launch instrumentation observed the same 135 Git
children: 132 `subprocess.run` launches and three `cat-file` processes. The 132
include one graph enumeration, one merge-base query, one revision parse, and 129
imported production `git rev-list --parents -n 1` queries. A production
integration must reuse the enumerated parent cache, eliminate those queries, and
set a measured process budget.

PCX-19 temporarily removed loose blob
`22c64f4979ae39fb51a881c576f38740bc78b7f3`. The first classification returned
`unreadable` with that OID. After restoration in the same Python process, a new
object reader returned `valid`, proving that a missing object was not cached as
absence. Its endpoint OIDs were:

```text
C  759e2f27b42fa1f3bf68d8b436eed022ee8f1f5c
O  90aed2b3f8214a269d6421e6f4fe63ad3a61b091
M  3d4fd278b276f3e142f45300789259c7dd862165
N  dd34454f3204840ae81e2f273772c00488e681ea
```

## Damaged-mode controls

Each command first runs the undamaged classifier, then enables one deliberately
wrong behavior. `OBSERVED_RED` means the damage changed the verdict in the unsafe
or unsupported direction that the control was designed to expose.

```sh
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control missing-all-parent-direct-validation
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control supplier-authority-borrowing
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control identity-multiplicity-collapsed-to-set
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control reopen-pre-C-genealogy
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control missing-post-event-continuity
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control sole-valid-ignores-invalid-root
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control omit-old-tip-human-binding
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control literal-review-pending-treated-concrete
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control broad-review-pending-normalization
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control omit-supplier-carrier-human-binding
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control skip-preserved-state-validation
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control omit-unanswered-published-review-binding
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control skip-persisted-frozen-skeleton
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control skip-persisted-candidate-continuity
```

| Control | Baseline -> damaged | Status | C / O / M / N |
|---|---|---|---|
| `missing-all-parent-direct-validation` | blocking -> no finding | `OBSERVED_RED` | `d7dc739a275601572c26fadc522a2ae4b71d3b12` / `ff1d9fce8cf6d941f7e0210a9cc6b3380df94741` / `84115c60a389aebfc0cb9c89964539849e1540d3` / `bd005f27951b3bae6225e8cc736936db93667388` |
| `supplier-authority-borrowing` | blocking -> no finding | `OBSERVED_RED` | `8d565f19c072aa8f0cef381b3f0e8fc58029820f` / `41865c9def0f066b1d121b9882872ecf33bfe729` / `fe37d71173d0c2d5841f116326eacd8b75eab8cc` / `8579708e09425d6c4e09b9260991148f8ef3ed6b` |
| `identity-multiplicity-collapsed-to-set` | blocking -> no finding | `OBSERVED_RED` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` / `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` / `f75429c785808a191c0600345870097251ca8f8a` / `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` |
| `reopen-pre-C-genealogy` | no finding -> blocking | `OBSERVED_RED` | `cd13c47983b0624a824f5fc583f7de647b240504` / `03c76bf6661f670a705245479f406a1d3ba7b279` / `3258b9e2bac9ea4c40a95a8db2cfbdaf5c972b84` / `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` |
| `missing-post-event-continuity` | blocking -> no finding | `OBSERVED_RED` | `ec84d0800c660f6379b21cfd721122fa06162999` / `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` / `5b3f0ee9f157786e8392185afa848583d9af19bc` / `258e858010ccd1e43716ab0269faa86ae08808a7` |
| `sole-valid-ignores-invalid-root` | blocking -> no finding | `OBSERVED_RED` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` / `5dc5378fdc316aa30dce282d0388a438d755b067` / `c1d92f49ddecd5097d7db52863c2b8e990b43810` / `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` |
| `omit-old-tip-human-binding` | blocking -> no finding | `OBSERVED_RED` | `cd64224f775f16bc2099816c594012a9592f8536` / `356f3f37cdffaf8f6c568a158a32c478f55a0e13` / `317ee20aba90b31295ed5626eb1bd37f1926a011` / `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` |
| `literal-review-pending-treated-concrete` | no finding -> blocking | `OBSERVED_RED` | `a4262ccefc9ede4932475bc002285d2a50c8ad90` / `a7ca8baea31e18d5a66c9866590838aa61b01c76` / `b55151e1a8c959e07397fd35006ab4b98e466972` / `7406c126a4a04f22492f7e1677d05be0f2c5951f` |
| `broad-review-pending-normalization` | blocking -> no finding | `OBSERVED_RED` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` / `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` / `32c6405daf9887441afff5bc7ec846e3fb3e2096` / `ba4edb8f323adba9645e47c2536f2b621bed7855` |
| `omit-supplier-carrier-human-binding` | blocking -> no finding | `OBSERVED_RED` | `874d2e356033d133cd409bc9deb8e93198d0ec78` / `adf1ce7876b84e595992f5865f871b59ea892234` / `d1e6f44ef7736fc9d695c8f5a4339e71216270d7` / `8c3e7d42c53baf018d30c895ecd64b799edb5d45` |
| `skip-preserved-state-validation` | blocking -> no finding | `OBSERVED_RED` | `5604e77ef241630dd284448a224de046d2caf460` / `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` / `215f27a473f8476dc01cc01efe69516a76346385` / `8702850ba2e7f56c29b16557c496adcaa627829b` |
| `omit-unanswered-published-review-binding` | blocking -> no finding | `OBSERVED_RED` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` / `8a2de576d9304a51988bfbd943749129f828f882` / `d5e3f69c296bcc8b6e99aefd9590e8012b85b37e` / `b952d0de4952cb720e3056abe78c7ad8ee52d50f` |
| `skip-persisted-frozen-skeleton` | blocking -> no finding | `OBSERVED_RED` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` / `d115e7063e3ffad24a495c9ffae5d70ffaf81928` / `9d5788eb19005f0df4a1314b8ce08d5733b7a4cb` / `a47b7307d654cb07612ccd7b04f1c32ab874c475` |
| `skip-persisted-candidate-continuity` | blocking -> no finding | `OBSERVED_RED` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` / `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` / `d5fff1649859ee16ec88b1c71a4b8a1cade69e03` / `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` |

## Evidence audit

The committed [audit_readme.py](audit_readme.py) is a standard-library-only
checker for this evidence. It reads a self-test JSONL stream and verifies all
447 README Git OID occurrences against their named scenario/control regions,
all seven fixture identity SHA claims, scenario and control result rows, the 20
PCX attack rows, measured counters, totals, aliases, controls, and nonclaims.
It rejects an OID that merely occurs in some unrelated record and rejects every
unmapped README OID. No historical-OID exemption is used.

Two fresh 133-record streams were generated in different scratch roots with
`PYTHONHASHSEED=1` and `PYTHONHASHSEED=777`. They had zero differing records and
zero differing fields. Their raw bytes happened to match in the tested macOS,
Python 3.14.7, and Git 2.55.0 environment, at
`f6bfffe4c8e5abb46c1532d421d349d7eea4e81c113907f46bcf866abf550dea`.
That raw digest is an observed replay result, not a portable contract: the raw
summary includes the Python and Git version strings. The auditor also defines
a canonical semantic stream by removing only those two summary fields and
canonicalizing JSON object serialization. It retains every Git OID, reason,
path, result, edge, and metric. Canonical semantic SHA-256:
`4aa6bd1a62537a8bbea28ec2f27730778b523a342af6ea917ed9a47d6c04e2c0`.

The ordinary two-stream audit output was:

```json
{"audit": "PASS", "checks_passed": 1552, "checks_total": 1552, "comparison": {"canonical_equal": true, "comparison": "PASS", "differing_fields": 0, "differing_records": 0, "raw_equal": true}, "counter_checks": 23, "failures": [], "fixture_sha256_claims": 7, "oid_occurrences": 447, "pcx_rows": 20, "pinned_controls": 14, "pinned_scenarios": 117, "record_rows": 103, "region_oid_claims": 447, "semantic_row_checks": 168, "unique_oids": 387}
```

The audit damage control makes three disposable README copies and changes one
current OID, the PCX-01 result, or the 133-commit counter. All three damaged
copies returned audit `FAIL`. It also changes one semantic result field in a
disposable comparison stream; strict comparison reports one differing record
and one differing field. The wrapper returned `PASS` with four `OBSERVED_RED`
records. These audit-only controls are separate from the fourteen classifier
damaged-mode controls and do not change the 117-scenario/14-control self-test
inventory.

## Commands run

```sh
python3 automation/install.py
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control missing-all-parent-direct-validation
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control supplier-authority-borrowing
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control identity-multiplicity-collapsed-to-set
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control reopen-pre-C-genealogy
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control missing-post-event-continuity
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control sole-valid-ignores-invalid-root
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control omit-old-tip-human-binding
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control literal-review-pending-treated-concrete
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control broad-review-pending-normalization
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control omit-supplier-carrier-human-binding
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control skip-preserved-state-validation
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control omit-unanswered-published-review-binding
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control skip-persisted-frozen-skeleton
PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control skip-persisted-candidate-continuity
root_a="$(mktemp -d /tmp/production-contract-r14-seed1.XXXXXX)"
root_b="$(mktemp -d /tmp/production-contract-r14-seed777.XXXXXX)"
PYTHONHASHSEED=1 PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir "$root_a" > /tmp/production-contract-r14-seed1.jsonl
PYTHONHASHSEED=777 PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir "$root_b" > /tmp/production-contract-r14-seed777.jsonl
python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --jsonl /tmp/production-contract-r14-seed1.jsonl --compare /tmp/production-contract-r14-seed777.jsonl
python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --jsonl /tmp/production-contract-r14-seed1.jsonl --damage-control
python3 automation/run_tests.py
python3 automation/reconcile/reconcile.py --check
```

The installer and bytecode compilation exited `0`. The self-test passed 117/117
scenarios, 4/4 executable aliases, and 14/14 controls. Each standalone control
exited `0` with `OBSERVED_RED`. The reconciler exited `0` with zero blocking
findings and six pre-existing advisories about frozen human-action records. The
first commit hook selected no repository test files because this directory is a
design record path. A commit-message-only amend then selected the full lane
because its staged diff was empty; all 16/16 repository test files passed.
The r14 evidence pass explicitly reran that full lane; 16/16 files passed in
48.24 seconds.

## Nonclaims and tests not run

- The exact pending comparison and its O-binding contract exist only in this
  executable POC. They mirror the production schema's accepted sentinel but do
  not change production review parsing, schemas, templates, or workflow behavior.
- The POC does not change or claim parity with the production reconciler's staged
  index path. PCX-21 staged/committed parity and PCX-22 unmerged-index handling
  remain production-integration gates and were not run.
- The POC does not prove that a remote ref update is prevented. Repository
  remote status is post-push advisory, so no push-prevention claim is made.
- Squash remains unsupported. P21 proves that a squash-erased lifecycle blocks;
  this POC does not invent a squash-stable receipt or patch-similarity authority.
- The pre-commit full repository lane ran 16/16 test files. No push lane,
  platform matrix, or hosted integration suite was run.
- No remote, hosted-provider, partial-clone, or production-scale performance test
  was run. The only cost claim is the measured 133-commit, 16-action fixture above.
- No production code, schema, task record, contract, dependency, adapter, or
  neighboring POC changed, and no branch was pushed or pull request opened.
