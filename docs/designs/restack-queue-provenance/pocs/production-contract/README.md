# Production-contract provenance POC

This file is generated in full by `audit_readme.py` from the closed
`evidence.json` manifest. Do not edit observations here by hand.

## Result

The real-Git self-test passed 153/153 scenarios, 4/4 executable aliases, and 28/28 damaged-mode controls.
It imports and calls the worktree's actual `queue_action_identity` and
`queue_deletion_problem`; it never invents an Action-ID or lifecycle verdict.

Canonical evidence artifact: `sha256:f899e94961c573a50976ed2a747c8b4e1dfaf11d3c656477ffa219e7539aa102`.
Canonical semantic stream: `sha256:299e6639c941ea0162fbbead8e24de09959200ee55e6706ab5ddc11931cf2e98`.
The raw JSONL stream is ephemeral and has no stored hash claim.
Evidence schemas v2 at commit `0b80c342feb310d73de6564aab2224a899f42486` and v3 at commit `7f4a1ffacd1cf8163f597daa186f801e9ce06a3a` are superseded and burned by their later semantic/evidence blockers; both histories are preserved, neither identifier is reused, and this artifact closes `agentfold-production-contract-evidence/v4`.

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

## Bound r17 review outcomes

The exact reviewer DAG is clean and record-bound by `sha256:a3be1d077c6afca724f1613b04cd8a65fa741226066f29ecca06d8a9e62aedbf`; its outside-C parent is neutral, its task patch replays exactly, and production deletion authority returns no problem.
R3-03 is blocking at the fixed N frontier with one invalid authority edge and is record-bound by `sha256:65d4b02857bfef6bf3cd8f84a1600237d236f979f45624ab459d599ce339f543`.
The hidden-G attacker is clean at exit 0 and record-bound by `sha256:056377eb166a54c2a70fae073e36d8b1b2425da4394dac6e5dbc063ddf115756`: F is the neutral boundary, G carries the same identity in a unique missing blob, and G ancestry remains unopened.
R6-02 is explicitly dispositioned clean and record-bound by `sha256:646206f033211903160c7f6103f3d0b5a3d727db374764df1cb20d9bcdfc295b` because its outside-C boundary is absent; the ambiguous ancestor behind it is not reopened.
All eight persisted-state attacker cases block in both parent orders: outside-C exact carriers retain multiplicity 1 or 2 as collisions, while valid and unauthorized absent C-descendant arms both remain deletion/reintroduction competitors.
The 64-parent outside-C octopus exits 2 transactionally and is record-bound by `sha256:fdc63639f7e46a6576855bbbdc30e0f699c9f0ef8a9cf5f2d42ad191707019d4`; no action, edge, support, or carry-proof result leaks past the exceeded parent-edge budget.
The P22 pre-charge case stops exactly at `object_reads=134>133`, keeps Git processes at 4, freezes later counters, and is record-bound by `sha256:48c997a5f7d2f26622408474b66b004ee001bf2b7f84255bbaea5c662410fd38`; its post-hoc damage reproduces the prior 10,973-snapshot/24,736-cache-hit full run.
Unreadable Git objects use the stable typed reason `missing-or-malformed-commit:b5fcd8d0260da07b741462af3e3e2b49b546d600`. Every Git child is forced to C locale and UTC; the stable C/French results are equal even though the independent ambient diagnostic streams differ.
Before any projection or digest, all 184 raw rows must match the static recursive key/list/type grammar catalog `sha256:6e9fdf26259f62fece167ae99bfd55b909bdb351fd6ebb6fd91c0b12a7ee8d49`; an unknown top-level or nested field exits 1.
The parent-order pair has identical verdicts and the same role multiset:
`['compatible-carrier', 'source']`. The four persisted parent-order pairs are also byte-equal by semantic signature.

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
| `docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py` | 136294 | `sha256:edd9a6d2a5357bb6205b0f4e98c56035a6109fe9e52c26ad39306ed55ddbcb4f` |
| `docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py` | 386860 | `sha256:077aac0d663750dd7144238156a82dc9dc17c9cb52b61a35ea39fa738e3dc585` |
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
| `P1-direct-linear-valid` | `46109f507dba3eeb6191db457fc7848c415e8979` | `2819957948197a593fb1d0dc966e747c44db9ee5` | `029be55decf7d7f65826f86684cc8605d5d47b18` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:97f6fa38f479b53751dcff0f3ec4c079602219429ac3c7725c0c6abf33e4b701` |
| `P10-direct-invalid-parent` | `2ef716a2345dffac470956041b5245e20fbc8f98` | `1ac818d6b6ce87da87358e55015671ecf823dbb5` | `8f7e8c69c7ec6e4af250366114c90ecc24ce811d` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:20705eee03dbb12f2aaf425b97dbadb7f9af57f479f9edaab25f9cee4c77652b` |
| `P11-direct-three-parent-valid` | `78ad042cef55f824658b367d8599c5523b4e601d` | `b5726dd5f1e717518fae85cf820fc7b134db83fc` | `ad16f6d1f31e155a41a236d51a7a396e54dd5ea3` | 0 | `no-finding` | `valid` | `direct` | 3/0/1/0 | `PASS` | `sha256:e7ffac054020cda0c8014ba288e24f1de3a5847305479604038a3b93b1a93f12` |
| `P12-merge-supplier-valid` | `3a01d100e676a9a20f8dc545fed19be3419fb759` | `bc433c8ed8cda37d3813042f730b2f23d8e8d778` | `8dc6dbc10535cb058ee49c63a979d75966b7f248` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:0c491251c6b1a30600c926954f898026ed08a1f730ef8a6282a3cfb990fb1db0` |
| `P13-merge-supplier-invalid` | `c9de2e4ee2e285093b2b1ae42b597989f5e2c267` | `898789857318c82970d920a105ee1a124474e155` | `9424f0b01381a9388d58b77c06efec9a59f0249f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:d34df0f9940815ee1eb199d92cc869ddedbea680f43d705394120bcf6f96788c` |
| `P14-supplier-reintroduced` | `f340f1d750e747d6cf6a74dfac05146fd208f964` | `bf8487fe5085a4dc4b483f512c51ecd10cf7c253` | `14d300ed67dece9c599e5c0d096b708cc38bafa6` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:364dfb710eae44e1a47f455ee350bf65feb562299628462ae81ea42d74bfff2b` |
| `P15-competing-suppliers` | `80b72ef13352057aa74028971730fbfb266b56f9` | `20a4f077a613c17b6e3f36d87f807bed9395d541` | `fe575f3eecc1f2b034bcbeb17a0021fce16bb82f` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/1/1/0 | `PASS` | `sha256:82bfe89227417070b20b1399c6204a8ed011159a3e8e6ab8b9e9e5eb0499db09` |
| `P16-PCX-08-invalid-supplier-claimed-carrier` | `b76e3dd3be1c4896d95f0ade31b63eada3ec7002` | `b756376fce02251f8036c1b1560d8c6c96dd0699` | `b23ca400da3968f74afc3b950ff4d4eb27307196` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:9b0ba7850b20e67b768022736581ae6a43310d5d9af58063b8570557cd40f12e` |
| `P17-post-event-reintroduction` | `ec84d0800c660f6379b21cfd721122fa06162999` | `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` | `258e858010ccd1e43716ab0269faa86ae08808a7` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:9446c62d9180ae9f8d89bc67543638c8c63757a8bdf8ea0f42354b8bbe3640dc` |
| `P18a-missing-tip` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `907f5d5221680a4ff7eccd647bcf26bcd5e9c4d5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:3fbd6661684d72f660a839240c4182bd7dd3cdea7fc900c2269e65fc5956e6fa` |
| `P18b-noncommit-tip` | `None` | `90db16de6c0119c0c924c80d206b1e80bc3d2331` | `22be33aff3fad75ef91ab1e1cae2f2f8da2987d3` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:436bfc1e61f477d044089d1d00ef7143e3b7ee0c362f5ea732cf46e77f1425a4` |
| `P18c-unrelated-tip` | `None` | `22628ae24f01e250d30bb4cf9c2a7832f217677e` | `e46c2df2b7bdeeedf09b55b74a3745ea6d7f5139` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:2be89ef4e6deb5ea59223916b0d0a83574c83ea126b44a40cf9bb97e897717e0` |
| `P18d-shallow-required-region` | `None` | `e68bb90fcc341adde9f4372caff5ecc6f9b1e340` | `4303d2f9587973759de42362a6c20b4b48170ab5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:5161658fe06c02399c3814716e9c11e1fe4bbf57cdaf1e62f2098acdd3c183f1` |
| `P18e-missing-queue-blob` | `a668e725d1233ee7d5930c077268d222dd27c277` | `8d7223893ec84e193595fe975a53d36f893502cb` | `ec9f29e0560c60e66700496cee9ce14858aebb4d` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:d0873007175a8995e03af83039a4e39715c6c622ca0b88f3b04ed254fbd6275c` |
| `P18f-missing-queue-tree` | `80ee9796305f288404f4aab5960193d8555c5e5a` | `61e6b7c9b52f0ea9ecb35c5bb8da8211aa7232d5` | `4f08ffcf2930d3d3a121b453b4b16a5b5f0bfa73` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:9e7dd29cecc655a77916dd6ce22256eab8a65bff1b14843bce0d221c36bbc1ae` |
| `P18g-multiple-merge-bases` | `None` | `c9a1e28be75d020fa3222bfb2a5b04649329083e` | `8e067847820ccf0c7ed10b39c330162e1b10d880` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:c8f1e3af8574de837735e25dc47f098fc0ead756cabf73b81967fd2e7f109d3b` |
| `P19-production-identities` | `b9960dc72147b900fabc01a32e0057e6499059df` | `e702490de9ecf76f7a638b39d49006dc32229c4f` | `f10076f83de90580658d6d1599b0ee208b7fac87` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/6/0 | `PASS` | `sha256:ac5684f839aff3506657275583d44d60b3b34de2f4824307dbabc438bb22d796` |
| `P2-direct-linear-invalid` | `70b791b1e8a9bd24f58737e93a443451f8f0ca11` | `ab15090d6bc10c375e03aa38f1ca6aa87d672a98` | `b00411d0cb294fe228cef9fa6744869d212bff1b` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:df3bcda21fee5069eff6f08804bc47d04cfcaae09ffd7b2d2a183ec4309a8154` |
| `P20-lifecycle-types` | `dec0d432ddbb67c88d9833003f2939a596372ba5` | `d2e3aa02bfe5ddff10ea863ef5c6fe6557d54e36` | `822ee419b65be452b934eb592888a07ad6b74f9e` | 0 | `no-finding` | `valid` | `direct` | 4/0/9/0 | `PASS` | `sha256:84629e1b3c503b4a2d8188cc6c13a309ba853b5735f40ea8d74bfd012171e724` |
| `P21-PCX-17c-squash-erasure` | `34448e62dde0da7a459c9f068a1929a11404bc60` | `67154541398ed536f17c169d282b151571b9031e` | `cdd5e979ba9eeb3e6caf97b05a182981178203bf` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:568890eeed8214b33619ed0276397952a12ce8b0d90047c740dbb416282f5485` |
| `P22-PCX-18-one-pass-many-actions` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 1 | `blocking-finding` | `invalid` | `direct` | 16/0/16/0 | `PASS` | `sha256:28cadf62bf5812132ea4655b1f2dc93d40651c6753aa0b39512e7b7aa95714e5` |
| `P3-genuine-old-loss` | `94db247b706f734bca553f86045fba8b98158a6c` | `5fa1eba2f8984af57952e6c083a0c455fc65d54c` | `5dffe2d077e79208c3e05ec0bfdd5de39600292e` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:8448d5c488da66738b6508341b40e5d093a061c3011d2abc6c3cb5b3137962c0` |
| `P4-pre-C-identical-origins` | `cd13c47983b0624a824f5fc583f7de647b240504` | `03c76bf6661f670a705245479f406a1d3ba7b279` | `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:20655d7349078525868ab4c74e7fd384a5b91008b048e29b42f327d71e0b7d79` |
| `P5-duplicate-at-C` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` | `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` | `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:04c9ee87589b2f7e8dff5678efb258a6037a912ec38a359493773360000ced0a` |
| `P6a-old-delete-recreate` | `8039e1a89ee29be7b3a79d4fda7aa15a8653058f` | `900438d3fe4393f0ea2f87aa4d8dfc1e188f5919` | `6781a4eaee80c8ebde47bef04c33dcb47e91bc98` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/1/0 | `PASS` | `sha256:2552a4f988eafb999189eec3d80adfbfa73f0a5a34ccd0bb85bd10edf248c773` |
| `P6b-candidate-delete-recreate` | `b5161adf1ba6eeb99b2181aa264598f707d19a95` | `bfb4c66d18c551b23a8580132543db2357ddb4f7` | `ca9f44b0f38c99dc7c70093046ead1b19f464389` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:6d018c74912d86768efcbf11055eb1118bdb215b7e5fcbabb86652118b922fc1` |
| `P7-immutable-payload-change` | `43f673bf99a741dc37c6631d39bd5e9c037f7368` | `523cb1cb6e17b0e00b3bc3235618cfc0834d233f` | `03ae818dc35342d03432e7e25ca292808528ff3d` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:4a442887ff5506a4f0e4fd23ad2026803125be1bc08ae6daad4c07d30e9ebfd3` |
| `P8-path-timing-move` | `1c34d6196d22c53ce54eac5b2cbed46be8432134` | `f9bdb1fd1af9e2d3b5b405594d2ef37ab55ac025` | `cef78e9bb54e4b4318172d0a2b6881da3a4b8971` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:32c6495c2a90fdcd2e1a1ecafd7cfc9397aa32364cd42bd7d61f52f73ae142f2` |
| `P9-direct-two-parent-valid` | `074b437bb8582cabd4372ea380454368e8d81ab3` | `2380b58d4a6b687769359903f12100d69a543b2d` | `faa886162cc54c7c6544e33793a6e7f4342a90a0` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:ca8065358dcec4acf49a31b81857f61dfe4ec94edaa2178a030d3e9692923329` |
| `PCX-01-neutral-parent` | `ee5d0eb6e70a978d7da73147f1faef9615f8624e` | `c4b177d1b0039326cd6592c90f7ce62e729ed3a8` | `acc6673079b122e2ae443cc91c4012c83344430d` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:38a74ea9c8af248be63d80038963d74ec2a9a5b5b1ab6ce05b9bf7539451b333` |
| `PCX-02-neutral-plus-invalid-carrier` | `b02a161fd6cd727aa2eb6bdf5ec43f5c5587e04d` | `78c77a131414cb7f196137896f9fd0080bb6552e` | `cf599de5003f9d108a979cb21f6d36c5c3785dee` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:6ac5b9582fd05a4a12893e4825d1e7ef5917ba3e470bc9f34cdf380538862ac7` |
| `PCX-03-foreign-exact-identity` | `35f271b5d18393dac59002bb0c0c794d3589659b` | `36313b4892aaa243fc2d01fd05ebc8e7ac0145e3` | `f7fb0303c3061d22daf61cdeb03cd67496639432` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:712ee281802538d9807c555d8924271149a15d0d466fcfa59ab018d89d1bbdf7` |
| `PCX-04-several-absent-one-supplier` | `32c7576c4c4aca96bdad8162078e9b2a28d6ae33` | `c4cf7124f59fc3edbec373d87507aba76143cfd6` | `cb06b9b4e0a3ae842774d0f888ebb5f1bca53881` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:2bae53fbb996196371eb5cd05fa70ccaf1ed6d7dae3f4741c11205f6ccaead8e` |
| `PCX-05-competing-later-supplier` | `d297f8d7d5f3557c94f944194e6da99c1c092c81` | `39f138bf6fdf1db76fe12a652664dbdd3fcb33e6` | `5cc308cff656d4866cfd255d968e65ee17b58271` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:1c09d8f3e9f00c8310d8520f5b33f2c3fc2e5dc51beb1e8a3087f15fc77a0aeb` |
| `PCX-06-nested-supplier-over-direct` | `4fef7d2a64023363e13a455eddeac016838f651a` | `db0f6a1bdc43a8bccc8184e323867f7ed9aa04a0` | `2513214e5beaae7f3a289d4fae4018a00971c21c` | 0 | `no-finding` | `valid` | `supplier` | 2/2/1/4 | `PASS` | `sha256:660b7651ef4ebcd8bb30a05f9105b4cf7f9ae00819b13ba645554f745223df7b` |
| `PCX-07-overqualified-propagation` | `e9920c69e87c8fadecea9dd6bfce80039a60619b` | `4eb27ecce806ae96e902a1c1cb1098fb7e8d7ba7` | `ea08bb6dd2a18266bfd6f436011c1cc610c4c8dd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:0e336ec2961f59ef7f4958c215f5fc2235bfb63bfcf166d726a17a532c038107` |
| `PCX-09-recreated-claimed-bytes` | `41008171d1f9c6afd397a17c3e5567e040d881e2` | `9e38900a6d2f2e3b48457b5fe92fb55cf68ef1ed` | `626d32b7150a4185dddc568c91f3f096abd5f4e5` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:062b99dcb1073335fe717c43042e59f48fd373954fdb4fcb324c4ed0ca843fd9` |
| `PCX-10-transient-multiplicity` | `04b5c0356d29ee676d98d58fc639efaaa47278ea` | `cb082de1d3492e0b6e85918c5b1a4d2d600a110c` | `6dc48150188c026a1300d5fa19b065b1ad6a01aa` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:025564d9c9ac1a422eb78128a70db64986916eb980eda4be5d00637ac3de815e` |
| `PCX-11-different-payload-same-path` | `9f7f5b9e5ce030055a6151bed80dfb6db1a94206` | `d45b35ca53a81320262faaeb7136fd081e8c1fef` | `78876b74b5d5c2cbdd3085a992a484c82280c769` | 1 | `blocking-finding` | `invalid` | `mixed` | 2/1/1/1 | `PASS` | `sha256:3ebf2bfedff67c04ce2c40a02d1eeb8cd43736f92069d6b88ba84cb2767bedfd` |
| `PCX-12-timing-rename-supplier` | `c81cd1ddc4c58f7e6d5b9bd7f0a626f972651c79` | `e89ed03c9f3c8d338d6b4f03dfee7d6994ce400e` | `97ae732aab6ceb15bba65fdc775f3b4d5115a3a2` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:84b70873b6bf2503e79651b2959e32c2eb430cf28ed4d806e05c2656fab0078b` |
| `PCX-13-conflicting-human-response` | `58e15401aaba3e6f056f7dbaf6789c10d35ae553` | `1e790e17e8d0ba21ab1a7213d6e0e0fa2d12f047` | `14707f668aecd10bb531aa6fa0ec57700d26844b` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/3/1/1 | `PASS` | `sha256:feca61423fdad7253b6e6b12c7fed2eef47b599ce0a79fd6c729ab3d03d08ec5` |
| `PCX-14-valid-human-supplier` | `920e716ffd62703b03e21acd40423d34d60f165d` | `15ab9f04625ca7c4d6a8847bebaaa2b3169b5b69` | `36eaf058713764ea31d22a9cc74f800aaefbed1d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:5d5fdcb5bc4d36f99e944203944e6d7e95b106087d35962bb513362a87062661` |
| `PCX-15-generated-retry-supplier` | `f5df7b0d8cf5622f4f786cbe936003b31c493199` | `d66c33a79421c1c87e7477e748fbb3513f8d0de5` | `5f8251bbbc8ce9fc2742bc88cbd70bf88615b05a` | 0 | `no-finding` | `valid` | `supplier` | 1/1/7/1 | `PASS` | `sha256:ae2fcf675c1b714e340cadc6f86dfaad60e0b108e4fc9b7053f15f8a0a6b6e28` |
| `PCX-16-task-pickup-supplier` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:83c7c47a83999ea1ead52864ef1070a520b0c5af5de08f1fa7e2d4c59ade2049` |
| `PCX-17-complete-cherry-pick` | `33db81167dcecdaa77e3c6e97ea6305b99d13346` | `8385f0c8c1094932a794ebb94b32b4d872806cd2` | `855eaa3b813900caaa0e523baa198491cb4bc47b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:b635b59e1e694ff5757b172c8b0c5c5133230e8f5e44af441f1829ca2e4af45a` |
| `PCX-17-deletion-only-cherry-pick` | `56008eecc6492c2c091a516834d675e283cc40bd` | `35b9163866f1c9cf6ab2435eeba3abfc0b9fd1fa` | `5da95440d2c9065d8b6f4506d2108a3f97bed539` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:433431a3d0c7771818b11fe7a6099d06509ce1706f00f036ccd212b53bd24b12` |
| `PCX-19-missing-claim-blob-recovery` | `759e2f27b42fa1f3bf68d8b436eed022ee8f1f5c` | `90aed2b3f8214a269d6421e6f4fe63ad3a61b091` | `dd34454f3204840ae81e2f273772c00488e681ea` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:824e0da528869df0b67e25e6e310937f4a13b4763821551c3dc85333aa760bbc` |
| `PCX-20a-budget-below-limit` | `c957293f54b1b960b7b7f351087c77ac874eb253` | `ad76497bc5fa23076fff741b5d419a2ccd714637` | `ce775146b901f12bc2c05d22f06343da4d2c66d0` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:b831e3bde0d0f6c44508b47e55aff48b555853a88da221e1214206810e06fe9a` |
| `PCX-20b-budget-overflow` | `a018c90c3dbe1374339730ede5c7b76e21fee985` | `fb2043655802898f2561cc21431580a2609aef9c` | `06abdb0e773f19b6acc2ecf85d17e6c1770e7295` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:66c129b35b593a092bc1f77bd7f7ab5e271fbb49e4af66f3256550c21f27ef45` |
| `R10-direct-review-target-backtick-dotless-rejected` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` | `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` | `ba4edb8f323adba9645e47c2536f2b621bed7855` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/2/0 | `PASS` | `sha256:5e798b3785b6e6c3ed47a6b69f721c338c1906318927b37bc11a960c24d186cf` |
| `R10-supplier-review-revision-generic-placeholder-rejected` | `b13043f4864a963aee7af4e3e3a913313f9f7b19` | `9d96a7eecc2b34704ef588142e4b48111849f3a9` | `02371c1e8f0eebe4e567694cfe6677c8b872a7a8` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 1/1/2/0 | `PASS` | `sha256:2a57143f4b730fd4652247063ab954db189d4744ef668b153cfb2c340b79527a` |
| `R13-direct-review-binding-identical` | `d6d18f0c56d196748c9a94adad1191e68722eb4a` | `7e0284f9a2354f44218502da59ca365cff918285` | `88dc201a2aae2ad0b8984b58fff19f45c78d7859` | 0 | `no-finding` | `valid` | `direct` | 2/0/4/0 | `PASS` | `sha256:303fccb5b56683d84f0f010cb868762fa05d13be75688bff1191814316922628` |
| `R13-direct-review-binding-revision` | `f7d60f4ef43874a6e2045634265a8bb7968e07f4` | `e51c37206f2fa3f2d3a5ee9ff92aeaedc0aa431b` | `a4d2d52e8f40a5ba80cf350bd00db494c92c2eae` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:95c50bd2613ec8ff31aaa70f525f222649c91d563244966748a892492d599395` |
| `R13-direct-review-binding-target` | `8454b9025487d126acbb3eb278584199e4d93bc2` | `75d9c282afe629e2fee58b878ffe93481926e719` | `74f92dd03eaf05333a9e7168644bbae38b7bb50f` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:8d02b236e0c12906fe43783e92dd836c9d0ad555c1d8ce45b8a675eba5dd70bb` |
| `R13-direct-review-binding-terminal` | `32a00d09012a40145f9abdaedea2734348c68e5f` | `d784ca71704ac0bd18e1a70b45c18d1994353eb9` | `6677edfd8778a755904939d01b070af66f32bcaa` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/4/0 | `PASS` | `sha256:b0b52f4c688ae512435c5a446fcfec06a14f3fe49b7da5fb67d10c7ed260b9a6` |
| `R13-persisted-claim-loss` | `5604e77ef241630dd284448a224de046d2caf460` | `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` | `8702850ba2e7f56c29b16557c496adcaa627829b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:6475af123d2c06f01945ec8761b42cd62d6dee021ff5769d1e54aed2335988e7` |
| `R13-persisted-pending-fill` | `6b710008b02a5c4b970a282ad2624b0384727292` | `5218487e636b8519c69f49d146acd9b7f8b25948` | `31a21eb1595bd8ebe46e55bb235d8d677edd6d58` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:2085bf6e9fe4ab938fc19c7a28087146512b7185c5bc7086fbac0bc24d1166b7` |
| `R13-persisted-response-change` | `68dfa83702f8aa1a82181785ff40b9e0eb0f2958` | `af35b452b83aa6f8fee2d3dcf01a951a83cc0f19` | `464115d4c500dda036c5592c6c8f21fe9a959e15` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:346d32d2ab8c0c9aedc6aa7f707a81a976f663e3e67e0731b341b20b74220e42` |
| `R13-persisted-response-removal` | `49d500f64d51f720b0decb65db3ad5163d4f72e4` | `69bbf3a1bec29fcf92121c581925bb092d1535ab` | `24126e616db515f5ee1d08d4f2da297b50e02f3a` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:12ec27eb315a4ffaae17479da5fc769d52c2917bcd2ef9bb149cc95759de060c` |
| `R13-persisted-review-outcome-change` | `103fdd9bd623d90d09b2193e9272b3980c80906a` | `2c3f7acfeeb385de256074091a38c9953ce7f1f9` | `c8a8b37e924d1e18c54dd5bea09d07191b6b0be6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:588f9217cf198d526b09cb0eebae024ce323c2e3f95aedde9817e169365b0bac` |
| `R13-persisted-review-revision-change` | `952a03b6b34abb531365195232acd149ec51e221` | `cc3bf0c5664ca51a1c1df82759aaa607efd30550` | `344c8d4e0333b14fb5b21550528242614812a55b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:bdd1247bec34edd7715fc3f9d00d90acfb7daadb8b61be6f11d23149a497be83` |
| `R13-persisted-review-target-change` | `de7f303a3f48d8d27eb65e7388d0f8dd934b4e96` | `2c37567f76cece330ee8c4997c96aa2bcd1764e0` | `4f6be0576ef37c17b25b0268542bf4003a7b56bb` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:b270da4cf0bc6093b1f1d3026a01753041843bc916a7dba7347d71957a98afa5` |
| `R13-persisted-same-state` | `0d4f188e038977d78c48829a48b12354ffc8aa32` | `a3edb26d4a2069954d0459dd9ea503cc27833f61` | `edee50f1fe44db9136335db0de7e27ad442f4eca` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:94dc9da38a05e7efab5b0763aed44edd81df97618b6d72b59a03ca6b7331b671` |
| `R13-persisted-terminal-fill` | `ba73b784939318c875041e869d49a08cfd88f440` | `b5ea69a78713ea41e8229125a90fa2718088c6f9` | `8250a2475da8b2c1a0dfffd5ecbe3e73fdd9b838` | 0 | `no-finding` | `none` | `none` | 0/0/6/0 | `PASS` | `sha256:94134ff7b836dc6b49d0d95da3bde279094ac956dd365ae61eb952cbc79fc94d` |
| `R13-supplier-review-binding-identical` | `14976a93658e5bcfe9339368e77f82e77f31830d` | `ffc5d33bc00724fa377f13ce6ed824f6dc9fc02b` | `962821fb4d4faabe72c3b8e86823a5367aa3294f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:804534d75ec7106b4635163bb08fab54d2972d66c561d06be9e5241a5371fbf3` |
| `R13-supplier-review-binding-revision` | `52fe1848f1536143161e717bf436ee8c8b07df59` | `e7a884697094e9be1c876b78fc33d9e259d92149` | `8fd2e814f38bf145bd7c84d9e22a355056d40649` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:61d69c41d6ab41384441e816e8d7619d515e902b3d818e25f61f841ea61c41a8` |
| `R13-supplier-review-binding-target` | `874d2e356033d133cd409bc9deb8e93198d0ec78` | `adf1ce7876b84e595992f5865f871b59ea892234` | `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:f67c3049bde8b617acd5589340d0cf52b1ca3f6ec4211d02ea5567eeb8903f83` |
| `R13-supplier-review-binding-terminal` | `e93ff6925d5008e9c95866628b410dda5b293e91` | `60538a926a9acd01f898ba0371ad5249c912f7fc` | `1031e6315881cdc99376df52bcddc86a4427e920` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:c6e5dd7f13a5273398ec6558586f7d080ea3f66e7403b2c548dae19bab21c4eb` |
| `R14-direct-old-unanswered-carrier-same` | `c1a83b69fb7f04ea375aca7027b157dd9cc266ef` | `37d577cc2c265e8e7082bfd86dd156172db98c5c` | `ae63528ae1af829ced9c2f1b763cc6aeb8c054ec` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:d0319e698284418268ecbca5d63efcfb816418b564de9a5ab54661865ddc4a7b` |
| `R14-direct-old-unanswered-carrier-target` | `0f221025b8224d465679596d3dfd44b6023371ca` | `d39ee31be16db2789928827c2e132a31e22b828f` | `9c07f77ec2836ec0f4222313e315b3ddc31c4ccd` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:281a03f0eafaec101a9a95ad816a6188f56ca0e2fed638892a1a414657741607` |
| `R14-persisted-delete-recreate` | `32c778b5ec16afe676bcd2ce898c89388b28ea0e` | `68f01125491f31f259d6cc636bc2f818c9529571` | `0d272d85cea3703f4fdc3aedfa7e821374de51ab` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:97d8d56713f0347852ea2d3856fedab46cbae399789f2b730f438337f29ffc28` |
| `R14-persisted-hidden-bytes-low-similarity` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` | `d115e7063e3ffad24a495c9ffae5d70ffaf81928` | `a47b7307d654cb07612ccd7b04f1c32ab874c475` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/3/0 | `PASS` | `sha256:b8798d7d9340ec53dc42958c2a5362993414b0a3b489cb3b98288d5e3b400cd8` |
| `R14-persisted-intermediate-claim-regression` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` | `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` | `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:b6a32839145fac9442e482483503050ab14817162f05c3a9e63131059f3e3c46` |
| `R14-persisted-intermediate-review-regression` | `5fe7bc2ba01136ca7e91068de3c21394628d8616` | `ceeb45bc58cb8e6726517130e20fff034db993f3` | `b7e814f11797fcf8cc10f0a41b0dd8f0849718cc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:bff554b49d88aceea04f8e0c2e86235a59d7aa4b4bfb2b313aad2120e6820bf7` |
| `R14-persisted-merge-carrier-conflict` | `00a09440e320c344f9840d7939f97b5a72654aa1` | `521e76aa7253b7dc1214c2bbdca5c788a601e21d` | `e2f3eacb8b4a86f383f8a76be26dac7e4966edad` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/8/0 | `PASS` | `sha256:862288d9f613b50c1fd37c15cdf93e6d410914c35b18fbdf47325ae9ae7e6695` |
| `R14-persisted-merge-carrier-pending` | `01b493c655badddcf6641e8a7d21d3594a0cb5c3` | `74442946b6639f57e7167838a13cc286f39d3519` | `ca8939b406b7b2323fd08b044625639f5e80cb6b` | 0 | `no-finding` | `none` | `none` | 0/0/8/0 | `PASS` | `sha256:8a634a1183ee5f724bd7d9567049a2a946803e95b9395ba95eaf004c6e7022b4` |
| `R14-persisted-valid-first-response-low-similarity` | `b14ffe7afbd09ecdcf3fcdecbf99fcd42e5f9e59` | `dafb69000967fde6234bce7999767113def81c5c` | `690a6c7b5a5425bcd8a3abfa90b75c77ecbde966` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:25692d01854de525b05c8f816d3c610dc17153c9b7d8f3b8766d107ed70bfece` |
| `R14-persisted-valid-review-retraction` | `58a66e99ff34cdfa5e2bd150d68d5d6121b0cd71` | `03f6cd5ee859d98e6110b2554606ba655ea9b66c` | `75f7c3689154b3ecf8e5c67d467e338ab24a47cb` | 0 | `no-finding` | `none` | `none` | 0/0/5/0 | `PASS` | `sha256:16e9f602bf11b5568257933678bab6fa09a1c8847922117470779f2b844fb9bc` |
| `R14-supplier-old-answered-carrier-pending` | `7f104616c4fd6c3d1f15d7467a7e0da9e164f6e7` | `6f1dba05d9dca3e3776da3c7005a83807190ae74` | `0662f0827db1ad2e39f59626dd8d87f316b73421` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:2bbb0c94e6e8c35cf968588c2a354e375b30ec13f043b07e0c5a6a84e2b824d4` |
| `R14-supplier-old-answered-carrier-revision` | `9121f39bba512fa9fd762c3d07c93d1c11d5bc42` | `6d9c8b1bfed15a512d68db494efb71a2d0577f33` | `0b0243e67b4d4635716eb2113f81419da982ba3c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:1f7176501103ffa0ce8c189e92980c83ecc3089b9b9a4247e85b2a4a20c82cd8` |
| `R14-supplier-old-answered-carrier-same` | `d87b23dffb37c46a64f0f37fd10db886fc100532` | `a6ff10d32896ec2d87dad1696b24e07cc73ead65` | `9f1c795a2f4fd1450d4d524f3f7adbdf0c496c52` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:275aafb2a38ba6e7a462ce4b656c2c5e4cd562ae622997fbc053da019d6b85a1` |
| `R14-supplier-old-answered-carrier-target` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` | `8a2de576d9304a51988bfbd943749129f828f882` | `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:197fab4215defaf3d6b1ec22632c46cfb32d72078d10387ed4d5b75ee24cdeef` |
| `R14-supplier-old-unanswered-carrier-same` | `186d0ffca8ab62c6de1677780cb4153eced4fe53` | `b6e124010b1f74882864bdc3dc1fbd289fd5305c` | `e9e33f66742ae613b738497753ffb4957610b85e` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:f6cb591f673e100d19aa64d97cdeb3b67416994500785bbaec96b81ce3b35bd0` |
| `R14-supplier-old-unanswered-carrier-target` | `9109e916c44dbeaa2bfe0e3b5497e9d98ef3e9a3` | `a09f2f2ed771008847609d177c72e0b1f62d8084` | `0c38b44e67a3ad27238aed8c8a667837aa7fc444` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:822ca8c9014a047f2817d13ac991f67619b0f6925f3b9c6da2841eb1ff679693` |
| `R15-old-continuous-preserved` | `9972c0979b118b85b5c9d80a811679b41840910b` | `6e29170cbd7791baf6f74923a50387a9359979e1` | `316e8cd76611658ad9587c73e54cbfb6f3c9f379` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:3d30233145b913d518fc227e789046869dec2782ec00bd4f76609c5a0d31d154` |
| `R15-old-hidden-bytes-restore` | `600ae7430233c349c25bbe4ab0f9f8fb55e7c92e` | `023e0594e4a6d2f3403635decbac7a9d90ec06f0` | `20096f8d2a62bfe7e6990d90b91135ef249879c6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:43958f6a4b2531d166aa2c394dc130c0efbdfe9215b9ecf983b73f40115c437d` |
| `R15-old-human-binding-restore` | `ed9337d8d288a493c724a71081e4db71972e2e08` | `1d8e4411979ce8ea8dc5697180f8d17be74f1be6` | `fce1db3bfd0846d5af6dcc96b362a52baec376bc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:f2c63ce7a9455e484b5b252c4d923f5981365750c2a55075e561c1c7f5e341b8` |
| `R15-old-invalid-delete-recreate` | `f26bbc4c9cdbbf3ad4b2cd18c03b6ae60ef51fc4` | `4fa6ffd247960df785d1e957e4cd902382e8f437` | `b3e62e6398e4ee29f708d4eca4bd98a4b699b015` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:95616d1857ecb796d8cc3909cbb5f12c8ea214a987c5cc3ecf69b0866069337c` |
| `R15-old-valid-delete-recreate` | `d949c6358b9809dbc4c19c55ccc30fab511c7413` | `5f6066d0642c29fbb3414c54445b8ac08d5c99ff` | `de690fe09e6d88d499db4b3ebccdb7dbfb8b5617` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:d6e4f4816f614b56e2ec60fbc6b89db049ff3c15fac47862517113ed8293bd86` |
| `R16-earlier-landed-evidence-reversal` | `e731036f833027f6e32ae9d17deec1f1b3114412` | `f8186fb2af1ae0e23196a4ac0095582433643daa` | `aee42abb66d8ba55343efe6f741c32987563844e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:fe30b20aa999a5c476752d362d1d28dcf70c66a2cffb619de080907e4824029b` |
| `R16-pickup-evolution-0-backlog` | `41945ab0488983f425986ec3f815e50e974be318` | `ddee8c3c0a47baed150ff41c81fe3dd3578991e0` | `50ddfeceda267269a756eff178f2e6f2dcde7af7` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:fc2c2f90471fdee68f9963532cec3c73edc912f2d915f464a6c7b17c049e5701` |
| `R16-pickup-evolution-2-blocked` | `e7e14e5b5790e4682f7609b3ca494fc9fd1e9218` | `97de8555908750bc8bfe4f195811124e6639b33e` | `48a4d96e210ac69ff036bff2bd154d6e496e6a05` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:822e92f14cbda32fa9978523e00303fdab18d93cf299f9ad2b610b8c12ca89f5` |
| `R16-pickup-evolution-3-in-review` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `66aae1f38225afbdde6a9af1c261223a7505c461` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:8b0ec7dcd65b7af8f954182194aad8c9cbee97650c22c6dbd6983c097b25d44d` |
| `R16-pickup-evolution-3-in-review-drop-artifact` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `04e4cdf6f4c210ea0a27c59ed86f1d01627024c2` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:7c763d1ecb04fa5fcad07ffb1daaa7a49af94f5dd886973afae8aaa57d48fed9` |
| `R16-pickup-evolution-4-done` | `28b720891ddfd4c7291ada824d3d2196cf4a560b` | `da9ebd1326c500e7d2c008fdb80f43be5cf13ff9` | `a8a309c333926cb8144f022c4356736917e5907f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:d447cb36378f5d980da2af9824bb63461264f1ad2dfcde20920bf38217b9817c` |
| `R16-support-adoption-drift` | `a831384530c69ef834d1d997c25ffb996cfa4bbc` | `be001bade214359024c192e8b06d79229261a4c7` | `ce12604ff0140d20fdda463a6140634b62f35bed` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:92c77b6ec6f9e9a8c0662762a91ff9176b02c7ff33322f96f62799b87cc35837` |
| `R16-support-forward` | `8617eee2ba78f3977a9e7e0329159f725633daac` | `4690d1f06ca2513358bd47fc88e8dfdee3a15d71` | `9e15331efb2e68a1762d26fed1df245232a40f2d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:a4b815b50c51f502e53a4424a02c81833d46ae84d5386e3d476899dcf20f666d` |
| `R16-support-invalid-source` | `b5e005e8c934907d6548515f752cba73b79797da` | `8cc15771a0e42ecaa2b04166fdd57589976cb454` | `2c6d7881177ab459839ec9bf195c035cb8faeddf` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:b3c6207b17797c1363e50d471cdb43b644af57e62e9ff9e87ea4fb9fbb990678` |
| `R16-support-nested-drop` | `168496fb2f34612a9276eab0151b2b83bf1edd88` | `13967af6be58e3cbea6ee31c6f54f6c39b246626` | `95622f34bd3618ecc561897fe977861d26c1a4c8` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:e6571ef316e6da8863219f6f57f698c783fb05f5e769dfb3f519e2abb782a2f9` |
| `R16-support-permutation-diamond` | `f3d302490bc5c12be93f9392e00071fef0822ffa` | `b82141d042aba0552175891be684c7dd7eccc579` | `04baf28178f9b9b80761050e875ca2f993b4792a` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:0b995c04629835746e9b32aa83d01846c6d19707c195e3234daebb2c13dab09d` |
| `R16-support-reverse-drop` | `96de2cbd6d1afee44ffb6a03dcd12ea53ade9d70` | `fdd6aafdea7adfb0255ef9c1cf12168a23685d00` | `c24c0ed6dd25307717255c297879a96ee8c40f7c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:a7ba727a4af6222bc86488bdb4e201a6365f795215e6f0ab421e01dbbaa81aa6` |
| `R16-support-reverse-preserved` | `f3b2fb92a748ae2b38142cc01b1542b5302dcdfb` | `1f62604717746cdf35f2f13b4efe8789e9a73118` | `e38824daf72c0fbb9c049b6662fea36ad262f8cd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:b35881aa87fd664adab2212c3d0d6ff4b36f48763ab928fadd6f62cacb36feeb` |
| `R16-support-source-evolution` | `ffc5faa56114e44e8497228192ca4daacd278179` | `91474815e967e29084c0d18638907fe068dfd87e` | `2614fbbda55f0fd12af32872df6361a290c8b12b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:23355ea62a28929c3eaa06baed8cfd58606d15c29d29d62e6073bdfe6f2b48d3` |
| `R17-carry-absent-arm` | `a3cbba79bd52df83262715df9652f338ed3b7f5f` | `a6a471c1129d9af27fd96ae12ec4bee2d2f326e5` | `a5e82a41d59db68164823c9fb5a58359bcf1ec49` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:bda39e824581e99abd41ce9e69ae0f549e7b4f7fe16b41e4753bc34db0cddd8c` |
| `R17-carry-compatible` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `ba001beceb64bc88110a724ad6da2ee3498c8c90` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:d06872e07d527093292e56154707faf1c73448ed35ee4947a5066d593ebd2db8` |
| `R17-carry-compatible-reversed` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `b4684c533ad9bfcb5918dfff653a30eda3e53d66` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:0c7f7438e5d075ea9870fa5d4f17a59f42883adc69f491200037aed3a9207ab0` |
| `R17-carry-incompatible` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:9d260bc2c138b0cd6beec9ce16af63f682f6a290b1e68230566d60938ba89452` |
| `R17-carry-outside-duplicate` | `f793332edc8b2cbee979959d560c177365267cb6` | `723fbd86c6180058e653f7b8241401c172a7dd1a` | `0449217881a784a7c4bb1ef1e6b8ed1a5fb781f5` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:4d01ff3ffa184fbae4820042a72e80ecfa7b08452ac4aaa0588b4d8b248c98d1` |
| `R17-carry-outside-single` | `446a8c37bb272b847634d4f51ed29d6bdf9db1a5` | `5f2c5d5e1489b14b10120ff854459b2e71944fd1` | `60e0f415b3d0d3c59e0a7980c4efbc9868e1d576` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:4cd5894ed18cf728cb74a4ee74cf626dae7ef23f75d28aa1649376e764e3fb7c` |
| `R17-outside-C-neutral-parent-valid-restack` | `d3d362d37559714b75cea48eef7f44a4547f4e2f` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:a3be1d077c6afca724f1613b04cd8a65fa741226066f29ecca06d8a9e62aedbf` |
| `R17-persisted-outside-duplicate` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `481c03e8e4afa0b3dfe37df8a244bc53823811f4` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:6843aa0d8fa2d45a1ef543536d16504b69483a6c78073bc41112723f27a2c99d` |
| `R17-persisted-outside-duplicate-reversed` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `d74cfd74fc6648eb13bb52ad192ee13b4146155e` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:add5cef5b0dd1f92896ec9e67067b3539cc329846b391499a1a34b885421d81f` |
| `R17-persisted-outside-single` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `32a88f55e904d1892fd473b62f3d30a4bf2faf24` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:cece88a448bc658371178cf8e01b90ee8d9b42d6f42bf11ce30a1794b5206d22` |
| `R17-persisted-outside-single-reversed` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `4a231bb4516e6185d7ade17f5e5cb8aaafcc0613` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:c75a428168523bcd25e5e20ddff2cd966fbe013aff258aba8a18b8b2edad00dd` |
| `R17-persisted-unauthorized-absent-arm` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `c1e4c835d0ece38b56490f0beffef88494aef8a2` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:9eda60c11160a7e77f70c76e3f3a2ee8e8ed686bf072f7f79b67cee706fbc516` |
| `R17-persisted-unauthorized-absent-arm-reversed` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `6a55c69bf40bfcd9abe33bababdae51ad111eeca` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:f65f345c21b63cd9a3a1d1b0c50ff4fa60457ac6f49bdf159a5f5a59754b9d70` |
| `R17-persisted-valid-absent-arm` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `501cc5ef6cb38be7a83d37b9f47d26cf2acebdec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:75fdad8cb25b4881a7b8bfe8f6bd42038c720d727ae34c99a74f6e445f342315` |
| `R17-persisted-valid-absent-arm-reversed` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `12f08cf66b77738190f29720044039af1fcc10ec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:5051d05990b63298b75a64b2b34ade78bc181bd3bae5be20a950d5a505fe64cc` |
| `R17-precharge-P22-budget` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:48c997a5f7d2f26622408474b66b004ee001bf2b7f84255bbaea5c662410fd38` |
| `R17-unreadable-outside-C-ancestor-stays-unopened` | `33f9ad5aab42435cc63bf59f2b38294666dce16f` | `9490a5097490e4a7e38d8b76dded28f7d370d22d` | `508323236873cfbdf04254316378e7748f4a3959` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:056377eb166a54c2a70fae073e36d8b1b2425da4394dac6e5dbc063ddf115756` |
| `R17-unreadable-outside-C-boundary` | `None` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:bddb5288c1ec7fa19ee601b0655415c092b9f68d2b80609e8a81c4f6478b2b90` |
| `R17-wide-outside-C-boundary-budget` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:fdc63639f7e46a6576855bbbdc30e0f699c9f0ef8a9cf5f2d42ad191707019d4` |
| `R3-01-two-invalid-causal-sources` | `73373ac5106e43d8643b5b616268d77a5ca1d264` | `8f89d0fc4c063c0bbabb284434f74bcf244fb5d3` | `8ed846d60715d845a5e19ab6b299ce853a592614` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:5051062da918df28c0d32e366cd681452464234a18bee49bf0edfb3591e0470b` |
| `R3-02-invalid-valid-causal-competition` | `16722b83a642e40f2157c752a07adffddfaa709d` | `35e767d91f32b96f8f8308b431b5c6a0b35be23f` | `ff42531aadc6ffa000560bc56d995993ffa8e62c` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/2/1/1 | `PASS` | `sha256:81e25ed0fcc07b7358c073790705c840f6e80b4e0c46e408cfcf9b62e1757c05` |
| `R3-03-valid-supplier-plus-invalid-parent-at-N-blocks` | `1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd` | `ba83bd926d133cee0384ae4b8fd577de5d14e835` | `433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:65d4b02857bfef6bf3cd8f84a1600237d236f979f45624ab459d599ce339f543` |
| `R4-01-same-root-valid-diamond` | `4e831314d34c2897a072cca5b58303d8fd0e7ddd` | `2ae7f29324bd8d6b29c1f7640602fe7ec9193b1e` | `a7bbf4b40d0a3322205e3d8407eee73b9b11ccc9` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:7d78cd88aff8d74aa6f6337bd13cc60d2811514ee39fa843b4b9804130ad469a` |
| `R4-02-distinct-valid-root-diamond` | `10965dc1169826888c7d66e2389f9f90787c0064` | `286e35141edc20fad35f8b0d4aeb4930c403d038` | `37a75ca4c96e8966c19fa18afe6b6f9b1e4c10d7` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:be5e7fba9b5bef08c29116a5e21f3da403c4c81b24f22101a665ba3a705c86c6` |
| `R4-03-equal-root-plus-invalid-diamond` | `90e37b9adc7b3b428f2963282519639354bd2b56` | `de44aaea6c73d11ca46c2255f39f9b9a3d10d36e` | `3c9778ae10bc7a945bb59ad802db12bd6803ea64` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/1 | `PASS` | `sha256:dc93d1665a8fab7ae75eed10c86154cf2f764a095ae8b0c629e65c233432424e` |
| `R5-01-invalid-redelete-after-supplier-reintroduction` | `1e5dad973b3278ca8c12f3dd74f72250eaaf9f09` | `c63664276a141f3f60f61c9d404de201e6f8cf16` | `d40a531fd9a0dacb986f9259ac6f94ec0d248faa` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:8e1b604c8ca68a9a3c28d4d612c8a2065c36680cd89bea00d925d5d04acdef1d` |
| `R5-02-valid-redelete-after-supplier-reintroduction` | `79b338b3ef54382a0ec95e87a7ba962b1ec7c20a` | `9c8b1418effb6889d14466e278a7987b7e7cfbc3` | `fb0bff9778f436aed2a46f887eafb84e1c74ea5f` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:be033f58afe2538c16256e70340b1c3663d5ba25935d49ef16ff6d19ba687300` |
| `R6-01-valid-plus-invalid-all-absent` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` | `5dc5378fdc316aa30dce282d0388a438d755b067` | `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:4f79e2862e360e8324f0b239c682df4c91fdec06b744b0989c1b256398f4cea1` |
| `R6-02-valid-plus-ambiguous-all-absent` | `f61617485ff0160e37de559fe752c56ff3bcb5f7` | `10a37a2bc559519d6d84f70850b0a78445c3d5ec` | `4ab46009954bb98c5f22629274722667dc21ca37` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:646206f033211903160c7f6103f3d0b5a3d727db374764df1cb20d9bcdfc295b` |
| `R6-03-two-invalid-all-absent` | `f5141f92b29541282cf1ec520470e8c604aeaa6b` | `eb354df4fb54776834a9dff53f51f496a2bb338f` | `8f769727f1c641bd2587115f2fbcda5fdda816d1` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:313cb082a99c9324902a79f39d36bd12ec0942f3e2b4fbde001ed2764c34c4a6` |
| `R6-04-same-valid-root-all-absent-wrappers` | `c4ad2cb41bff8803f0f3d5b81ea0cfd785c9aa59` | `c3b9fb54026383a350146fb2f25243c9e8c7cb01` | `7bf74330f432155c3c39eedbfc81fa72bface489` | 0 | `no-finding` | `valid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:9cc5f7c9025ec28bba1b31e0228a20c9163850e486d7eccc3a9b5e62b70357c7` |
| `R8-direct-human-response-conflict` | `92c80d9c65c7be349d0a6c663a6a2ea9c3c2397c` | `1dc4f0dc77aae1eefaef0bb443ec187ff1efb23d` | `cb29049ff107a9a11a4ec7babbdee21819518dd6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:f7463277f3d703dd944ca54309f7ad0fe02f7a710d8fee1670afa532b93f8f0d` |
| `R8-direct-human-response-identical` | `2b79814b0bce6f1556c0b2724ade9d7bbb4bf939` | `b3879039d6d7168e89b3046e6e60e056460907c1` | `2c2289035cfc91c73564f6a97b326ebca02be132` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:8bf6fcdf471883f49fbe9039947af9361b431e45aabf7ff0fa1fc055be56ab7d` |
| `R8-review-binding-divergent` | `9b4889771f49a83cd02600a2de58fc5e6e8b8259` | `e3c594800cfe94f4f23c58060ae4ab31f50c078c` | `dc70864ec5e13a399d4966356b9803075681a0e6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:434fe76fc8845a3e91b720a2055fb5e7ad857d9c02cc4faec404819a42d92a4a` |
| `R8-review-binding-identical` | `45b7550dbdc799efed73af109da57c6906d428a0` | `a3f97a3b22945e663eb10180bde5de3b7bf790fa` | `b2dbe65f89982fb586b0fb5349454d80c7c53310` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:8913e802eb70066dabdf05dfa44a3128a20ff9fe93ed573ffb1c464bf1452294` |
| `R8-review-binding-terminal-conflict` | `cd64224f775f16bc2099816c594012a9592f8536` | `356f3f37cdffaf8f6c568a158a32c478f55a0e13` | `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:b2d524ec2bf3a7f4a64a0e588e477a3f01e3b29bce6a7a3ed5fae659139f9e4c` |
| `R8-supplier-human-response-conflict` | `255e448f3c735fefdcee3c07071c3d6bb6abb312` | `27927fe11bdeee043660e700c81e8cb3853c56bf` | `1fb9fc40da2d44e839830611cc20d0aee23c560e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/0 | `PASS` | `sha256:3ab1253896a24bc55a3d1487c8221e7a07f563d1e15551f05037654d717acee1` |
| `R8-supplier-human-response-identical` | `800658fac71a8c7fbc2d257bde57964cc96dcef9` | `f33b095abbf3c3e3225e0fbfc663b0a7f52d312b` | `e94946d2990fe3c67bc61676f66f90fab1b7a26a` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:3233efd70f25db0d3e4f559b0471d77c8f346c8e07067a1539d8bba6370cfa61` |
| `R9-direct-review-revision-pending-fill` | `00ce8c4f203a14c87a9955fece2645744ab2222a` | `6da769be2398ce26c45d3dba7845e0d6bcdc07fc` | `f5e8ec93ded434c47e27f345c1e38da95297f7be` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:70e2fdfcf863b08f33c199930a8650fa5c5bad29669d296e7ea99de864f933c6` |
| `R9-direct-review-target-pending-fill` | `7a613196cb22eb565e0f85194f7e2b8251a1484e` | `4263506464cbffb20b5f550fa142ebd391669ca1` | `8f2d8945b9ee6ffc11a714efefad9f8c1d708410` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:657572008fca80dd823b898e4117b7e55964f011509a2fdabc96a499fb702079` |
| `R9-supplier-review-revision-pending-fill` | `eef4459d2337688dab6f6681415a6f5c57cca6b8` | `9bec712c0e2453a881aa8fd36ff89d8887e07942` | `26d16dfc1e390a11c674ccbcf8281d212a19544b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:8d7cab172401d1d16614c48ba1161463b7b8a75b6a447f74bbbb2613d3a7b821` |
| `R9-supplier-review-target-pending-fill` | `8cc94bd588fa82e6bf7fa0258a7f4a3b96453d75` | `648b5b5515d697600fab0a9aa087a1f63bddad3d` | `64affcee2fe535a4f21aa80e72df2131349dda62` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:0d03f64f17afe82945e0d41650bf29b8ed345854de936381f816c4255036c9e6` |
| `W0-fast-forward-return` | `b614e3dd70da804a078bde5088d38ac9de511846` | `b614e3dd70da804a078bde5088d38ac9de511846` | `2fce4585d497e94f48f6807dd3cd9fd7b432b264` | 0 | `no-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:c62e8cf51a00d1ef105239d6a2bd8b013613f6de1eb47087a3c09f419fd80ffc` |
| `W1-pre-PR-push-exact-endpoints` | `2fb10d8c39b965cafdeb5e496e351ab258f75960` | `365339838cdfc9d6579ac21478fec9b776742c27` | `1cc139111382dea68cae0208e17354f6f75c5bad` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:47234468381143ce6c4be06851744d9ea3755309ce887d9dd4c4e2db439906bd` |
| `W2-base-advance-retarget-invariant` | `1e1e59bc5493dd584372acb3da94233d867bbed0` | `a6363187edd2b2ae4cac6d24e0bc6d4d9adfb836` | `1c48ddcef1c77fdc65609d2a077ef3cb40396393` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:0a2a413acc9736217431fb44cc47085af3d3861adaf2959bffe3e6f22f645980` |
| `W3-multiple-PR-API-zero-calls` | `7f7a2d473d3bb95a7879b5ff2c26195a4b730e1e` | `b32b24f6a4b08d17c073bfdc2355521efbcbcf58` | `56238e170cdc0358979e2cbefc7af6cbf89b279b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:499fa174375be063ca1a64672cf7e8b7a2b060468ed2f8be802c1fc631b2244e` |
| `W4-stale-rerun-exact-inputs` | `b5c4bd355d0c9fb9279be13d67268628652addc1` | `842d19ca481aa76dfcdcf096af4c550e826d9569` | `6046485394ff351e5cbecdd5c5503c44a821af8c` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:30c47683c028df0c39a6546b3818bc5a32cdd89f940d8b45803c03715472704d` |
| `W5-missing-O-coverage-unavailable` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `4923d6cd62a6ccd426bd569cc06323a11f775bc4` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:f0929d3b4953bb3713557fd3c225ded1004e56dda29bcba171ac9695621c5918` |
| `W6-created-deleted-zero-endpoints` | `fb590466fe387afa4f25743982c78e281f34f36e` | `2df4b3d62821abe8ea3f482b931ed91d256d24a9` | `1f3aa42d8428e4dd3b8b98220355e0bf883c318d` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:345f69ea7d5f47940a63e82e88ffbcdefa363cdb97abd57e350adf83d218a703` |
| `W7-PR-synchronize-top-level-endpoints` | `99342d9672d3f50559eccba1fc16eb8710b7b476` | `55bd0ff6ffe71dcae7a1afbfa440b021bf972dec` | `5a612247b54e551764fbf258e44893a0f5c40dde` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:92582afc278ef1ecdd30153ab53e52cd0bce63562031860b9667e3a0c9dcee6d` |

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
| `posthoc-budget-accounting` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | `blocking-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:a7daaf1e7e0313252ef775c662715d320253243a71659f048a0e6d035bd53a6b` |
| `reopen-outside-C-boundary-ancestry` | `33f9ad5aab42435cc63bf59f2b38294666dce16f` | `9490a5097490e4a7e38d8b76dded28f7d370d22d` | `508323236873cfbdf04254316378e7748f4a3959` | `no-finding` | `unreadable` | `OBSERVED_RED` | `sha256:157181b097f4d2be8cab789883086861525fd654134a838a42f564e262280b66` |
| `reopen-pre-C-genealogy` | `cd13c47983b0624a824f5fc583f7de647b240504` | `03c76bf6661f670a705245479f406a1d3ba7b279` | `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:a009eb9b4b50291d7cd9be8722192ad2e66090801ed093a14cf27e9469b3bb8a` |
| `restore-universal-ancestor-carry-scan` | `d3d362d37559714b75cea48eef7f44a4547f4e2f` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | `no-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:af433f685f3710f1c9a8c5488bf5581df374b7c6aad0a536cf9c5ea5a500d04b` |
| `skip-carry-compatibility` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:227154600e109348a3d6c0b1514e54872effddc9be1f7ba0ebc66880909d3abb` |
| `skip-old-side-continuity` | `f26bbc4c9cdbbf3ad4b2cd18c03b6ae60ef51fc4` | `4fa6ffd247960df785d1e957e4cd902382e8f437` | `b3e62e6398e4ee29f708d4eca4bd98a4b699b015` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:3a19d4f3b7d4ca1f109fd58c85b6365eb5dbf9e21bce3aa3e1a72dad161fa73b` |
| `skip-persisted-candidate-continuity` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` | `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` | `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:be25c6d46778bb2ae7c7c41984f17f94a41335ee62bb08a48d93186be9bb87c4` |
| `skip-persisted-frozen-skeleton` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` | `d115e7063e3ffad24a495c9ffae5d70ffaf81928` | `a47b7307d654cb07612ccd7b04f1c32ab874c475` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:8c4193947ee5457b221c3f7e0e7d097120e8494f9b663f5ac88cc3954bce035d` |
| `skip-preserved-state-validation` | `5604e77ef241630dd284448a224de046d2caf460` | `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` | `8702850ba2e7f56c29b16557c496adcaa627829b` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:24c70098bf6f1ac8767098bddbd3a29314b6564ca96b3a8e10349b51bbdc5bf6` |
| `skip-supplier-support-certificate` | `96de2cbd6d1afee44ffb6a03dcd12ea53ade9d70` | `fdd6aafdea7adfb0255ef9c1cf12168a23685d00` | `c24c0ed6dd25307717255c297879a96ee8c40f7c` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:d1b258a1c702f816d164f26803f921934c2eb2c94f103ac281f1e9a16401c1f3` |
| `sole-valid-ignores-invalid-root` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` | `5dc5378fdc316aa30dce282d0388a438d755b067` | `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:abe626b443dd6abfc3904501eb9a699340e2377c88e2e62540220fce7a8e0260` |
| `supplier-authority-borrowing` | `8d565f19c072aa8f0cef381b3f0e8fc58029820f` | `41865c9def0f066b1d121b9882872ecf33bfe729` | `8579708e09425d6c4e09b9260991148f8ef3ed6b` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:bd0477934aca03ca18ec5300fa3db3dc5bbf310cffa7086a8776de47f5d55e74` |
| `unmetered-cone-work` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | `blocking-finding` | `no-finding` | `OBSERVED_RED` | `sha256:ea953cb9245f335c1cd2072547c6b5dd1dfe9e20a81dca51eca277d874d4e03a` |

## Measured cost and object recovery

P22 measured 133 graph commits and 16 disappeared actions with exactly 1 POC graph enumeration, 0 POC-owned per-action history walks, 10973 snapshot requests, 10970 snapshot-cache hits, and 135 actual Git processes.
The process count includes imported production `git rev-list --parents -n 1` queries; zero applies only to POC-owned per-action walks. The POC's single budget consistently caps every emitted work counter.
PCX-20a passes at its exact measured maximum 156 with limit 156; PCX-20b exits 2 with zero partial results when measured maximum 166 exceeds limit 165 by one.
R17-precharge-P22-budget charges before work and aborts on `measured work budget exceeded: object_reads=134>133` with exact bounded counters; the post-hoc reference vector is retained only as a damaged control.
The 64-parent boundary case measures 4 intrinsic graph commits and 8 parent edges against limit 7; parent-edge work is therefore metered even while graph commits remain below the limit.

PCX-19 is replay-bound by `sha256:824e0da528869df0b67e25e6e310937f4a13b4763821551c3dc85333aa760bbc`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.

## Reproducible audit

Use two fresh, empty scratch roots:

```sh
PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-v4-seed1 > /tmp/production-contract-r17-v4-seed1.jsonl
PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-v4-seed777 > /tmp/production-contract-r17-v4-seed777.jsonl
python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-v4-seed1.jsonl --compare /tmp/production-contract-r17-v4-seed777.jsonl
python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-v4-seed1.jsonl --damage-test
python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --repo /path/to/repo --old FULL_OID_O --new FULL_OID_N
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
unknown raw fields/cost rows, locale error drift, post-hoc budget work,
noncanonical ordering, BOM, CRLF, and missing newline.

## Nonclaims and integration gates

- This POC changes no production reconciler, restack adapter, workflow input, schema, task, or run record.
- A post-push check can only be advisory; prevention requires a pre-push or server-side production gate.
- Squash/deletion-only provenance is unsupported and blocks; only complete cherry-pick preserves authority.
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
