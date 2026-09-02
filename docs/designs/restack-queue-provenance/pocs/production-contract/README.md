# Production-contract provenance POC

This file is generated in full by `audit_readme.py` from the closed
`evidence.json` manifest. Do not edit observations here by hand.

## Result

The real-Git self-test passed 208/208 scenarios, 4/4 executable aliases, and 38/38 damaged-mode controls.
It imports and calls the worktree's actual `queue_action_identity` and
`queue_deletion_problem`, and `queue_mutation_problem`; it never invents
an Action-ID or lifecycle verdict.

Canonical evidence artifact: `sha256:6d0c70baf3a67dec25aa293ac3b0f2affa73a031df9d05322f651a5c6ce958e5`.
Canonical semantic stream: `sha256:880085db607329359821f6b3e5d57ba13f6a3dc8fcca8aba407f8e2cde7a0ab9`.
The raw JSONL stream is ephemeral and has no stored hash claim.
Evidence schemas v2 at commit `0b80c342feb310d73de6564aab2224a899f42486`, v3 at commit `7f4a1ffacd1cf8163f597daa186f801e9ce06a3a`, v4 at commit `cce76a037f1584ff7d37048cb4411bdf0f5aa907`, and v5 at commit `d12b799a2fa27b05a5ee2af1b422131856296b41` are superseded and burned by their later blockers; all histories are preserved, no identifier is reused, and this artifact closes `agentfold-production-contract-evidence/v6`.
The execution-bound runtime landed in commits `c32f470977735a63feaf377ca9290353d1520e0e` and `850d02587f7f812b7dde9667a39da80b4ce48764`; the latter binds literal refusal at the 68th parent token.

## Contract exercised

The classifier accepts exactly two immutable inputs, old tip `O` and new tip
`N`, and derives the unique merge base `C`. It enumerates the full C-rooted
`C..N` ancestry-path frontier once. Immediate outside-`C` parents remain
identity-discovery boundaries, never event children. A boundary parent with no matching identity is
neutral and its ancestors remain unopened; any matching identity there is a
collision. Production identities map to exact
path lists, so multiplicity cannot collapse to membership. O-side and C-descendant
carrying paths require one continuously valid `C`-rooted occurrence. Every
linear carry edge calls production mutation authority and its frozen-byte
complement; a carrying merge chooses one source and checks every other parent
as a binding/frozen-compatible carrier.

Direct mode requires every carrying parent-to-child deletion edge to pass
production deletion authority independently. Supplier mode requires one earlier
real deletion root, continuous absence to absent parents, live carrying parents,
and merge adoption. Carrying-to-merge edges remain propagation-only.

A supplier root carries a domain-separated `queue-supplier-support/v1` certificate
binding the real authority edge, raw non-action tree delta, every concrete path
referenced by the authoritative action, typed lifecycle obligations, and a
canonical digest. Adoption exact-copies the closest absent source's current
support projection. Earlier source-lineage evolution is allowed; adoption drift,
dropped evidence, conflicting projections, incomplete leaf coverage, or a failed
typed obligation blocks. Pickup accepts one uniquely claimed resolving task with
no pickup backlink; retry reruns its checker. Unsupported successor/reask and
boundary-review support dependencies fail closed.

Concrete human response/review binding is anchored at `O` and unified across
every real authority or propagation parent. Only outer-trimmed plain `pending`
is the Review target/revision pending sentinel. Final absence remains continuous
to the fixed `N` frontier; reintroduction and every invalid, ambiguous, or
additional causal root reaching `N` aggregate complete evidence and block.

Workflow transport is non-authoritative metadata around exact `O,N`: push uses
immutable event `before`/`after` and never `github.sha`; PR synchronize uses
top-level `before`/`after`, requires `after == pull_request.head.sha`, and makes
no API lookup. Created/deleted zero endpoints and an unavailable old `O` are
explicit coverage-unavailable results; the latter exits 2 with no fallback.

The ten former candidate-base endpoint/adapter scenarios are retired because
that endpoint no longer exists in the classifier API. Fixture-internal commits
remain landmarks only and cannot steer attribution.

## Absent-at-C strategy comparison

Strategy U is selected for this POC. When an identity is absent at C but live
once at O and N, it independently proves exactly one all-parents-absent legal
birth on each arm, followed by uninterrupted production-valid carriage. An
all-parents-absent candidate is legal only when its historical queue header
passes the production path/actor/leaf, delivery, field, lifecycle, context,
and exact identity-round-trip projection; repository-global reciprocity and
current-template presentation remain separate admission gates. Agent actions,
including generated retries and task pickups, must be born `open`; human
decisions and clarifications must be born `waiting` and unanswered; reviews
must be born unanswered in `awaiting-artifact` or `waiting`, never `folding`.
An outside-C carrier collides; a second birth, multiplicity, post-birth absence,
delete/recreate, invalid or frozen mutation, binding regression, incompatible
merge carrier, unreadable object, or endpoint non-regression failure blocks.
Absent merge parents that do not descend from the birth are neutral.

Strategy B layers a canonical birth-state witness on U. Its witness contains
only the production identity transcript, actor, leaf, production delivery
class, frozen skeleton, and initial lifecycle/review-binding projection. It
contains no queue path, commit, timestamp, mutable retry diagnosis, or operational
counter. Both strategies clean exact cherry-pick, independently identical birth,
generated retry, task pickup, and rename/timing-move fixtures.

U's typed birth gate rejects an agent action born `in-repair` and a human
decision born with a concrete answer under both strategies. B therefore adds
no protection for those former claim-at-birth examples. B does, however, block
a fully legal pair: one review is born `awaiting-artifact` and reaches `waiting`
through the exact production publication transition, while the other is born
`waiting` with the same binding and endpoint state. Every production mutation
check accepts that edge: `True`; every endpoint non-regression check is also clean: `True`. U stays clean and B blocks only on `origin-birth-witness-mismatch`, so B is redundant for illegal births and false-blocking for a legal restack; U is selected.
Both strategies claim only equivalent valid live incarnations. Neither claims
human intent, replay/cherry-pick provenance, or a relationship between independently
identical legal births. Equal B witnesses would still not prove that one birth
came from the other. Endpoint-only equality exists only in the
`endpoint-only-origin-equality` observed-red damaged mutant; it is not a normal
strategy branch.

| Fixture | U | B | Witness match |
|---|---|---|---|
| Normal base advance + replayed addition | `no-finding` | `no-finding` | `True` |
| Independently identical birth | `no-finding` | `no-finding` | `True` |
| Agent action born claimed (illegal) | `blocking-finding` | `blocking-finding` | `None` |
| Human decision born answered (illegal) | `blocking-finding` | `blocking-finding` | `None` |
| Legal review publication equivalence | `no-finding` | `blocking-finding` | `False` |

## Bound r17 review outcomes

The exact reviewer DAG is clean and record-bound by `sha256:a28ef43b85d7234baa2668a69eb022b42f0de6675eba8b4058fb2047ffb214e4`; its outside-C parent is neutral, its task patch replays exactly, and production deletion authority returns no problem.
R3-03 is blocking at the fixed N frontier with one invalid authority edge and is record-bound by `sha256:7edc60b01a3f1453c0a0c078e0e51c461b42b141200903ee246d4ef4ccf0d14e`.
The hidden-G attacker is clean at exit 0 and record-bound by `sha256:d39bcf90df4b04d1c4e7699a0506f487482645fa1d3b44243143d535d671a15c`: F is the neutral boundary, G carries the same identity in a unique missing blob, and G ancestry remains unopened.
R6-02 is explicitly dispositioned clean and record-bound by `sha256:76f7c24206d7be22dc1dd01c8c455fd7ed1d8193ede2255d832125d5a8189501` because its outside-C boundary is absent; the ambiguous ancestor behind it is not reopened.
All eight persisted-state attacker cases block in both parent orders: outside-C exact carriers retain multiplicity 1 or 2 as collisions, while valid and unauthorized absent C-descendant arms both remain deletion/reintroduction competitors.
The 64-parent outside-C octopus exits 2 transactionally and is record-bound by `sha256:5f8ae5a64816ad8a11920abbed3d4bc84daaccc45a364ebbf49b70f8e6327a91`; no action, edge, support, or carry-proof result leaks past the exceeded parent-token budget.
The P22 pre-charge case stops exactly at `object_reads=134>133`, keeps Git processes at 4, freezes later counters, and is record-bound by `sha256:43a59c9a572fee962162fe043d259a149540ccd98fdf27015334a439a087a8be`; its post-hoc damage reproduces the prior 10,973-snapshot/24,736-cache-hit full run.
Ten runtime exact/+1 pairs bind streaming graph bytes/lines/tokens, object payloads, flattened trees, dynamic support traversal, certificate serialization, origin-arm nodes/parent edges, and canonical birth-witness bytes. Every +1 refusal exits 2 with zero partial results; graph reads peak at 256 bytes per chunk and publish nothing on refusal. P22 separately observes exactly 129 imported production parent queries and 135 Git processes.
Unreadable Git objects use the stable typed reason `missing-or-malformed-commit:b5fcd8d0260da07b741462af3e3e2b49b546d600`. Every Git child is forced to C locale and UTC; the stable C/French results are equal even though the independent ambient diagnostic streams differ.
Before any projection or digest, all 249 raw rows must match the static recursive key/list/type grammar catalog `sha256:1d5c4784a6c2cb636dc0c57943a185b08cf820dc88b76e089e5c12ad2410cbbb`; an unknown top-level or nested field exits 1.
The parent-order pair has identical verdicts and the same role multiset:
`['compatible-carrier', 'source']`. The four persisted parent-order pairs and the origin-birth parent-order pair are also equal by semantic signature.

Reviewer-supplied reference OIDs (bound as review input, not regenerated fixture IDs):

| Role | OID |
|---|---|
| `C` | `030fe92b832b1bd2790182cab030b9dfd46ec6dc` |
| `F` | `233e9c9821300b9a1579c261a37b3829d0459250` |
| `K` | `920d63682562575383ac5adbaf33c5855d24a554` |
| `N` | `3a60d2c225bbcdf0619135111af9bc0a1120dbce` |
| `O` | `07418610247abbde975bd54ac937acf75ca02500` |
| `P` | `bda691d6bc1759421cc55925e8c350edea7d42be` |
| `deletion` | `d45b8657259492bbc12f6c32a2e81a7944357ce4` |

Boundary-attacker reference OIDs (bound review input):

| Role | OID |
|---|---|
| `C` | `52c16e3ace5b2fb945b2e8fc42b7485536ea1a47` |
| `D` | `595acd03b0c0f5cee214599587247d1115b2fc40` |
| `F` | `4afa966344cb99e6a72a10997b10572072e7cccb` |
| `G` | `b838a677f5753a45bff2d33f6e94b3a80cc92905` |
| `G_blob` | `88ce173dddc1914b0e7ccd52f5b89fb4742a713d` |
| `K` | `245d7de3ef54645d32fbcf8bbda7d69f426ce6d2` |
| `N` | `61d97651036a8cc9da10662ca7560bce14ce9ce5` |
| `O` | `5ff93e594d8689fe44774a9728a882c846e1833e` |
| `P` | `6564e680097653cebcc008a0bfee8587c644057f` |

Persisted outside-C collision reference OIDs (bound review input):

| Role | OID |
|---|---|
| `A` | `426b485efa3b5f85a678600795a20b1e91c6049f` |
| `C` | `843634959ac1156ef81ee7ccbf1f703261bbde1f` |
| `F` | `e10a4eb3208c44000e7363c2894e2a77b74828fa` |
| `N` | `af48cf172570a08d65c12dc467b2226dfbe8981a` |
| `O` | `c0ec07829f6aa4e1207a680a0354deb8a8f0c162` |
| `P` | `60f5448337b6f9a114c0231b86242474dd34873b` |

Persisted absent-arm reference OIDs (bound review input):

| Role | OID |
|---|---|
| `A` | `90de0b5af2ad8baec036ddaed2842eda86c2c556` |
| `C` | `0ddb561a40c84c0590d9abe8a3036521b239de25` |
| `D` | `161d7ed2d7bc121ce5331fed2e1ecb0dd650041e` |
| `K` | `f03d61cc931d7c860e7fd6f166c60d09596b48e5` |
| `N` | `76cf3354a913effec09cac7b183684159dfd0b84` |
| `O` | `17ef4a3d8c518778d62c635864670319efd03754` |
| `P` | `1847cdbe8298d5895ad566c03abc870064ca711b` |

Wide-boundary budget reference OIDs (bound review input):

| Role | OID |
|---|---|
| `C` | `b066accf737c901fd1ee314fcf310afb70c8fe87` |
| `N` | `412c2f8c5a8be93d1e0ffc5983d607bf750bb2f0` |
| `O` | `ba894e5a1c019e3b2c29ee8319eebfb4b0aaa9a3` |
| `P` | `b79ff7a4036270fed4a70d82ad226817ae94e662` |

## Input byte identities

| Path | Bytes | SHA-256 |
|---|---:|---|
| `docs/AGENTS.md` | 675 | `sha256:5342de9cada318428ea9b091e2434ad4d1e19e173a87295fe978651dc1a04b14` |
| `docs/designs/AGENTS.md` | 709 | `sha256:0e8c04dea40750971f0a567e84dd33ae5529960629abee9323234046105649e8` |
| `docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py` | 194740 | `sha256:88d6bfba1ee098292308732a3b8a2db2b172fd0c1acdfd24e8153c8f07c0374b` |
| `docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py` | 484867 | `sha256:f824e091119d277d12d9d06cf7ea9bc374f7d65d29a241741b9f215a3c7390b0` |
| `automation/check_action_projection.py` | 123062 | `sha256:bd9f73b79b3fac94f36d8248b4ce23c6fa7826da45d562a85bd9b1e14255e0c1` |
| `automation/markdown_semantics.py` | 33735 | `sha256:a5f58a99e739af4e3e61109caa880cb68dc739d93c727b74b8e2456220641c63` |
| `automation/reconcile/reconcile.py` | 499357 | `sha256:0436489bf3bb9a52ff80e6e36962393413d626d034b029e938876f4ddd84c0b7` |

## Seven fixture SHA bindings

| Claim | Scenario | JSON pointer | SHA-256 |
|---|---|---|---|
| `r8-divergent-old-target` | `R8-review-binding-divergent` | /details/old_binding/1 | `sha256:2ab16346393dd555c10887e02261d9fa80124206e31437260fb5d50cc7185bd3` |
| `r8-divergent-candidate-target` | `R8-review-binding-divergent` | /details/candidate_binding/1 | `sha256:5ac4dea8ba9a26fa2e56de8e4ffb2d7fe0cf688e57fb6eeeb0091f9a399115bc` |
| `r8-identical-target` | `R8-review-binding-identical` | /details/old_binding/1 | `sha256:371e751cdca327cb53062048f641bba3263084738230bdd8b24ae6cc4aecb484` |
| `r8-terminal-reviewed-revision` | `R8-review-binding-terminal-conflict` | /details/old_binding/1 | `sha256:2159f135c15139aa0fdbd35362a3dd949c47c2627bee2aae17edf746e6ba5b75` |
| `r9-direct-filled-revision` | `R9-direct-review-revision-pending-fill` | /details/candidate_value | `sha256:7b0d8084905c6e81c7f74bf50eb38a2c22eac406092088111603b64855fc1575` |
| `r9-supplier-filled-revision` | `R9-supplier-review-revision-pending-fill` | /details/candidate_value | `sha256:5706f8e796fc78b6bf7465c994523dec4fe9240309bbdb51c0bda69dfe0e5b70` |
| `r10-malformed-bound-revision` | `R10-supplier-review-revision-generic-placeholder-rejected` | /details/candidate_value | `sha256:62b8e9ca2b243a2fc6baf048001d518d73455c3829217d3703fede4cd2f524b9` |

## Scenario evidence inventory

Each record digest binds its complete canonical scenario JSON, including
all nested OIDs, verdicts, reasons, paths, counters, certificates, and
carry proofs, and workflow input contracts. It is not an OID-pool membership check.

| Scenario | C | O | N | Exit | Classification | Evidence | Mode | A/P/U/S | Validation | Record SHA-256 |
|---|---|---|---|---:|---|---|---|---:|---|---|
| `P1-direct-linear-valid` | `46109f507dba3eeb6191db457fc7848c415e8979` | `2819957948197a593fb1d0dc966e747c44db9ee5` | `029be55decf7d7f65826f86684cc8605d5d47b18` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:22d5714c783a6ad003a4a2f75735910073739d8ed937b75b761e4c86b7f0f4ca` |
| `P10-direct-invalid-parent` | `2ef716a2345dffac470956041b5245e20fbc8f98` | `1ac818d6b6ce87da87358e55015671ecf823dbb5` | `8f7e8c69c7ec6e4af250366114c90ecc24ce811d` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:6758df87fa043e1701be8e9e8e43f81a406807b073d95ad7d2ead3481a03a156` |
| `P11-direct-three-parent-valid` | `78ad042cef55f824658b367d8599c5523b4e601d` | `b5726dd5f1e717518fae85cf820fc7b134db83fc` | `ad16f6d1f31e155a41a236d51a7a396e54dd5ea3` | 0 | `no-finding` | `valid` | `direct` | 3/0/1/0 | `PASS` | `sha256:a3632ccbafacf93e412fc19816b8073d6b6c13d006c298d7957af4b4f21cff95` |
| `P12-merge-supplier-valid` | `3a01d100e676a9a20f8dc545fed19be3419fb759` | `bc433c8ed8cda37d3813042f730b2f23d8e8d778` | `8dc6dbc10535cb058ee49c63a979d75966b7f248` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:ef91cf5b414f5880da473fbb816e1227d3b33525c5d44db890dbe1fdd323686a` |
| `P13-merge-supplier-invalid` | `c9de2e4ee2e285093b2b1ae42b597989f5e2c267` | `898789857318c82970d920a105ee1a124474e155` | `9424f0b01381a9388d58b77c06efec9a59f0249f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:eac2c7aa7aae827d5dd2bb3c76a300fc668f66ebe5f2053189760ab610dddf50` |
| `P14-supplier-reintroduced` | `f340f1d750e747d6cf6a74dfac05146fd208f964` | `bf8487fe5085a4dc4b483f512c51ecd10cf7c253` | `14d300ed67dece9c599e5c0d096b708cc38bafa6` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:66fe63ca6e99645b386fae0de0d595b7e8f92b4d41106969c04280f6f7260aeb` |
| `P15-competing-suppliers` | `80b72ef13352057aa74028971730fbfb266b56f9` | `20a4f077a613c17b6e3f36d87f807bed9395d541` | `fe575f3eecc1f2b034bcbeb17a0021fce16bb82f` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/1/1/0 | `PASS` | `sha256:e4d982caf45907edb25414ebb38147d6b22f7e63669443c969b3c5f550553304` |
| `P16-PCX-08-invalid-supplier-claimed-carrier` | `b76e3dd3be1c4896d95f0ade31b63eada3ec7002` | `b756376fce02251f8036c1b1560d8c6c96dd0699` | `b23ca400da3968f74afc3b950ff4d4eb27307196` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:54c9688fb11344e6cbf26928e46480099a4ee45381baa471ebf58717f6bfb445` |
| `P17-post-event-reintroduction` | `ec84d0800c660f6379b21cfd721122fa06162999` | `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` | `258e858010ccd1e43716ab0269faa86ae08808a7` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:9872b048c86f180dc1431ed7a1099150ff0b37baad79cfb06bb854443c9fe7d2` |
| `P18a-missing-tip` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `907f5d5221680a4ff7eccd647bcf26bcd5e9c4d5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:5eda401661995e41de7f5d837f028d3ebf334fbc0f768f0c2bdee7b62fa2cc40` |
| `P18b-noncommit-tip` | `None` | `90db16de6c0119c0c924c80d206b1e80bc3d2331` | `22be33aff3fad75ef91ab1e1cae2f2f8da2987d3` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:c4e59b53c4eebc8b2435bc5434a004af7428e95f16e8b2f49cf00ea502933a02` |
| `P18c-unrelated-tip` | `None` | `22628ae24f01e250d30bb4cf9c2a7832f217677e` | `e46c2df2b7bdeeedf09b55b74a3745ea6d7f5139` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:80bf91ebc3c78977c05b81b52b160abb2ba9a4acdfb34ab3584ef080d95a4eba` |
| `P18d-shallow-required-region` | `None` | `e68bb90fcc341adde9f4372caff5ecc6f9b1e340` | `4303d2f9587973759de42362a6c20b4b48170ab5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:57f883c695c97edfc618995b6f87571cce589dbb5f3af75d136e8ea4efdcd46a` |
| `P18e-missing-queue-blob` | `a668e725d1233ee7d5930c077268d222dd27c277` | `8d7223893ec84e193595fe975a53d36f893502cb` | `ec9f29e0560c60e66700496cee9ce14858aebb4d` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:88720401bbceedf124a0cbf333571ac3087c68ec7fb1ff3c59c7075a00333637` |
| `P18f-missing-queue-tree` | `80ee9796305f288404f4aab5960193d8555c5e5a` | `61e6b7c9b52f0ea9ecb35c5bb8da8211aa7232d5` | `4f08ffcf2930d3d3a121b453b4b16a5b5f0bfa73` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:e3fb47f619a4b7cfdeab5953f7258febc521b1901042da413f8227016cbd216b` |
| `P18g-multiple-merge-bases` | `None` | `c9a1e28be75d020fa3222bfb2a5b04649329083e` | `8e067847820ccf0c7ed10b39c330162e1b10d880` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:857aab226cbd433ced93c7d4a4f7469c65e778283349f7d375df8dc74113c95f` |
| `P19-production-identities` | `5a986a543953cc623f320ced017dc315be4ac80e` | `7aed085d4fb3393205d57ad66e8d2834a0263bf7` | `7ceda0b76130db3d02ecd3c1d271b467980cf25e` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/6/0 | `PASS` | `sha256:9a2edbafb86311737ef2c080bec8cdafc29fe0fc16257a55740416ec7fa66117` |
| `P2-direct-linear-invalid` | `70b791b1e8a9bd24f58737e93a443451f8f0ca11` | `ab15090d6bc10c375e03aa38f1ca6aa87d672a98` | `b00411d0cb294fe228cef9fa6744869d212bff1b` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:5d76be7cfc8303e83d02331b6170e3e29fb13b2219c546ee6f926fc9bc6f896d` |
| `P20-lifecycle-types` | `4c9f5ab102d33b44f949f0490fa2ab6b1afef7d5` | `f01ebed3277db3c00a38c601d11a5423a35fc922` | `9de85b85f0f28f3594f681543732bdd2b76bee5a` | 0 | `no-finding` | `valid` | `direct` | 4/0/9/0 | `PASS` | `sha256:45986184caa74aa489aaaa134494e72f7cd04c01dc7cea7bcbc812a31168bdbe` |
| `P21-PCX-17c-squash-erasure` | `34448e62dde0da7a459c9f068a1929a11404bc60` | `67154541398ed536f17c169d282b151571b9031e` | `cdd5e979ba9eeb3e6caf97b05a182981178203bf` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:ba1f84ca167009e1ec378724b5c4e152100e69e3c52dceaf3dacfe260d97057d` |
| `P22-PCX-18-one-pass-many-actions` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 1 | `blocking-finding` | `invalid` | `direct` | 16/0/16/0 | `PASS` | `sha256:076bb89d3158061178cea53e7816f68b760bcb93eb1e110c7266bcadb1e11bb8` |
| `P3-genuine-old-loss` | `94db247b706f734bca553f86045fba8b98158a6c` | `5fa1eba2f8984af57952e6c083a0c455fc65d54c` | `5dffe2d077e79208c3e05ec0bfdd5de39600292e` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:3b14a98fff3d23e2fe594423ec8ed8f48c91c09e1737ee25189ca8de8185676d` |
| `P4-pre-C-identical-origins` | `cd13c47983b0624a824f5fc583f7de647b240504` | `03c76bf6661f670a705245479f406a1d3ba7b279` | `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:2c04d36a34f62e41a71dd48d65054845d676ffc936b6a2703fd460e7170207c6` |
| `P5-duplicate-at-C` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` | `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` | `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:d62601b5fee013e2bfa387f1ee5a3eef543a0190921c24a493f48cad3b376531` |
| `P6a-old-delete-recreate` | `8039e1a89ee29be7b3a79d4fda7aa15a8653058f` | `900438d3fe4393f0ea2f87aa4d8dfc1e188f5919` | `6781a4eaee80c8ebde47bef04c33dcb47e91bc98` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/1/0 | `PASS` | `sha256:38eb2eab79a76421dfab62a6c03619dba3219ce7e3d0cce2a394bae0d57c51aa` |
| `P6b-candidate-delete-recreate` | `b5161adf1ba6eeb99b2181aa264598f707d19a95` | `bfb4c66d18c551b23a8580132543db2357ddb4f7` | `ca9f44b0f38c99dc7c70093046ead1b19f464389` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:95c3cc490749b63f9719bdba85a406bbfb9a475195951c09700852d7a59ba518` |
| `P7-immutable-payload-change` | `43f673bf99a741dc37c6631d39bd5e9c037f7368` | `523cb1cb6e17b0e00b3bc3235618cfc0834d233f` | `03ae818dc35342d03432e7e25ca292808528ff3d` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:73bbe12dbe9c8f4ad41200210e6503d6692ff3fc9abe3f29cfc03e30f4028923` |
| `P8-path-timing-move` | `1c34d6196d22c53ce54eac5b2cbed46be8432134` | `f9bdb1fd1af9e2d3b5b405594d2ef37ab55ac025` | `cef78e9bb54e4b4318172d0a2b6881da3a4b8971` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:fad70e47168c3153c581436defc2c0e27170f355abdbdd4a59e1e7a6faf75dbf` |
| `P9-direct-two-parent-valid` | `074b437bb8582cabd4372ea380454368e8d81ab3` | `2380b58d4a6b687769359903f12100d69a543b2d` | `faa886162cc54c7c6544e33793a6e7f4342a90a0` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:c47729b891b7595b4379ab1e6cb2f8775631d7d9af133a002fe6418b1ff39ed1` |
| `PCX-01-neutral-parent` | `ee5d0eb6e70a978d7da73147f1faef9615f8624e` | `c4b177d1b0039326cd6592c90f7ce62e729ed3a8` | `acc6673079b122e2ae443cc91c4012c83344430d` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:59e260e53a01440e7dbcd129e8347dda3d9280278d00ebc25f3931c88e52dfc6` |
| `PCX-02-neutral-plus-invalid-carrier` | `b02a161fd6cd727aa2eb6bdf5ec43f5c5587e04d` | `78c77a131414cb7f196137896f9fd0080bb6552e` | `cf599de5003f9d108a979cb21f6d36c5c3785dee` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:cfc7857dab5aba7533c1410f944201a888e8ed024cbe8fe19fe206ad8907cb4e` |
| `PCX-03-foreign-exact-identity` | `35f271b5d18393dac59002bb0c0c794d3589659b` | `36313b4892aaa243fc2d01fd05ebc8e7ac0145e3` | `f7fb0303c3061d22daf61cdeb03cd67496639432` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:714d26540d332a7c97ac8971ce7d3e365a402b492dfaa89a3fab14aea883b084` |
| `PCX-04-several-absent-one-supplier` | `32c7576c4c4aca96bdad8162078e9b2a28d6ae33` | `c4cf7124f59fc3edbec373d87507aba76143cfd6` | `cb06b9b4e0a3ae842774d0f888ebb5f1bca53881` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:03348f4527763d7c54596fd760d7edfd981ccbbfa9b1085b5a8adfb69438ea82` |
| `PCX-05-competing-later-supplier` | `d297f8d7d5f3557c94f944194e6da99c1c092c81` | `39f138bf6fdf1db76fe12a652664dbdd3fcb33e6` | `5cc308cff656d4866cfd255d968e65ee17b58271` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:93b0e5b5fa5020f75ef357f41c39eab6305f56463db28c1535f7174518652c3b` |
| `PCX-06-nested-supplier-over-direct` | `4fef7d2a64023363e13a455eddeac016838f651a` | `db0f6a1bdc43a8bccc8184e323867f7ed9aa04a0` | `2513214e5beaae7f3a289d4fae4018a00971c21c` | 0 | `no-finding` | `valid` | `supplier` | 2/2/1/4 | `PASS` | `sha256:652d30f54f7885baeb0a45c569b43e95c6c82111120618983ab2688027fcd4e0` |
| `PCX-07-overqualified-propagation` | `e9920c69e87c8fadecea9dd6bfce80039a60619b` | `4eb27ecce806ae96e902a1c1cb1098fb7e8d7ba7` | `ea08bb6dd2a18266bfd6f436011c1cc610c4c8dd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:99b01d07c1773789cc0e7367c0a118638599c166e44c65a55d69c54ff5a7fef7` |
| `PCX-09-recreated-claimed-bytes` | `41008171d1f9c6afd397a17c3e5567e040d881e2` | `9e38900a6d2f2e3b48457b5fe92fb55cf68ef1ed` | `626d32b7150a4185dddc568c91f3f096abd5f4e5` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:fe7e97230796f040a7790478dd987ec2d73adbada646904926cd66759358cc58` |
| `PCX-10-transient-multiplicity` | `04b5c0356d29ee676d98d58fc639efaaa47278ea` | `cb082de1d3492e0b6e85918c5b1a4d2d600a110c` | `6dc48150188c026a1300d5fa19b065b1ad6a01aa` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:330d2758d78a58babaf1a43d32907edcb1526dd195059f382614cdec35126dc5` |
| `PCX-11-different-payload-same-path` | `9f7f5b9e5ce030055a6151bed80dfb6db1a94206` | `d45b35ca53a81320262faaeb7136fd081e8c1fef` | `78876b74b5d5c2cbdd3085a992a484c82280c769` | 1 | `blocking-finding` | `invalid` | `mixed` | 2/1/1/1 | `PASS` | `sha256:6344d4540e57b6a533aa5e44975568cf980c14b3e0e70818f3240ccc55ef0d2d` |
| `PCX-12-timing-rename-supplier` | `c81cd1ddc4c58f7e6d5b9bd7f0a626f972651c79` | `e89ed03c9f3c8d338d6b4f03dfee7d6994ce400e` | `97ae732aab6ceb15bba65fdc775f3b4d5115a3a2` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:782056845c30cbeb867612175d5387b4f96e845cc9a8b0a87033cf1e37d51cf8` |
| `PCX-13-conflicting-human-response` | `58e15401aaba3e6f056f7dbaf6789c10d35ae553` | `1e790e17e8d0ba21ab1a7213d6e0e0fa2d12f047` | `14707f668aecd10bb531aa6fa0ec57700d26844b` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/3/1/1 | `PASS` | `sha256:7941b8a1eddfe2330ef1225d4adee4e5aa48ee5be35f8840a556f3ca0c469f4c` |
| `PCX-14-valid-human-supplier` | `920e716ffd62703b03e21acd40423d34d60f165d` | `15ab9f04625ca7c4d6a8847bebaaa2b3169b5b69` | `36eaf058713764ea31d22a9cc74f800aaefbed1d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:4115e2a770743eec2b18d67c21c7084339de5141512e4b3bf8e49a9203869cfd` |
| `PCX-15-generated-retry-supplier` | `03cab3c249ed96db646bda0085596770b15f5801` | `44457ccb883890f47979a0504d52f5da066af287` | `338762e488c1ce489527bb173d9f8e2262c5f4c8` | 0 | `no-finding` | `valid` | `supplier` | 1/1/7/1 | `PASS` | `sha256:2b31c17e7cb1b61e8cfcd66ffe6c8f7a6697cf450106c94758a18f24793400d6` |
| `PCX-16-task-pickup-supplier` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:4da6f8cd272907d32d962e6036075ef11181b32f1f3fa89d7cbe0abd1cee38a2` |
| `PCX-17-complete-cherry-pick` | `33db81167dcecdaa77e3c6e97ea6305b99d13346` | `8385f0c8c1094932a794ebb94b32b4d872806cd2` | `855eaa3b813900caaa0e523baa198491cb4bc47b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:eed88c6a77fcc71337493a4d8640a29d5366f5b088785b996513fd0b6ad1d00e` |
| `PCX-17-deletion-only-cherry-pick` | `56008eecc6492c2c091a516834d675e283cc40bd` | `35b9163866f1c9cf6ab2435eeba3abfc0b9fd1fa` | `5da95440d2c9065d8b6f4506d2108a3f97bed539` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:5c1239c09b46b593251b8c926c4cfdd0e7b33793976b4a21e78c226cb89cf33a` |
| `PCX-19-missing-claim-blob-recovery` | `759e2f27b42fa1f3bf68d8b436eed022ee8f1f5c` | `90aed2b3f8214a269d6421e6f4fe63ad3a61b091` | `dd34454f3204840ae81e2f273772c00488e681ea` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:66a79e56ad3d7c57ee17fb7d1c7478d50700e1514a02d5bc98777f90de767f53` |
| `PCX-20a-budget-below-limit` | `c957293f54b1b960b7b7f351087c77ac874eb253` | `ad76497bc5fa23076fff741b5d419a2ccd714637` | `ce775146b901f12bc2c05d22f06343da4d2c66d0` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:2ed103201b3509bb7355fae71265467995e55042972cea9492740777a7758383` |
| `PCX-20b-budget-overflow` | `a018c90c3dbe1374339730ede5c7b76e21fee985` | `fb2043655802898f2561cc21431580a2609aef9c` | `06abdb0e773f19b6acc2ecf85d17e6c1770e7295` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:348c6942d52913c5662245941a883c39bfb3ce9aacc5eaf25a672202ff84e321` |
| `R10-direct-review-target-backtick-dotless-rejected` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` | `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` | `ba4edb8f323adba9645e47c2536f2b621bed7855` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/2/0 | `PASS` | `sha256:3e0859f8aa99c943eb7c31ef441fde59c0d0f9e0769ac21f67167e577788953f` |
| `R10-supplier-review-revision-generic-placeholder-rejected` | `b13043f4864a963aee7af4e3e3a913313f9f7b19` | `9d96a7eecc2b34704ef588142e4b48111849f3a9` | `02371c1e8f0eebe4e567694cfe6677c8b872a7a8` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 1/1/2/0 | `PASS` | `sha256:fffff94c54cf222dd4ff1abeee9f210197c2de8ea1beb3463571d5f35143c0d9` |
| `R13-direct-review-binding-identical` | `d6d18f0c56d196748c9a94adad1191e68722eb4a` | `7e0284f9a2354f44218502da59ca365cff918285` | `88dc201a2aae2ad0b8984b58fff19f45c78d7859` | 0 | `no-finding` | `valid` | `direct` | 2/0/4/0 | `PASS` | `sha256:4917539c274300951139ad85bf45d2211708545c2c087f459a6333fa74ab5f2c` |
| `R13-direct-review-binding-revision` | `f7d60f4ef43874a6e2045634265a8bb7968e07f4` | `e51c37206f2fa3f2d3a5ee9ff92aeaedc0aa431b` | `a4d2d52e8f40a5ba80cf350bd00db494c92c2eae` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:1a84ca6a21990a2399c91f5fdaff5f0ff08b720df1405b184a57ff25e26c4fdf` |
| `R13-direct-review-binding-target` | `8454b9025487d126acbb3eb278584199e4d93bc2` | `75d9c282afe629e2fee58b878ffe93481926e719` | `74f92dd03eaf05333a9e7168644bbae38b7bb50f` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:b208e8fd9d544eab39e0cde81cd5f7255ef20c3440bc5ff7d1e6fbd809da2143` |
| `R13-direct-review-binding-terminal` | `32a00d09012a40145f9abdaedea2734348c68e5f` | `d784ca71704ac0bd18e1a70b45c18d1994353eb9` | `6677edfd8778a755904939d01b070af66f32bcaa` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/4/0 | `PASS` | `sha256:82473f47c8e8bbb862462818383dd1194c6b8fc525e005039cb2718e491299ac` |
| `R13-persisted-claim-loss` | `5604e77ef241630dd284448a224de046d2caf460` | `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` | `8702850ba2e7f56c29b16557c496adcaa627829b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:5d457f3c6142a080665fb7419a233e3efe9035e064ddab7e78a116372de04fbb` |
| `R13-persisted-pending-fill` | `6b710008b02a5c4b970a282ad2624b0384727292` | `5218487e636b8519c69f49d146acd9b7f8b25948` | `31a21eb1595bd8ebe46e55bb235d8d677edd6d58` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:eca6a76fbe0afb3bc9c6fbfcbc826a34a73bcf8f7318511971141956d3039b27` |
| `R13-persisted-response-change` | `68dfa83702f8aa1a82181785ff40b9e0eb0f2958` | `af35b452b83aa6f8fee2d3dcf01a951a83cc0f19` | `464115d4c500dda036c5592c6c8f21fe9a959e15` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:b69606e5c1a8aa243224020d2d3f57243debcdca1d958fc6a257b58c36723971` |
| `R13-persisted-response-removal` | `49d500f64d51f720b0decb65db3ad5163d4f72e4` | `69bbf3a1bec29fcf92121c581925bb092d1535ab` | `24126e616db515f5ee1d08d4f2da297b50e02f3a` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:0e52a05217dddf0b995c6f48cf4a40244ef9034bfe8ce19df1f1602269b19cab` |
| `R13-persisted-review-outcome-change` | `103fdd9bd623d90d09b2193e9272b3980c80906a` | `2c3f7acfeeb385de256074091a38c9953ce7f1f9` | `c8a8b37e924d1e18c54dd5bea09d07191b6b0be6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:946697991a0bb7c3662a546d7cc77838dc0e212a8f0736e01c8d7a2126a0619b` |
| `R13-persisted-review-revision-change` | `952a03b6b34abb531365195232acd149ec51e221` | `cc3bf0c5664ca51a1c1df82759aaa607efd30550` | `344c8d4e0333b14fb5b21550528242614812a55b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:5917ce6cdbd2705b6bb33ca982380497b88266effe47d1aab0ef3957f084bf73` |
| `R13-persisted-review-target-change` | `de7f303a3f48d8d27eb65e7388d0f8dd934b4e96` | `2c37567f76cece330ee8c4997c96aa2bcd1764e0` | `4f6be0576ef37c17b25b0268542bf4003a7b56bb` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:e6820aac3ea01fb134ce5749ad025781a691106a42603d6b11144738932b6295` |
| `R13-persisted-same-state` | `0d4f188e038977d78c48829a48b12354ffc8aa32` | `a3edb26d4a2069954d0459dd9ea503cc27833f61` | `edee50f1fe44db9136335db0de7e27ad442f4eca` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:777eb47139ccc6d36ba861eaa1b1909d3c9e8f350859424084d52cb716c4c3c4` |
| `R13-persisted-terminal-fill` | `ba73b784939318c875041e869d49a08cfd88f440` | `b5ea69a78713ea41e8229125a90fa2718088c6f9` | `8250a2475da8b2c1a0dfffd5ecbe3e73fdd9b838` | 0 | `no-finding` | `none` | `none` | 0/0/6/0 | `PASS` | `sha256:6f8b526c09e54cde095597e0da43c69e910b73acdc81ed077f2b4d0ef22498ce` |
| `R13-supplier-review-binding-identical` | `14976a93658e5bcfe9339368e77f82e77f31830d` | `ffc5d33bc00724fa377f13ce6ed824f6dc9fc02b` | `962821fb4d4faabe72c3b8e86823a5367aa3294f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:8d6ca79f1d377c3bed5486c37a1e1c081d6939bb132743889435c81ce101d9ae` |
| `R13-supplier-review-binding-revision` | `52fe1848f1536143161e717bf436ee8c8b07df59` | `e7a884697094e9be1c876b78fc33d9e259d92149` | `8fd2e814f38bf145bd7c84d9e22a355056d40649` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:aef8622a6c3f545c5bf60a1c74480a144db1c28da9dc6553d450641d6fa22b51` |
| `R13-supplier-review-binding-target` | `874d2e356033d133cd409bc9deb8e93198d0ec78` | `adf1ce7876b84e595992f5865f871b59ea892234` | `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:1a7e1a517f4815145457d08d0b53d73388b8ee7c4b737b5b01d71c5d309054c0` |
| `R13-supplier-review-binding-terminal` | `e93ff6925d5008e9c95866628b410dda5b293e91` | `60538a926a9acd01f898ba0371ad5249c912f7fc` | `1031e6315881cdc99376df52bcddc86a4427e920` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:1f7c6c7a40f5fd8a274e98d0ddb6422f067b8cc1546c362d4e5473a672b02f8b` |
| `R14-direct-old-unanswered-carrier-same` | `c1a83b69fb7f04ea375aca7027b157dd9cc266ef` | `37d577cc2c265e8e7082bfd86dd156172db98c5c` | `ae63528ae1af829ced9c2f1b763cc6aeb8c054ec` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:95257415e5d83a33df314d1c7c9e39375fb975650024d390a400af4f951fbf1a` |
| `R14-direct-old-unanswered-carrier-target` | `0f221025b8224d465679596d3dfd44b6023371ca` | `d39ee31be16db2789928827c2e132a31e22b828f` | `9c07f77ec2836ec0f4222313e315b3ddc31c4ccd` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:e8e49f1f7f74bdcfa2835c774d17f0f58571fb1d30b52836e49feb21ed2aee8f` |
| `R14-persisted-delete-recreate` | `32c778b5ec16afe676bcd2ce898c89388b28ea0e` | `68f01125491f31f259d6cc636bc2f818c9529571` | `0d272d85cea3703f4fdc3aedfa7e821374de51ab` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:0834f519753fa8b69a21193ac38a2d6ebceedbb6334d6bce15ff09837950d57e` |
| `R14-persisted-hidden-bytes-low-similarity` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` | `d115e7063e3ffad24a495c9ffae5d70ffaf81928` | `a47b7307d654cb07612ccd7b04f1c32ab874c475` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/3/0 | `PASS` | `sha256:52857b3031b8fbc223888beb6a1cd66f2ee722be557321b216efc85817aefaa7` |
| `R14-persisted-intermediate-claim-regression` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` | `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` | `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:19b629b9867ebffd040d0a1ef65923c36e9cafc668ce4e564dcddf528fc4b87c` |
| `R14-persisted-intermediate-review-regression` | `5fe7bc2ba01136ca7e91068de3c21394628d8616` | `ceeb45bc58cb8e6726517130e20fff034db993f3` | `b7e814f11797fcf8cc10f0a41b0dd8f0849718cc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:a5fea078ddfecfb554fbb2193a03f4bc4f9212c071f2442e6dcc487c1454d704` |
| `R14-persisted-merge-carrier-conflict` | `00a09440e320c344f9840d7939f97b5a72654aa1` | `521e76aa7253b7dc1214c2bbdca5c788a601e21d` | `e2f3eacb8b4a86f383f8a76be26dac7e4966edad` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/8/0 | `PASS` | `sha256:9304b303ce7769609c02a55e0a9ba6aca722ccf04626072d633235fb95407643` |
| `R14-persisted-merge-carrier-pending` | `01b493c655badddcf6641e8a7d21d3594a0cb5c3` | `74442946b6639f57e7167838a13cc286f39d3519` | `ca8939b406b7b2323fd08b044625639f5e80cb6b` | 0 | `no-finding` | `none` | `none` | 0/0/8/0 | `PASS` | `sha256:9f4add12b53f3ef23a21274e32b335f0acc34661ea1c2d66cb25aabc626fd5bf` |
| `R14-persisted-valid-first-response-low-similarity` | `b14ffe7afbd09ecdcf3fcdecbf99fcd42e5f9e59` | `dafb69000967fde6234bce7999767113def81c5c` | `690a6c7b5a5425bcd8a3abfa90b75c77ecbde966` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:66c7077c6de6328f65b447d02c8d05a02058a8ca61598e88f279a5bbc7dc7437` |
| `R14-persisted-valid-review-retraction` | `58a66e99ff34cdfa5e2bd150d68d5d6121b0cd71` | `03f6cd5ee859d98e6110b2554606ba655ea9b66c` | `75f7c3689154b3ecf8e5c67d467e338ab24a47cb` | 0 | `no-finding` | `none` | `none` | 0/0/5/0 | `PASS` | `sha256:1d9bfb5430ee5185b8d6aa386d58aef76f1f7314404bcb37083a2ca405e172d8` |
| `R14-supplier-old-answered-carrier-pending` | `7f104616c4fd6c3d1f15d7467a7e0da9e164f6e7` | `6f1dba05d9dca3e3776da3c7005a83807190ae74` | `0662f0827db1ad2e39f59626dd8d87f316b73421` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:962ade0d5e95ddb9c79e6cd4c785dcb41b21f0166d93e99401b7b1dd9384ad6d` |
| `R14-supplier-old-answered-carrier-revision` | `9121f39bba512fa9fd762c3d07c93d1c11d5bc42` | `6d9c8b1bfed15a512d68db494efb71a2d0577f33` | `0b0243e67b4d4635716eb2113f81419da982ba3c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:977d3b998f5c3a5496592bf42f1489a475bce954cd458dab207027628b4c8b37` |
| `R14-supplier-old-answered-carrier-same` | `d87b23dffb37c46a64f0f37fd10db886fc100532` | `a6ff10d32896ec2d87dad1696b24e07cc73ead65` | `9f1c795a2f4fd1450d4d524f3f7adbdf0c496c52` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:ac870b257bcd9d48a9df790f19eece8d1e32bf352cc9352a4595db1d16a35695` |
| `R14-supplier-old-answered-carrier-target` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` | `8a2de576d9304a51988bfbd943749129f828f882` | `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:5f53a4345d1d64639f5df9720ca7987218516c9078743633bf80c747a105c099` |
| `R14-supplier-old-unanswered-carrier-same` | `186d0ffca8ab62c6de1677780cb4153eced4fe53` | `b6e124010b1f74882864bdc3dc1fbd289fd5305c` | `e9e33f66742ae613b738497753ffb4957610b85e` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:efb1abba3d6bea99fd40e4fb546fd3fa7e739609bacdadfeee786e067e1eba70` |
| `R14-supplier-old-unanswered-carrier-target` | `9109e916c44dbeaa2bfe0e3b5497e9d98ef3e9a3` | `a09f2f2ed771008847609d177c72e0b1f62d8084` | `0c38b44e67a3ad27238aed8c8a667837aa7fc444` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:ccbecbfbc9a6329712f7adeafb429fab2616207d8b9dff23b6a8174ab890d736` |
| `R15-old-continuous-preserved` | `9972c0979b118b85b5c9d80a811679b41840910b` | `6e29170cbd7791baf6f74923a50387a9359979e1` | `316e8cd76611658ad9587c73e54cbfb6f3c9f379` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:1765f8983b560cdf9216d18ba394b56ef11a42ae082914c5b286d6fea6a0589b` |
| `R15-old-hidden-bytes-restore` | `600ae7430233c349c25bbe4ab0f9f8fb55e7c92e` | `023e0594e4a6d2f3403635decbac7a9d90ec06f0` | `20096f8d2a62bfe7e6990d90b91135ef249879c6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:50f48b36491fbc2ef7e30e56c0c486505aa8abb7aa314e3c1b3e17945c1a3c00` |
| `R15-old-human-binding-restore` | `ed9337d8d288a493c724a71081e4db71972e2e08` | `1d8e4411979ce8ea8dc5697180f8d17be74f1be6` | `fce1db3bfd0846d5af6dcc96b362a52baec376bc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:407d766fc968df7d2e0aceaad3fcc2e6639d927e14b1a0a6adc6e2aee45eace0` |
| `R15-old-invalid-delete-recreate` | `f26bbc4c9cdbbf3ad4b2cd18c03b6ae60ef51fc4` | `4fa6ffd247960df785d1e957e4cd902382e8f437` | `b3e62e6398e4ee29f708d4eca4bd98a4b699b015` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:53b3fe4212a0040031adacc233a1ec48ed4beae54a47d312e604c5aae07addad` |
| `R15-old-valid-delete-recreate` | `d949c6358b9809dbc4c19c55ccc30fab511c7413` | `5f6066d0642c29fbb3414c54445b8ac08d5c99ff` | `de690fe09e6d88d499db4b3ebccdb7dbfb8b5617` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:519246e255e61966b14e6ee5779e0f33572ba5b786af01f0816ea7a451996763` |
| `R16-earlier-landed-evidence-reversal` | `e731036f833027f6e32ae9d17deec1f1b3114412` | `f8186fb2af1ae0e23196a4ac0095582433643daa` | `aee42abb66d8ba55343efe6f741c32987563844e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:69684436b0cce8d1288887bff8f711008090b8eee1e22b8991fc32210c88a920` |
| `R16-pickup-evolution-0-backlog` | `41945ab0488983f425986ec3f815e50e974be318` | `ddee8c3c0a47baed150ff41c81fe3dd3578991e0` | `50ddfeceda267269a756eff178f2e6f2dcde7af7` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:9ed092a07f76e0d7fdfa16390406614ce996579f4919b414236a89bb3876f084` |
| `R16-pickup-evolution-2-blocked` | `e7e14e5b5790e4682f7609b3ca494fc9fd1e9218` | `97de8555908750bc8bfe4f195811124e6639b33e` | `48a4d96e210ac69ff036bff2bd154d6e496e6a05` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:e46ef3a48dc6c1798bb637f485d10abfe5758228520564764fb0a3d5944c60fe` |
| `R16-pickup-evolution-3-in-review` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `66aae1f38225afbdde6a9af1c261223a7505c461` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:49771559dc10f5187192e9d7164d1ffee7fcf0fa05dec3dcac7de4beea7f0022` |
| `R16-pickup-evolution-3-in-review-drop-artifact` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `04e4cdf6f4c210ea0a27c59ed86f1d01627024c2` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:d06a28e462944a250987071f4f64b0d018a77b9454cdb06566907448d957e7cc` |
| `R16-pickup-evolution-4-done` | `28b720891ddfd4c7291ada824d3d2196cf4a560b` | `da9ebd1326c500e7d2c008fdb80f43be5cf13ff9` | `a8a309c333926cb8144f022c4356736917e5907f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:c93ba3c02cdccb066c2764a66e1cd2bda05d329f5228f3dbe7ab60ba89574902` |
| `R16-support-adoption-drift` | `a831384530c69ef834d1d997c25ffb996cfa4bbc` | `be001bade214359024c192e8b06d79229261a4c7` | `ce12604ff0140d20fdda463a6140634b62f35bed` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:71ce35d90cc0676da95087e714a303928a903dee45eaaea21768abd1afed1c75` |
| `R16-support-forward` | `8617eee2ba78f3977a9e7e0329159f725633daac` | `4690d1f06ca2513358bd47fc88e8dfdee3a15d71` | `9e15331efb2e68a1762d26fed1df245232a40f2d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:9958ba68d1c4997c491a288cfd3755169f9b798b6387429b709aa8658d9901d9` |
| `R16-support-invalid-source` | `b5e005e8c934907d6548515f752cba73b79797da` | `8cc15771a0e42ecaa2b04166fdd57589976cb454` | `2c6d7881177ab459839ec9bf195c035cb8faeddf` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:9db9f19449fd54b2a54f4f3601364aa57369b8f9247479e76d113d64b9bf3393` |
| `R16-support-nested-drop` | `168496fb2f34612a9276eab0151b2b83bf1edd88` | `13967af6be58e3cbea6ee31c6f54f6c39b246626` | `95622f34bd3618ecc561897fe977861d26c1a4c8` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:35eca8c6f0432f5a1af69e967d131752119f3db2d29b5af7d2408ca145f4d996` |
| `R16-support-permutation-diamond` | `f3d302490bc5c12be93f9392e00071fef0822ffa` | `b82141d042aba0552175891be684c7dd7eccc579` | `04baf28178f9b9b80761050e875ca2f993b4792a` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:f652c148756455cdb23152ee658b4edef29a846507420511ad866c62f9eb5efe` |
| `R16-support-reverse-drop` | `96de2cbd6d1afee44ffb6a03dcd12ea53ade9d70` | `fdd6aafdea7adfb0255ef9c1cf12168a23685d00` | `c24c0ed6dd25307717255c297879a96ee8c40f7c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:8158643427c4d9569e3fec5383f082505c59e6cf5097791ba9e0a4ec1f7aa626` |
| `R16-support-reverse-preserved` | `f3b2fb92a748ae2b38142cc01b1542b5302dcdfb` | `1f62604717746cdf35f2f13b4efe8789e9a73118` | `e38824daf72c0fbb9c049b6662fea36ad262f8cd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:0577aa724ec9e8659a99299818469a9810a29787b0a578c6492967c10329e8e0` |
| `R16-support-source-evolution` | `ffc5faa56114e44e8497228192ca4daacd278179` | `91474815e967e29084c0d18638907fe068dfd87e` | `2614fbbda55f0fd12af32872df6361a290c8b12b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:6c24e877ed2b8b9ba71e0bb6f421dadb2227978a61e90fd29c940f631e9f4cab` |
| `R17-carry-absent-arm` | `a3cbba79bd52df83262715df9652f338ed3b7f5f` | `a6a471c1129d9af27fd96ae12ec4bee2d2f326e5` | `a5e82a41d59db68164823c9fb5a58359bcf1ec49` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:7eb0fc3ad6b95216109a8ac5b81a83c409813f68160e2704ad7dc19ac07360d5` |
| `R17-carry-compatible` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `ba001beceb64bc88110a724ad6da2ee3498c8c90` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:3979f220132065f19d4ca4e51def3effbeaf38720bf5301b52cd58542a22cdf0` |
| `R17-carry-compatible-reversed` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `b4684c533ad9bfcb5918dfff653a30eda3e53d66` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:f8266316ab431a92efc16ca94dd6dd324fe6f49fbf4dc5b47b82bd01baac6a21` |
| `R17-carry-incompatible` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:4a6a4ab4fc96a2c356c038519dbc0ab31a49230443fb32e2abda0c5cc9b3edd3` |
| `R17-carry-outside-duplicate` | `f793332edc8b2cbee979959d560c177365267cb6` | `723fbd86c6180058e653f7b8241401c172a7dd1a` | `0449217881a784a7c4bb1ef1e6b8ed1a5fb781f5` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:55a372b5c0032299a8bd353a15841787e9c165d89f22da857204decc4c886e18` |
| `R17-carry-outside-single` | `446a8c37bb272b847634d4f51ed29d6bdf9db1a5` | `5f2c5d5e1489b14b10120ff854459b2e71944fd1` | `60e0f415b3d0d3c59e0a7980c4efbc9868e1d576` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:7a37ad67e77156661967bbbbd4b09b6faa558387c4ba7bfabc01f298849d7dc5` |
| `R17-dynamic-support-traversal-exact` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:b6f3cbc14b0410c77db60603839756b95ad05f11c59f383e8a0cedb2cd798985` |
| `R17-dynamic-support-traversal-plus-one-refused` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:6d57ec54e3651b7e676393dd6af9547cecaad2f4904e7bb68924e93b6514b066` |
| `R17-flat-tree-peak-exact` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:f11e0e07630db872221c619cba87cbf5456af05b6c901851f41c43c0db88c39f` |
| `R17-flat-tree-peak-plus-one-refused` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:584b7d58c18016a12b034b1883a892fd5d58a6365d74ee9fa812750a733fc727` |
| `R17-graph-line-peak-bytes-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:85357c016290988a4d84d451787590cadf2dc5f21c611c220d87e51ac5853f0b` |
| `R17-graph-line-peak-bytes-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:6274b6939828e43f6c975238f1cca9134acde9bf044e8f95df23902b4421ea9d` |
| `R17-graph-output-bytes-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:57a74fefbb97f36f56848736f1a01b600126f1d67e27f94427547f0d3ada5123` |
| `R17-graph-output-bytes-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:cfefd016e4e367994cca7d825d4628ac6b27b224f71bc56fd3c484dd2996e1bd` |
| `R17-graph-parent-tokens-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:7fbbbd2a4b6bdb6e8c7ed2e6ddf87fefdd50a92389a52f901add3f3d1321733a` |
| `R17-graph-parent-tokens-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:8d5843df0cc05a423b02d79fb49a303dbeb8d631907918d4f74990f496cac9c5` |
| `R17-object-payload-peak-exact` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:eb2010e5a8027dc931242b1eec83e28916a52045be7c78323472ac144e8b18ad` |
| `R17-object-payload-peak-plus-one-refused` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:ca14b2cc2c8a804e85ee1af1b4089a42980126b5de3a8e59b65ecf18902bc6d8` |
| `R17-outside-C-neutral-parent-valid-restack` | `d3d362d37559714b75cea48eef7f44a4547f4e2f` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:a28ef43b85d7234baa2668a69eb022b42f0de6675eba8b4058fb2047ffb214e4` |
| `R17-persisted-outside-duplicate` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `481c03e8e4afa0b3dfe37df8a244bc53823811f4` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:50ec15ea0745c92294785738daa7e22cd0adbacd9759e6abaa451038b38b222b` |
| `R17-persisted-outside-duplicate-reversed` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `d74cfd74fc6648eb13bb52ad192ee13b4146155e` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:ef3941290e95873c5764afaba2e461cb2aa09039f9dd99e888f750b5ba6003f5` |
| `R17-persisted-outside-single` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `32a88f55e904d1892fd473b62f3d30a4bf2faf24` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:31b523cb81b4bbc75859604e53e63cb11d650c5075e74685557a3bb57442cc9c` |
| `R17-persisted-outside-single-reversed` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `4a231bb4516e6185d7ade17f5e5cb8aaafcc0613` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:d6bfd9126beb9008cfee9dc3ab887b6a002e96498e634d9aa02375dac0846064` |
| `R17-persisted-unauthorized-absent-arm` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `c1e4c835d0ece38b56490f0beffef88494aef8a2` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:eadec7f6b8bd9dae395c4dcf75b8ba4b3b74621565ceaf6d0ff2ccfa82537334` |
| `R17-persisted-unauthorized-absent-arm-reversed` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `6a55c69bf40bfcd9abe33bababdae51ad111eeca` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:c95efcc3b8d146e02ca8449ff73a546ed6858e067c9490878c9849b2a5b7a2e6` |
| `R17-persisted-valid-absent-arm` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `501cc5ef6cb38be7a83d37b9f47d26cf2acebdec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:a595a29678879395ec650471164456dc601a38b1a72d5257832418f963f1a2d8` |
| `R17-persisted-valid-absent-arm-reversed` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `12f08cf66b77738190f29720044039af1fcc10ec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:c5e16866828cde55da9707ee8f9342d5c71737bc970bc3a624e096a86ff9b3b4` |
| `R17-precharge-P22-budget` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:43a59c9a572fee962162fe043d259a149540ccd98fdf27015334a439a087a8be` |
| `R17-support-serialized-exact` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:17da5b1d6b6ff06d16df0c4e9da6bf234576901e9ec33689d143b295e8997700` |
| `R17-support-serialized-plus-one-refused` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:769f30fe331c10d74ef7ef15648029a6b9a08e75eb966a7fb4920031ca0a1407` |
| `R17-unreadable-outside-C-ancestor-stays-unopened` | `33f9ad5aab42435cc63bf59f2b38294666dce16f` | `9490a5097490e4a7e38d8b76dded28f7d370d22d` | `508323236873cfbdf04254316378e7748f4a3959` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:d39bcf90df4b04d1c4e7699a0506f487482645fa1d3b44243143d535d671a15c` |
| `R17-unreadable-outside-C-boundary` | `None` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:cfdb364e0804ea5f3161d4065427df70e0a099931bbebdfc34ae6cf16119c2fc` |
| `R17-wide-outside-C-boundary-budget` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:5f8ae5a64816ad8a11920abbed3d4bc84daaccc45a364ebbf49b70f8e6327a91` |
| `R18-B-agent-born-claimed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `2a4d3f1d3eef9a03bc7d3c986cd2da5c467b54c5` | 1 | `blocking-finding` | `invalid` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:abc06363c6f69e4872b79b1dcfa29896669d765ad54d7e20017d7295175ebaf4` |
| `R18-B-exact-cherry-pick` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `63ad62d48e793b82a4aaa69974978986d3b6043a` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:0bf74e6c2d59519e7166a5e1614c4f9b62d87c2722f153de754d9046dec04c19` |
| `R18-B-generated-retry` | `a46069e80fb5d5227d71a18b050a8c337bbabd1f` | `0d60dcde791edf705070d94e0f800ef2e6f35ed5` | `d7144cf5a0fb0e3f09c9f573f8257c3290b41dac` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/2/0 | `PASS` | `sha256:0d48fb1fb6e880bbdd54ead0971f83e7d770876c92fdbd13e19eb5bc881f7543` |
| `R18-B-human-born-answered` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `3d3002819c80f751134bf18dd69c9e6fbc4e9b81` | `6e12a9c537ae86bbbfa26c8158bf99e56e940b50` | 1 | `blocking-finding` | `invalid` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:7c00d1212b8aeef15754ff5f065ab3f51354d4f08a662f6902c94939ad0e8381` |
| `R18-B-independent-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `393caed61f0ad9e0d1069b23eca5a5b542e444aa` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:76739e557b22a9d2b017483630966ba5eaa709b43f399583ba64ce612b62bce0` |
| `R18-B-normal-base-advance-replay` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:018aaabc911e43a8e316071c18911b8084e9a446fd9d2e3fc6b1352c5bef4bc5` |
| `R18-B-rename-timing-move` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `bb07ead37b4e0c90fa4de7221270536530fbca1e` | `fc2963a36886ae8d832f3f47f7c45477919cec8c` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/2/0 | `PASS` | `sha256:4506ab66aa46a21525bb28ebc396b00e50b7431d3108aa9544bc1c054f6b0809` |
| `R18-B-review-publication-equivalence` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `d4580983aff8ff5052a9fad2699ad964ecf903e5` | `a588f41c0d4b66d12c691dbdce121c111bf60f3f` | 1 | `blocking-finding` | `ambiguous` | `origin-B` | 0/0/1/0 | `PASS` | `sha256:0e28a1085e73edfa892341b52ecfcbc57b32853d76853c65eefbf9904a12f0e8` |
| `R18-B-task-pickup` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `65334cd7e556f35c62a0e1dcc097a51fb56c2f7a` | `8871448cee01cd76d0e182cd0e70e5083eb37bb2` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:dc8a2bf56cc98bf91dde3bfa4aa89331d30a91bde75289ae3eb50e2fcc472428` |
| `R18-U-O-only-post-C-loss` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `9c12ccfb1f02f0d3d7571d00ffdb12c66d82130b` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:ad960dad8a63d6b9b4c3e2088b1864f514274e31018aa593a8ceee327a3e2c2e` |
| `R18-U-agent-born-claimed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `2a4d3f1d3eef9a03bc7d3c986cd2da5c467b54c5` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:cf0cf4c4073a88d67d0a544a4e66faf498170689db3760d48b77edb0f8e9d5cf` |
| `R18-U-claim-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `90e1f0632af49864eb90bb43dfd9d653226f7e29` | `0170b8f74746a2842e91e3d24db2b40794892a6d` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/3/0 | `PASS` | `sha256:c05f444a8e0e05420945576102ce76757667b95917e4d11ab160fbc305635bd4` |
| `R18-U-delete-recreate-N` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `abac59c0275ad436a733c341b84b8792991be1ef` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:7f95b922408af408460e53a55d1fee8adef3b6b65206e05915d8c755a83d5585` |
| `R18-U-delete-recreate-O` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `32e5e784fb97324e37f759d14a5dac600588b780` | `6a39f8fd46eccd075abe13037b8ab08311fbbdd5` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:bee0ad088f852a93db6f121c3de73fed83acb250893d0952f8e53f37414eb825` |
| `R18-U-endpoint-regression` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `fe39fc5d19b39d80c00132f6bb67671afd026024` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:08981cfbd4d0624aab56fbe850bbca9495e0ebcfd7947b2365531ba07493858b` |
| `R18-U-exact-cherry-pick` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `63ad62d48e793b82a4aaa69974978986d3b6043a` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:167be21048a7646be8c3ee563ab864ddca61e0149adc32d9ac7f00fe2e04b6ad` |
| `R18-U-generated-retry` | `a46069e80fb5d5227d71a18b050a8c337bbabd1f` | `0d60dcde791edf705070d94e0f800ef2e6f35ed5` | `d7144cf5a0fb0e3f09c9f573f8257c3290b41dac` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/2/0 | `PASS` | `sha256:a46bacd95135be5e462f435e3665143a18f62aa29b5bcd6e57d6da2de6883d16` |
| `R18-U-human-born-answered` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `3d3002819c80f751134bf18dd69c9e6fbc4e9b81` | `6e12a9c537ae86bbbfa26c8158bf99e56e940b50` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:6a378f6baa32a46873b5c7ede9c10b39d93bd4dac9b2b41246fd3c3746986544` |
| `R18-U-human-response-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `2574705b088135eb07beb5b710a919626a134e9f` | `8570f09b40724dcdbe220428a2808fd418d9955b` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/3/0 | `PASS` | `sha256:3ae9b2bc8fae8c3dc1578c86b6f8d11ec7487a200a31b2e1fb937dc68b036007` |
| `R18-U-independent-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `393caed61f0ad9e0d1069b23eca5a5b542e444aa` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:c39ed000c3e841ba2608df5a339bc22d2291f8b4782a42b2e3a1065e17f97fa1` |
| `R18-U-inherited-then-deleted-merge-arm` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `073d6e1d080608961f59d7a9168d96b24fd2e3a5` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:7543bdc9720d453cf39ed185741d06c9ccf0027122b022f129b5ba67cd5898d8` |
| `R18-U-multiplicity` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `9d0e0b8d05a8ea5f0da83647bec14f62b5edfb67` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:6b1ff07ff8172a084ccd07e52eacfcddf5366b7568c1ec42aaec4ba55d321548` |
| `R18-U-neutral-pre-origin-merge` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `57533e22234a2f70d70777040816fd6c436ee9a6` | `b50449c74ca178d7aa31ffe996afadb3563c8ef4` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:4d18431e266f97635a535bede8a68d29ad8f60b6ff17d2c286a2a47fb1b3a01c` |
| `R18-U-normal-base-advance-replay` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:17122d2d1ec0f1babe52c2a584444c5f3c23238b3d9a160d905e7a8934e7621d` |
| `R18-U-outside-collision` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `71cedcd8dde74240d0cdd5a0d0e0e43e4819e80e` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:a552cdde673af760d028552c66f0c55cd2332aa929512a2be227de4647ae913e` |
| `R18-U-parent-order` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `68f00ece3d08a437207e31fea0decedc88ca3a22` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:decd83f082c64ca498b45ace51f8a5b631ad20e1aa559b116f12c0b857b96fec` |
| `R18-U-parent-order-reversed` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `f96e171c8daff5cdc0ec7af626eb222af3c4f2bb` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/4/0 | `PASS` | `sha256:1342e01b2e2da18ca8181bc10477f10d69aa30170fb7e8e6b214f8c6ab6e116c` |
| `R18-U-rename-timing-move` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `bb07ead37b4e0c90fa4de7221270536530fbca1e` | `fc2963a36886ae8d832f3f47f7c45477919cec8c` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/2/0 | `PASS` | `sha256:6d990ae1346eff9953df5d183de2496ea4f959fb62ef03de4069df40acee311a` |
| `R18-U-review-binding-restoration` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `b4203751e312d0423e9b046c2363e2f638ecdeb2` | `9ee8ac72a1862689c5199828a56b8a83a26a8a26` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/5/0 | `PASS` | `sha256:299439fd35b213946702136e73e6f94dc692f70ab6115ccc6bf6396d5e1d9ee5` |
| `R18-U-review-publication-equivalence` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `d4580983aff8ff5052a9fad2699ad964ecf903e5` | `a588f41c0d4b66d12c691dbdce121c111bf60f3f` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:c83f4bca2b98a0f6e39b470393c1113d33de3bdaaa124fe4c0f327403c2df4a8` |
| `R18-U-schema-invalid-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `ae5b882d624ac753ab179bca502e1d470f7cdf23` | `87ffc4416aee8aee8c2adca7eff692b471c5de4a` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:4d97cb794bde7ac9843e304ce596380f5910ca1562067238e968837114ddda05` |
| `R18-U-second-birth` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `baa0995a63d5d5f4fa418cdf7f79b274c9e90272` | 1 | `blocking-finding` | `ambiguous` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:5ffa44089e6e470f23b3581b65abf946367af1273a2e10951dbf5be7748a9acb` |
| `R18-U-task-pickup` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `65334cd7e556f35c62a0e1dcc097a51fb56c2f7a` | `8871448cee01cd76d0e182cd0e70e5083eb37bb2` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:92f022859ad54d2773c96500bc8e25943a59a77007894ef6a1345891b497f85f` |
| `R18-U-transient-protected-mutation` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4a58c18ccdc13f072d74f6b134ad76b98f28463c` | `6a39f8fd46eccd075abe13037b8ab08311fbbdd5` | 1 | `blocking-finding` | `invalid` | `origin-U` | 0/0/1/0 | `PASS` | `sha256:69435ec1f3c49840a0fdfdac5130274ba8d4a35c9c9b9b85f7d41a06dcbd1ef6` |
| `R18-U-unreadable-object` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `a04f20486b2958f99aa41dcf8590989d70bdbc9d` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:0be4c5c764a3848ac26159e33e7b32568da108fa405fdbd1d2e2e86a6892f985` |
| `R18-origin-arm-nodes-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:fe9a0fcc4ef20b65a1b57b9b59f8ebcbfca9ae047b681b7e2bb42d4ea02a3e1d` |
| `R18-origin-arm-nodes-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:1d30e6699392911aa8d493a335cd6e51584f80696577b08b4340421a45426c64` |
| `R18-origin-parent-edges-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-U` | 0/0/0/0 | `PASS` | `sha256:e777b216cc43bedeba58d7856a97338795d5fbec0688ac04a1076a45e8883c14` |
| `R18-origin-parent-edges-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:2e82a9df47cf368331c6ebd54779b4eefdf3891044f7eec4ce02d56956fad7fc` |
| `R18-origin-witness-bytes-exact` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 0 | `no-finding` | `valid` | `origin-B` | 0/0/0/0 | `PASS` | `sha256:afa9e9541e2d32ecbd8dbd60fcbfdc787cae5c1ec5659578ccfac29fded8eaab` |
| `R18-origin-witness-bytes-plus-one-refused` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `341b3be192bb915c355248757106f10e89c80590` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:ea73ead06967163c2b57170274a47190398d007fdccd2baa6a011e48f56d5f87` |
| `R3-01-two-invalid-causal-sources` | `73373ac5106e43d8643b5b616268d77a5ca1d264` | `8f89d0fc4c063c0bbabb284434f74bcf244fb5d3` | `8ed846d60715d845a5e19ab6b299ce853a592614` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:4f54f3eeb18781bbae5f53d0a9dfcfbd3a46014b9fd595ad9e868bf6edc54503` |
| `R3-02-invalid-valid-causal-competition` | `16722b83a642e40f2157c752a07adffddfaa709d` | `35e767d91f32b96f8f8308b431b5c6a0b35be23f` | `ff42531aadc6ffa000560bc56d995993ffa8e62c` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/2/1/1 | `PASS` | `sha256:7b1ea1846f4651f9050398316dccaaf13bf4f138ef2a286f14fd8e4a9287430b` |
| `R3-03-valid-supplier-plus-invalid-parent-at-N-blocks` | `1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd` | `ba83bd926d133cee0384ae4b8fd577de5d14e835` | `433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:7edc60b01a3f1453c0a0c078e0e51c461b42b141200903ee246d4ef4ccf0d14e` |
| `R4-01-same-root-valid-diamond` | `4e831314d34c2897a072cca5b58303d8fd0e7ddd` | `2ae7f29324bd8d6b29c1f7640602fe7ec9193b1e` | `a7bbf4b40d0a3322205e3d8407eee73b9b11ccc9` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:7bc74d585e76d10f198924e4b69de439e3221d0714b02f09f14d07ff9778bc12` |
| `R4-02-distinct-valid-root-diamond` | `10965dc1169826888c7d66e2389f9f90787c0064` | `286e35141edc20fad35f8b0d4aeb4930c403d038` | `37a75ca4c96e8966c19fa18afe6b6f9b1e4c10d7` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:1984956500ce2e8fa918ec316b5270681514c5dc56dd159c6d9af3b2582ad10a` |
| `R4-03-equal-root-plus-invalid-diamond` | `90e37b9adc7b3b428f2963282519639354bd2b56` | `de44aaea6c73d11ca46c2255f39f9b9a3d10d36e` | `3c9778ae10bc7a945bb59ad802db12bd6803ea64` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/1 | `PASS` | `sha256:d09ee99aeb66e0ac9d509bc06dee5fdd8e456f259a5c61192be84cc77f473be9` |
| `R5-01-invalid-redelete-after-supplier-reintroduction` | `1e5dad973b3278ca8c12f3dd74f72250eaaf9f09` | `c63664276a141f3f60f61c9d404de201e6f8cf16` | `d40a531fd9a0dacb986f9259ac6f94ec0d248faa` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:a24758131b4bc323e56d86ec6cdf59bdb43bdad78c4b772d5d374663a866dbc2` |
| `R5-02-valid-redelete-after-supplier-reintroduction` | `79b338b3ef54382a0ec95e87a7ba962b1ec7c20a` | `9c8b1418effb6889d14466e278a7987b7e7cfbc3` | `fb0bff9778f436aed2a46f887eafb84e1c74ea5f` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:7721dcdbd9faf378a7b71cdb24b094dd7fdb8cd20f7fae18807960171328a464` |
| `R6-01-valid-plus-invalid-all-absent` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` | `5dc5378fdc316aa30dce282d0388a438d755b067` | `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:32ad1ff62d360df9a7d3469f323fee886ea7417d4926ca8ec30dce6da7df43b9` |
| `R6-02-valid-plus-ambiguous-all-absent` | `f61617485ff0160e37de559fe752c56ff3bcb5f7` | `10a37a2bc559519d6d84f70850b0a78445c3d5ec` | `4ab46009954bb98c5f22629274722667dc21ca37` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:76f7c24206d7be22dc1dd01c8c455fd7ed1d8193ede2255d832125d5a8189501` |
| `R6-03-two-invalid-all-absent` | `f5141f92b29541282cf1ec520470e8c604aeaa6b` | `eb354df4fb54776834a9dff53f51f496a2bb338f` | `8f769727f1c641bd2587115f2fbcda5fdda816d1` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:ffda826db24361988058145413d23ee8ae1e524b6ba3a6784b152d4ea972600a` |
| `R6-04-same-valid-root-all-absent-wrappers` | `c4ad2cb41bff8803f0f3d5b81ea0cfd785c9aa59` | `c3b9fb54026383a350146fb2f25243c9e8c7cb01` | `7bf74330f432155c3c39eedbfc81fa72bface489` | 0 | `no-finding` | `valid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:46d09e926b300acdc5c05271485e017203a0911388d6b2800288ad2365d3e40b` |
| `R8-direct-human-response-conflict` | `92c80d9c65c7be349d0a6c663a6a2ea9c3c2397c` | `1dc4f0dc77aae1eefaef0bb443ec187ff1efb23d` | `cb29049ff107a9a11a4ec7babbdee21819518dd6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:5d7f408803f801465f96cc70fd527f12b4eba88b9f3ed108ec16bb2af7dc1dd6` |
| `R8-direct-human-response-identical` | `2b79814b0bce6f1556c0b2724ade9d7bbb4bf939` | `b3879039d6d7168e89b3046e6e60e056460907c1` | `2c2289035cfc91c73564f6a97b326ebca02be132` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:46e9dd3057bb8bde8468f0de4a64c20cca8dfc83966c0a88ca9425de12bfd99d` |
| `R8-review-binding-divergent` | `9b4889771f49a83cd02600a2de58fc5e6e8b8259` | `e3c594800cfe94f4f23c58060ae4ab31f50c078c` | `dc70864ec5e13a399d4966356b9803075681a0e6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:768464e3481e5b789932d3ae10fad5b66b9ce8dfbf8bbbf26a7ca577eb8327ce` |
| `R8-review-binding-identical` | `45b7550dbdc799efed73af109da57c6906d428a0` | `a3f97a3b22945e663eb10180bde5de3b7bf790fa` | `b2dbe65f89982fb586b0fb5349454d80c7c53310` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:15c5c365621998c16407b15dfda77093957273971ade88335cb695f2a6523a15` |
| `R8-review-binding-terminal-conflict` | `cd64224f775f16bc2099816c594012a9592f8536` | `356f3f37cdffaf8f6c568a158a32c478f55a0e13` | `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:e61b869e8253bff163feb686f5b4ad472fc7110889e488334fe8acb05e86edc8` |
| `R8-supplier-human-response-conflict` | `255e448f3c735fefdcee3c07071c3d6bb6abb312` | `27927fe11bdeee043660e700c81e8cb3853c56bf` | `1fb9fc40da2d44e839830611cc20d0aee23c560e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/0 | `PASS` | `sha256:2533761393ae1d41975122fd201af93a2eb2857c30fcd976ca4fd7bdfaa2f013` |
| `R8-supplier-human-response-identical` | `800658fac71a8c7fbc2d257bde57964cc96dcef9` | `f33b095abbf3c3e3225e0fbfc663b0a7f52d312b` | `e94946d2990fe3c67bc61676f66f90fab1b7a26a` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:35155e30e7b618ff50ed0993da74403158463a409e569db68d695c23cb8b0ef0` |
| `R9-direct-review-revision-pending-fill` | `00ce8c4f203a14c87a9955fece2645744ab2222a` | `6da769be2398ce26c45d3dba7845e0d6bcdc07fc` | `f5e8ec93ded434c47e27f345c1e38da95297f7be` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:f50f2bd342a30d1354d083c345fda86f026f203db546f6ee9d38b9ddff386e24` |
| `R9-direct-review-target-pending-fill` | `7a613196cb22eb565e0f85194f7e2b8251a1484e` | `4263506464cbffb20b5f550fa142ebd391669ca1` | `8f2d8945b9ee6ffc11a714efefad9f8c1d708410` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:63c7cfcbcf3d7bfe1a4110522fb630ee06f400e5f93e6939ad18db7ed73c0f43` |
| `R9-supplier-review-revision-pending-fill` | `eef4459d2337688dab6f6681415a6f5c57cca6b8` | `9bec712c0e2453a881aa8fd36ff89d8887e07942` | `26d16dfc1e390a11c674ccbcf8281d212a19544b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:e964fb7203faa59b2f71f2d63221a93ad94d70bfd85c218eb73c9efe42499ae7` |
| `R9-supplier-review-target-pending-fill` | `8cc94bd588fa82e6bf7fa0258a7f4a3b96453d75` | `648b5b5515d697600fab0a9aa087a1f63bddad3d` | `64affcee2fe535a4f21aa80e72df2131349dda62` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:4f1bc68aa8264d2d7f0ebc0f037f40c1c72fc5b17b45f34c9eb02d4ff18a16b3` |
| `W0-fast-forward-return` | `b614e3dd70da804a078bde5088d38ac9de511846` | `b614e3dd70da804a078bde5088d38ac9de511846` | `2fce4585d497e94f48f6807dd3cd9fd7b432b264` | 0 | `no-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:1cbf3c56124a79aa4fdd3b454b2453931722134f8fedf4dd07f735d3693dbe49` |
| `W1-pre-PR-push-exact-endpoints` | `2fb10d8c39b965cafdeb5e496e351ab258f75960` | `365339838cdfc9d6579ac21478fec9b776742c27` | `1cc139111382dea68cae0208e17354f6f75c5bad` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:eb0f3e3695f06b1540fc31d8ba556230620c5f12a1a70e467bf3e5a8a49adf7b` |
| `W2-base-advance-retarget-invariant` | `1e1e59bc5493dd584372acb3da94233d867bbed0` | `a6363187edd2b2ae4cac6d24e0bc6d4d9adfb836` | `1c48ddcef1c77fdc65609d2a077ef3cb40396393` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:b4a02d0836de373f8085d58b2ff6b170ba384c43f283285ae51099a5c3f8b915` |
| `W3-multiple-PR-API-zero-calls` | `7f7a2d473d3bb95a7879b5ff2c26195a4b730e1e` | `b32b24f6a4b08d17c073bfdc2355521efbcbcf58` | `56238e170cdc0358979e2cbefc7af6cbf89b279b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:559ad1f88aa7edcd0403161a88ae2a8cfed93d331d7039f59c0e4621a57b9266` |
| `W4-stale-rerun-exact-inputs` | `b5c4bd355d0c9fb9279be13d67268628652addc1` | `842d19ca481aa76dfcdcf096af4c550e826d9569` | `6046485394ff351e5cbecdd5c5503c44a821af8c` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:3e8fc544d622706a4310546a9830fe845c2d755e0452a833fb50f07881b7c57d` |
| `W5-missing-O-coverage-unavailable` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `4923d6cd62a6ccd426bd569cc06323a11f775bc4` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:69da0f9d760e536dc6a3a3f0af7cbc6ba6141ee947febb4fde9457572e444769` |
| `W6-created-deleted-zero-endpoints` | `fb590466fe387afa4f25743982c78e281f34f36e` | `2df4b3d62821abe8ea3f482b931ed91d256d24a9` | `1f3aa42d8428e4dd3b8b98220355e0bf883c318d` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:6fbc1fd2b01de6a35386a616c6c7a0eb9edeb728962e01406a26d9bbd80c39b8` |
| `W7-PR-synchronize-top-level-endpoints` | `99342d9672d3f50559eccba1fc16eb8710b7b476` | `55bd0ff6ffe71dcae7a1afbfa440b021bf972dec` | `5a612247b54e551764fbf258e44893a0f5c40dde` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:eb7c5c9682177289646ac6620ccce34f7be06ef0597bbef6757540e6e28c6c60` |

A/P/U/S means authority, propagation, persisted mutation, and supplier-support checks.

## Executable S aliases

| Alias | Maps to | Classification | Evidence | Mode | Authority | Invalid authority | Propagation | Status | Record SHA-256 |
|---|---|---|---|---|---:|---:|---:|---|---|
| `S1` | `P1-direct-linear-valid` | `no-finding` | `valid` | `direct` | 1 | 0 | 0 | `PASS` | `sha256:fef7c69b2733ef9300eb8a94c5402f06644504c1630441cd8bc5f6ae421c57e0` |
| `S12` | `P12-merge-supplier-valid` | `no-finding` | `valid` | `supplier` | 1 | 0 | 1 | `PASS` | `sha256:adb7c8e1467d16f5adb49e5287cc1393850094f70ea67894484b9ad98e6ac8f9` |
| `S2` | `P2-direct-linear-invalid` | `blocking-finding` | `invalid` | `direct` | 1 | 1 | 0 | `PASS` | `sha256:88ba94fa4ccea046af31fca874581f9a7cffa7f52de5f67e6a8d799ef6e05268` |
| `S3` | `P3-genuine-old-loss` | `blocking-finding` | `none` | `none` | 0 | 0 | 0 | `PASS` | `sha256:55e72e86cc683168757a7da62a39580e628f3a5af4662244e3715d24e458c397` |

## Damaged-mode controls

| Control | C | O | N | Baseline | Damaged | Status | Record SHA-256 |
|---|---|---|---|---|---|---|---|
| `broad-review-pending-normalization` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` | `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` | `ba4edb8f323adba9645e47c2536f2b621bed7855` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:292e6c32afeb9ca638d3bad9cd4a9596302eee6456662ce51f51bf84a31df86d` |
| `buffered-graph-output` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | `blocking-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:4076adca6645e7afdbbc0cd09df9cfdf73c8396d8a6f9475346170a5608ad5d0` |
| `endpoint-only-origin-equality` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4a58c18ccdc13f072d74f6b134ad76b98f28463c` | `6a39f8fd46eccd075abe13037b8ab08311fbbdd5` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:c4e33f3dab8b3dc1ad85cf9cb33ceea7717c5017d1ca85ce2cedb4aa6f3caa4e` |
| `first-parent-carry-proof` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:8c6b273cd04dcb4b4d17e60a3c3913f929ff3342d72b92ccfacd964f07d8f74e` |
| `identity-multiplicity-collapsed-to-set` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` | `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` | `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:7e6e7b7646ca1bcd1821ef3fd920528858c6a8e435eb04b5ff975ff4ebd20ccc` |
| `ignore-absent-C-arm` | `a3cbba79bd52df83262715df9652f338ed3b7f5f` | `a6a471c1129d9af27fd96ae12ec4bee2d2f326e5` | `a5e82a41d59db68164823c9fb5a58359bcf1ec49` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:f9a91f587c7790cdfdcd77cd3f389ea8fe9a54a4a27ce0f51af4d4809e75e3a4` |
| `ignore-invalid-N-root` | `1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd` | `ba83bd926d133cee0384ae4b8fd577de5d14e835` | `433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:017dfcee6a829874ad3c86a4868e42d8d4108579c771a8d838ab1f5c2e9c0fb9` |
| `ignore-outside-C-carrier` | `446a8c37bb272b847634d4f51ed29d6bdf9db1a5` | `5f2c5d5e1489b14b10120ff854459b2e71944fd1` | `60e0f415b3d0d3c59e0a7980c4efbc9868e1d576` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:3b56c222946112d1313e27f2259fa322b9f6715328bcbc5a67038eccb63181a8` |
| `ignore-persisted-absent-C-arm` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `501cc5ef6cb38be7a83d37b9f47d26cf2acebdec` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:b5a60b9898d9fabd6d22870af82214ea6692dc94c68f297735bc18d994a3e4ff` |
| `ignore-persisted-outside-C-collision` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `32a88f55e904d1892fd473b62f3d30a4bf2faf24` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:db79757d9c07fd27faa50b16aad799d190bc584e23a910badd7c2aed36f19100` |
| `literal-review-pending-treated-concrete` | `7a613196cb22eb565e0f85194f7e2b8251a1484e` | `4263506464cbffb20b5f550fa142ebd391669ca1` | `8f2d8945b9ee6ffc11a714efefad9f8c1d708410` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:13d112385cf15c651e998e536dc1094018aa7eed5bcb3a8e7462bcbbbda7a5eb` |
| `locale-git-error-stream-equality` | `None` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | `unreadable` | `unreadable` | `OBSERVED_RED` | `sha256:5c034618ea0b830c69aa5591031431f90a390b243a064353150941fb215c4cf9` |
| `missing-all-parent-direct-validation` | `d7dc739a275601572c26fadc522a2ae4b71d3b12` | `ff1d9fce8cf6d941f7e0210a9cc6b3380df94741` | `bd005f27951b3bae6225e8cc736936db93667388` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:a71ef07baa481ad097d61471eb45665ceb58881ef0384a019692ee0ce15b4493` |
| `missing-post-event-continuity` | `ec84d0800c660f6379b21cfd721122fa06162999` | `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` | `258e858010ccd1e43716ab0269faa86ae08808a7` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:84f5b3d73899c5a20ffd97d5252f388df00d154afd64a4aa9c5f049befdb76a1` |
| `omit-old-tip-human-binding` | `cd64224f775f16bc2099816c594012a9592f8536` | `356f3f37cdffaf8f6c568a158a32c478f55a0e13` | `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:ef4a25a4aabc01d7d532866e6426b0e835bb764ddba91dee3bb799907a9d4ecf` |
| `omit-supplier-carrier-human-binding` | `874d2e356033d133cd409bc9deb8e93198d0ec78` | `adf1ce7876b84e595992f5865f871b59ea892234` | `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:7ddbab84dee6c41351e232629529ef9126fe57025c9ef664213926ed748ccdd4` |
| `omit-unanswered-published-review-binding` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` | `8a2de576d9304a51988bfbd943749129f828f882` | `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:58344243b4503b74ca823588324cfb10c725a5cc25ad5dca23f7469369210de8` |
| `posthoc-budget-accounting` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | `blocking-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:d311db4328f3409144db755f0c473931b3c996a0744477b2c0e5076c84104680` |
| `reopen-outside-C-boundary-ancestry` | `33f9ad5aab42435cc63bf59f2b38294666dce16f` | `9490a5097490e4a7e38d8b76dded28f7d370d22d` | `508323236873cfbdf04254316378e7748f4a3959` | `no-finding` | `unreadable` | `OBSERVED_RED` | `sha256:157181b097f4d2be8cab789883086861525fd654134a838a42f564e262280b66` |
| `reopen-pre-C-genealogy` | `cd13c47983b0624a824f5fc583f7de647b240504` | `03c76bf6661f670a705245479f406a1d3ba7b279` | `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:a009eb9b4b50291d7cd9be8722192ad2e66090801ed093a14cf27e9469b3bb8a` |
| `restore-universal-ancestor-carry-scan` | `d3d362d37559714b75cea48eef7f44a4547f4e2f` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:af433f685f3710f1c9a8c5488bf5581df374b7c6aad0a536cf9c5ea5a500d04b` |
| `skip-carry-compatibility` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:227154600e109348a3d6c0b1514e54872effddc9be1f7ba0ebc66880909d3abb` |
| `skip-old-side-continuity` | `f26bbc4c9cdbbf3ad4b2cd18c03b6ae60ef51fc4` | `4fa6ffd247960df785d1e957e4cd902382e8f437` | `b3e62e6398e4ee29f708d4eca4bd98a4b699b015` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:3a19d4f3b7d4ca1f109fd58c85b6365eb5dbf9e21bce3aa3e1a72dad161fa73b` |
| `skip-origin-birth-uniqueness` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `baa0995a63d5d5f4fa418cdf7f79b274c9e90272` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:46780c4c26bec93c6a347d55679fcb32a5ae31d34428a7c9ad83237a52550e4e` |
| `skip-origin-endpoint-non-regression` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `1e019c53656fff2ab922fcce592bbd4421bac23a` | `fe39fc5d19b39d80c00132f6bb67671afd026024` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:f6e7a02312c7093efc66413539e01068febd09b540962072208eed4f52c6efae` |
| `skip-origin-post-birth-absence` | `470a8cb8473e6cd5336a87220feaacb3e2ec53e0` | `4ef94866fcea06a279b7cec42b9e1b90f49a7f12` | `073d6e1d080608961f59d7a9168d96b24fd2e3a5` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:954f795b2f02f50085ce51ab93ac853cdc41dc4b1f1e5d419febc64a33ebfc54` |
| `skip-persisted-candidate-continuity` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` | `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` | `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:be25c6d46778bb2ae7c7c41984f17f94a41335ee62bb08a48d93186be9bb87c4` |
| `skip-persisted-frozen-skeleton` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` | `d115e7063e3ffad24a495c9ffae5d70ffaf81928` | `a47b7307d654cb07612ccd7b04f1c32ab874c475` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:8c4193947ee5457b221c3f7e0e7d097120e8494f9b663f5ac88cc3954bce035d` |
| `skip-preserved-state-validation` | `5604e77ef241630dd284448a224de046d2caf460` | `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` | `8702850ba2e7f56c29b16557c496adcaa627829b` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:24c70098bf6f1ac8767098bddbd3a29314b6564ca96b3a8e10349b51bbdc5bf6` |
| `skip-supplier-support-certificate` | `96de2cbd6d1afee44ffb6a03dcd12ea53ade9d70` | `fdd6aafdea7adfb0255ef9c1cf12168a23685d00` | `c24c0ed6dd25307717255c297879a96ee8c40f7c` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:d1b258a1c702f816d164f26803f921934c2eb2c94f103ac281f1e9a16401c1f3` |
| `sole-valid-ignores-invalid-root` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` | `5dc5378fdc316aa30dce282d0388a438d755b067` | `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:abe626b443dd6abfc3904501eb9a699340e2377c88e2e62540220fce7a8e0260` |
| `stream-malformed-truncated-final-line` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `unreadable` | `partial-graph` | `OBSERVED_RED` | `sha256:7f15bfc0408ce7d02754a9c860f5db3523d0c686f1f59e52160243feca438a57` |
| `supplier-authority-borrowing` | `8d565f19c072aa8f0cef381b3f0e8fc58029820f` | `41865c9def0f066b1d121b9882872ecf33bfe729` | `8579708e09425d6c4e09b9260991148f8ef3ed6b` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:bd0477934aca03ca18ec5300fa3db3dc5bbf310cffa7086a8776de47f5d55e74` |
| `unmetered-cone-work` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:ea953cb9245f335c1cd2072547c6b5dd1dfe9e20a81dca51eca277d874d4e03a` |
| `unmetered-dynamic-support` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:bbcb82db16c13abaf88b2d0a0afc2aa345235c7926a1add086de0f8090fecc4e` |
| `unmetered-object-payload` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:a4ff94c668bdd9f7a2198acfc060c16e161a4f9946f348cbe50c67d058d5675d` |
| `unmetered-support-construction` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:33adcbb8dc7c85beb53db6beeed2f4fa65a3aa7b9250cd8bf893678e78507f3e` |
| `unmetered-tree-paths` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:23e8841c4f18d00df03a75b99c583f4926abcdfff4c72a7f959185b030dbe329` |

## Measured cost and object recovery

P22 measured 133 graph commits and 16 disappeared actions with exactly 1 POC graph enumeration, 0 POC-owned per-action history walks, 10973 snapshot requests, 10970 snapshot-cache hits, and 135 actual Git processes.
The process count includes imported production `git rev-list --parents -n 1` queries; zero applies only to POC-owned per-action walks. The POC's single budget consistently caps every emitted work counter.
PCX-20a passes at its exact measured maximum 5645 with limit 5645; PCX-20b exits 2 with zero partial results when measured maximum 6102 exceeds limit 6101 by one.
R17-precharge-P22-budget charges before work and aborts on `measured work budget exceeded: object_reads=134>133` with exact bounded counters; the post-hoc reference vector is retained only as a damaged control.
The 64-parent boundary case stops at parent token 8 against limit 7 after 2870 of 2952 raw bytes; the graph child is reaped and no graph is published.
The closed runtime matrix additionally admits/refuses exact/+1 values for total graph bytes, peak graph-line bytes, a 1,000,000-byte object, 1,004 flattened paths, 12 dynamic support paths, 2,920 serialized certificate bytes, five origin-arm nodes, three origin parent edges, and 1,042 canonical birth-witness bytes.

PCX-19 is replay-bound by `sha256:66a79e56ad3d7c57ee17fb7d1c7478d50700e1514a02d5bc98777f90de767f53`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.

## Reproducible audit

Use two fresh, empty scratch roots:

```sh
PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r18-v6-seed1 > /tmp/production-contract-r18-v6-seed1.jsonl
PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --reverse-construction --fixtures-dir /tmp/production-contract-r18-v6-seed777 > /tmp/production-contract-r18-v6-seed777.jsonl
python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r18-v6-seed1.jsonl --compare /tmp/production-contract-r18-v6-seed777.jsonl
python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r18-v6-seed1.jsonl --damage-test
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --old FULL_OID_O --new FULL_OID_N --origin-strategy U
python3 -m py_compile docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py
python3 automation/run_tests.py
python3 automation/reconcile/reconcile.py --check
```

The auditor requires raw and semantic equality for comparison, rejects
duplicate keys/IDs, enforces a static recursive raw key/list/type grammar
before projection, compares a fresh
manifest byte-for-byte, and regenerates this README in full. Its damage
matrix covers invented/duplicate/missing rows, same-region OID swaps, tuple
relabels, false verdicts/counters, contradictory transcripts/digests,
unknown raw fields/cost rows, locale error drift, post-hoc or unmetered runtime work,
noncanonical ordering, BOM, CRLF, and missing newline.

## Nonclaims and integration gates

- This executable comparison is not production-ready and does not authorize production integration.
- This POC changes no production reconciler, restack adapter, workflow input, schema, task, queue, memory, or history record.
- A post-push check can only be advisory; prevention requires a pre-push or server-side production gate.
- Strategy U accepts only typed legal live-incarnation births and does not prove squash, replay, or cherry-pick provenance; a squash that creates claimed or answered state at birth is illegal, and deletion-only resolution provenance remains unsupported and blocks.
- No candidate-base or provider base field participates in attribution.
- Fork/pre-PR transport without a trusted old O is coverage-unavailable; no reflog guess is permitted.
- Local pre-push uses remote old/local new; an offline wrapper must capture O before rewriting.
- Certificates intentionally overbind non-action authority delta and referenced paths until production exposes a validator-owned support receipt.
- Review successor/reask and boundary-review supplier leaves fail closed rather than simulate semantics.
- The one-pass claim excludes imported production parent queries; production integration must cache/eliminate them.
- PCX-21/22 remain production-integration gates, not isolated-POC completion claims.

## Tests not represented by this artifact

This artifact does not claim deployment, a real remote push, production
adapter wiring, server enforcement, or unsupported review-successor coverage.
