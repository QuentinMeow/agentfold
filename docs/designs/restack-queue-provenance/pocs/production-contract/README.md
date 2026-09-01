# Production-contract provenance POC

No reader action is needed: this isolated POC passes all 49 prescribed real-Git
scenarios, three mixed-causal-source regressions, and all five damaged-mode
controls, without changing production code.

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
  authority edge. The POC adds no new claim, evidence, retry, pickup, or human
  response rule.

The final self-test produced this summary and exited `0`:

```json
{"aliases_passed": 4, "aliases_total": 4, "controls_passed": 5, "controls_total": 5, "failures": [], "git": "git version 2.55.0", "passed": 52, "python": "3.14.7", "summary": "PASS", "total": 52}
```

Environment: macOS 26.5.1 on arm64, Python 3.14.7, Git 2.55.0.

## Contract proved by the harness

The POC first requires exactly one merge base and requires it to equal the
declared `C`. It enumerates only `O N ^C`, once, with `git rev-list --parents`.
It never opens parents of `C` for normal classification. A dedicated damaged
control proves that reopening pre-`C` genealogy creates a false block.

Each immutable production identity maps to a list of paths in every snapshot.
Counts and paths remain visible, so duplicates cannot collapse into set
membership. Carrying histories must remain uniquely present from `C`; absent
histories must remain absent from the chosen deletion through `N`. Missing Git
objects, shallow required history, unrelated tips, and multiple merge bases
return structured `unreadable` or `ambiguous` results rather than absence.

The two event modes are disjoint:

| Mode | Authority | Propagation |
|---|---|---|
| `direct` | Every carrying parent-to-child edge independently passes the production deletion validator. | None. Neutral parents that never carried the identity are listed but do not supply authority. |
| `supplier` | Exactly one earlier real deletion event supplies authority to every continuously absent parent. | Every carrying parent-to-merge edge proves adoption only. A claimed carrier remains propagation and cannot lend its claim or evidence. |

Nested supplier events retain the original authority event and stable-deduplicate
the prior plus current propagation, neutral, and absent parent lists. Later
adoption cannot erase ancestry evidence recorded by an earlier adoption. For
each absent parent, the classifier records a stable ordered union of its closest
causal sources, keyed by source event child and tagged with the source verdict.
A sole common valid source with no competitor may authorize. A sole common
invalid source stays invalid. Multiple valid sources, multiple invalid sources,
or mixed valid and invalid sources are ambiguous and retain every participating
source's edges, parent ancestry, reason code, reason chain, and full source-child
OID. Invalid and ambiguous descendants remain traceable for later evidence but
never enter the authorization set.

A result emits `valid`, `invalid`, `none`, `ambiguous`, or `unreadable`, plus
full `C/O/M/N` OIDs, the production identity tuple, endpoint paths and
multiplicity, event OID, authority-edge validator results, propagation edges,
neutral and absent parents, reason code, and measured counters.

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
scenario total remains 52.

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
| P18 | seven `P18a`-`P18g` cases | missing tip, non-commit tip, unrelated tip, shallow history, missing blob, missing tree, and multiple bases all return `unreadable` |
| P19 | `P19-production-identities` | path-independent ordinary identity, payload distinction, typed generated retry, and multimap multiplicity asserted |
| P20 | `P20-lifecycle-types` | ordinary agent, human decision, generated retry, and task pickup use four production validator leaves |
| P21 | `P21-PCX-17c-squash-erasure` | invalid; squash contains no surviving claim edge |
| P22 | `P22-PCX-18-one-pass-many-actions` | 16 actions across 133 enumerated commits; one graph walk, eight valid and eight findings |

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
N   e0953c49e5c671bf03901dbba0ee002e66e12e99
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
| Queue snapshots requested | 10,828 |
| Snapshot cache hits | 10,825 |
| Distinct queue subtree reads | 3 |
| Git object reads | 297 |
| Object cache hits | 21,401 |
| Production identity calls | 32 |
| Production authority calls | 32 |
| `cat-file --batch` processes | 1 |
| Git processes, including production validator calls | 267 |

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
```

| Control | Baseline -> damaged | Status | C / O / M / N |
|---|---|---|---|
| `missing-all-parent-direct-validation` | blocking -> no finding | `OBSERVED_RED` | `d7dc739a275601572c26fadc522a2ae4b71d3b12` / `ff1d9fce8cf6d941f7e0210a9cc6b3380df94741` / `84115c60a389aebfc0cb9c89964539849e1540d3` / `bd005f27951b3bae6225e8cc736936db93667388` |
| `supplier-authority-borrowing` | blocking -> no finding | `OBSERVED_RED` | `8d565f19c072aa8f0cef381b3f0e8fc58029820f` / `41865c9def0f066b1d121b9882872ecf33bfe729` / `fe37d71173d0c2d5841f116326eacd8b75eab8cc` / `8579708e09425d6c4e09b9260991148f8ef3ed6b` |
| `identity-multiplicity-collapsed-to-set` | blocking -> no finding | `OBSERVED_RED` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` / `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` / `f75429c785808a191c0600345870097251ca8f8a` / `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` |
| `reopen-pre-C-genealogy` | no finding -> blocking | `OBSERVED_RED` | `cd13c47983b0624a824f5fc583f7de647b240504` / `03c76bf6661f670a705245479f406a1d3ba7b279` / `3258b9e2bac9ea4c40a95a8db2cfbdaf5c972b84` / `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` |
| `missing-post-event-continuity` | blocking -> no finding | `OBSERVED_RED` | `ec84d0800c660f6379b21cfd721122fa06162999` / `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` / `5b3f0ee9f157786e8392185afa848583d9af19bc` / `258e858010ccd1e43716ab0269faa86ae08808a7` |

## Commands run

```sh
python3 automation/install.py
PYTHONPYCACHEPREFIX=/private/tmp/production-contract-pycache python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control missing-all-parent-direct-validation
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control supplier-authority-borrowing
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control identity-multiplicity-collapsed-to-set
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control reopen-pre-C-genealogy
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --control missing-post-event-continuity
python3 automation/reconcile/reconcile.py --check
```

The installer and bytecode compilation exited `0`. The self-test passed 52/52
scenarios, 4/4 executable aliases, and 5/5 controls. Each standalone control
exited `0` with `OBSERVED_RED`. The reconciler exited `0` with zero blocking
findings and six pre-existing advisories about frozen human-action records. The
commit hook selected no repository test files because this directory is a design
record path.

## Nonclaims and tests not run

- The POC does not change or claim parity with the production reconciler's staged
  index path. PCX-21 staged/committed parity and PCX-22 unmerged-index handling
  remain production-integration gates and were not run.
- The POC does not prove that a remote ref update is prevented. Repository
  remote status is post-push advisory, so no push-prevention claim is made.
- Squash remains unsupported. P21 proves that a squash-erased lifecycle blocks;
  this POC does not invent a squash-stable receipt or patch-similarity authority.
- The full repository test suite was not run. The pre-commit test selector ran
  0/0 files because only this design POC was staged.
- No remote, hosted-provider, partial-clone, or production-scale performance test
  was run. The only cost claim is the measured 133-commit, 16-action fixture above.
- No production code, schema, task record, contract, dependency, adapter, or
  neighboring POC changed, and no branch was pushed or pull request opened.
