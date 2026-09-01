# Production-contract provenance POC

This file is generated in full by `audit_readme.py` from the closed
`evidence.json` manifest. Do not edit observations here by hand.

## Result

The real-Git self-test passed 167/167 scenarios, 4/4 executable aliases, and 34/34 damaged-mode controls.
It imports and calls the worktree's actual `queue_action_identity` and
`queue_deletion_problem`; it never invents an Action-ID or lifecycle verdict.

Canonical evidence artifact: `sha256:dce421f2a526ffdb023a24ab57ffee48b545ac3f5f7270b080e6dd2e84f71058`.
Canonical semantic stream: `sha256:c42611939d72baa05655d056286a1db08140b1c500a2a20cf9c09b5fe603d832`.
The raw JSONL stream is ephemeral and has no stored hash claim.
Evidence schemas v2 at commit `0b80c342feb310d73de6564aab2224a899f42486`, v3 at commit `7f4a1ffacd1cf8163f597daa186f801e9ce06a3a`, and v4 at commit `cce76a037f1584ff7d37048cb4411bdf0f5aa907` are superseded and burned by their later blockers; all histories are preserved, no identifier is reused, and this artifact closes `agentfold-production-contract-evidence/v5`.
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

## Bound r17 review outcomes

The exact reviewer DAG is clean and record-bound by `sha256:be692b8fc59196adb36ddfac766b993af4c976fe99036d65f6a9b8a447c7fda9`; its outside-C parent is neutral, its task patch replays exactly, and production deletion authority returns no problem.
R3-03 is blocking at the fixed N frontier with one invalid authority edge and is record-bound by `sha256:1d7907c17a585f3bd4e977306f9c1b8cc174a782fd05baf3b0852f35a64277af`.
The hidden-G attacker is clean at exit 0 and record-bound by `sha256:8cc2be5a5e20cff70b8c289eb1768ec4a741368752985496c1826b2c6d9b22ca`: F is the neutral boundary, G carries the same identity in a unique missing blob, and G ancestry remains unopened.
R6-02 is explicitly dispositioned clean and record-bound by `sha256:35dced8accb278be8b946b108bbbd648d2a7674f1369fa839774e61643dd0a4d` because its outside-C boundary is absent; the ambiguous ancestor behind it is not reopened.
All eight persisted-state attacker cases block in both parent orders: outside-C exact carriers retain multiplicity 1 or 2 as collisions, while valid and unauthorized absent C-descendant arms both remain deletion/reintroduction competitors.
The 64-parent outside-C octopus exits 2 transactionally and is record-bound by `sha256:82d53930ac2f952b77b729fc44a677441022bfde553e9934518d47c08d39877e`; no action, edge, support, or carry-proof result leaks past the exceeded parent-token budget.
The P22 pre-charge case stops exactly at `object_reads=134>133`, keeps Git processes at 4, freezes later counters, and is record-bound by `sha256:1c905027b91c4ccaa2064647f280764b358280c348c3e141b21b5a157025954d`; its post-hoc damage reproduces the prior 10,973-snapshot/24,736-cache-hit full run.
Seven runtime exact/+1 pairs bind streaming graph bytes/lines/tokens, object payloads, flattened trees, dynamic support traversal, and certificate serialization. Every +1 refusal exits 2 with zero partial results; graph reads peak at 256 bytes per chunk and publish nothing on refusal. P22 separately observes exactly 129 imported production parent queries and 135 Git processes.
Unreadable Git objects use the stable typed reason `missing-or-malformed-commit:b5fcd8d0260da07b741462af3e3e2b49b546d600`. Every Git child is forced to C locale and UTC; the stable C/French results are equal even though the independent ambient diagnostic streams differ.
Before any projection or digest, all 204 raw rows must match the static recursive key/list/type grammar catalog `sha256:2abd9d92f27159b8aca7f8c6604230b81e09e1d50d4b540e120795073f459206`; an unknown top-level or nested field exits 1.
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
| `docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py` | 158970 | `sha256:2757fc545155119dc2da23822282ad0c7927e206329f76bd7349914a890c4132` |
| `docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py` | 423987 | `sha256:13163c69dc39295c42c39ab5c65676e0be9e7bd83506c0c4918177a1db47f3ad` |
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
| `P1-direct-linear-valid` | `46109f507dba3eeb6191db457fc7848c415e8979` | `2819957948197a593fb1d0dc966e747c44db9ee5` | `029be55decf7d7f65826f86684cc8605d5d47b18` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:113c525167d1f67b000676b04b9accda7adbe902751288780253d3778e9d7f4f` |
| `P10-direct-invalid-parent` | `2ef716a2345dffac470956041b5245e20fbc8f98` | `1ac818d6b6ce87da87358e55015671ecf823dbb5` | `8f7e8c69c7ec6e4af250366114c90ecc24ce811d` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:9c6f3f7276de098c9a91a0774f48f612eff6f8058b24eb42f6d16898c508071c` |
| `P11-direct-three-parent-valid` | `78ad042cef55f824658b367d8599c5523b4e601d` | `b5726dd5f1e717518fae85cf820fc7b134db83fc` | `ad16f6d1f31e155a41a236d51a7a396e54dd5ea3` | 0 | `no-finding` | `valid` | `direct` | 3/0/1/0 | `PASS` | `sha256:1e511e74aa6e1c1c4fbe72303ca9d94da637b439645e7211ae19e6650d2f1236` |
| `P12-merge-supplier-valid` | `3a01d100e676a9a20f8dc545fed19be3419fb759` | `bc433c8ed8cda37d3813042f730b2f23d8e8d778` | `8dc6dbc10535cb058ee49c63a979d75966b7f248` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:c87d6bf2899d9485ec1723204cd1fecb66c1b4223c297e37b67b515cea0951ea` |
| `P13-merge-supplier-invalid` | `c9de2e4ee2e285093b2b1ae42b597989f5e2c267` | `898789857318c82970d920a105ee1a124474e155` | `9424f0b01381a9388d58b77c06efec9a59f0249f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:4b3012e3d430ee0e51a5edfbdc39ea61c72451d683dc0bc958ddc3c546520d11` |
| `P14-supplier-reintroduced` | `f340f1d750e747d6cf6a74dfac05146fd208f964` | `bf8487fe5085a4dc4b483f512c51ecd10cf7c253` | `14d300ed67dece9c599e5c0d096b708cc38bafa6` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:e31cdb0eda74652f540207280419630f7a71a31088119b8fab4a01d871b0b51e` |
| `P15-competing-suppliers` | `80b72ef13352057aa74028971730fbfb266b56f9` | `20a4f077a613c17b6e3f36d87f807bed9395d541` | `fe575f3eecc1f2b034bcbeb17a0021fce16bb82f` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/1/1/0 | `PASS` | `sha256:e27838bea5c4c07409df5567e0e0aca6fe020e20b9d1f8782ed1c40332084fc3` |
| `P16-PCX-08-invalid-supplier-claimed-carrier` | `b76e3dd3be1c4896d95f0ade31b63eada3ec7002` | `b756376fce02251f8036c1b1560d8c6c96dd0699` | `b23ca400da3968f74afc3b950ff4d4eb27307196` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:c722faa021f3a53689a502b0f1051404274efd6a99aec6d25923984fcdb37503` |
| `P17-post-event-reintroduction` | `ec84d0800c660f6379b21cfd721122fa06162999` | `ca7b04ae210ede6aaacf66c7c091cefbed16ee3d` | `258e858010ccd1e43716ab0269faa86ae08808a7` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:28f53db8af6d35b3653c65b881aa1a5f2235fce9686a46c5dc444a6a900a5e47` |
| `P18a-missing-tip` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `907f5d5221680a4ff7eccd647bcf26bcd5e9c4d5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:452c6c911ce3f5bbd9c976f3e1ce95974b4037ff09cc0586cd8d9a3df60eb763` |
| `P18b-noncommit-tip` | `None` | `90db16de6c0119c0c924c80d206b1e80bc3d2331` | `22be33aff3fad75ef91ab1e1cae2f2f8da2987d3` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:5fb19614890b32b91de3d31899a72258c9709478a46e5afe53794b8661565723` |
| `P18c-unrelated-tip` | `None` | `22628ae24f01e250d30bb4cf9c2a7832f217677e` | `e46c2df2b7bdeeedf09b55b74a3745ea6d7f5139` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:db7ccd830d8e8a31d76ba00b2097217943b6db883c18b3784c6df3612c8517fe` |
| `P18d-shallow-required-region` | `None` | `e68bb90fcc341adde9f4372caff5ecc6f9b1e340` | `4303d2f9587973759de42362a6c20b4b48170ab5` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:5bd21e2457225f569b8a983d67ffa1edb4b95d08bcb2974829918cf2c5a874af` |
| `P18e-missing-queue-blob` | `a668e725d1233ee7d5930c077268d222dd27c277` | `8d7223893ec84e193595fe975a53d36f893502cb` | `ec9f29e0560c60e66700496cee9ce14858aebb4d` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:d7377314afefb00b17f7bd954b590af08c6b0f391e3abebf18e1340c1d58b59a` |
| `P18f-missing-queue-tree` | `80ee9796305f288404f4aab5960193d8555c5e5a` | `61e6b7c9b52f0ea9ecb35c5bb8da8211aa7232d5` | `4f08ffcf2930d3d3a121b453b4b16a5b5f0bfa73` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:ca4809344747337dfa148136ec20d3cf1c7418cec8ac4ab601d71275a40791aa` |
| `P18g-multiple-merge-bases` | `None` | `c9a1e28be75d020fa3222bfb2a5b04649329083e` | `8e067847820ccf0c7ed10b39c330162e1b10d880` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:6055ad73a461f1c059de20654234ec78a2dd3a71bce4892cc74fd9b80f77e2cf` |
| `P19-production-identities` | `b9960dc72147b900fabc01a32e0057e6499059df` | `e702490de9ecf76f7a638b39d49006dc32229c4f` | `f10076f83de90580658d6d1599b0ee208b7fac87` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/6/0 | `PASS` | `sha256:428afbab328bb855d84993f59f9acd5386a4b3ca9193b1848b0879a83c507464` |
| `P2-direct-linear-invalid` | `70b791b1e8a9bd24f58737e93a443451f8f0ca11` | `ab15090d6bc10c375e03aa38f1ca6aa87d672a98` | `b00411d0cb294fe228cef9fa6744869d212bff1b` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:7c78e2f24e5d58df18adb0cebac231ce2f29b5ca7c968b052c2b80e4b70d7232` |
| `P20-lifecycle-types` | `dec0d432ddbb67c88d9833003f2939a596372ba5` | `d2e3aa02bfe5ddff10ea863ef5c6fe6557d54e36` | `822ee419b65be452b934eb592888a07ad6b74f9e` | 0 | `no-finding` | `valid` | `direct` | 4/0/9/0 | `PASS` | `sha256:18ecda6f97cfc05f3570d3ee4002a9840d2d1e85ecf6507309f9d3d2a4a748d9` |
| `P21-PCX-17c-squash-erasure` | `34448e62dde0da7a459c9f068a1929a11404bc60` | `67154541398ed536f17c169d282b151571b9031e` | `cdd5e979ba9eeb3e6caf97b05a182981178203bf` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:8a89f2233ce6f303bc8eb5ba6f8f745f076cc2968e1d0c1d5a04e883c16b5f10` |
| `P22-PCX-18-one-pass-many-actions` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 1 | `blocking-finding` | `invalid` | `direct` | 16/0/16/0 | `PASS` | `sha256:fdccdf1a7dacc8d20e1a61273d6ecd526d7674ddddd60caa377c7a597ba0152c` |
| `P3-genuine-old-loss` | `94db247b706f734bca553f86045fba8b98158a6c` | `5fa1eba2f8984af57952e6c083a0c455fc65d54c` | `5dffe2d077e79208c3e05ec0bfdd5de39600292e` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:a394cdb442bc4cb05f742e51afde08227a87b4835fc623d1e6f9162a7b6a88c4` |
| `P4-pre-C-identical-origins` | `cd13c47983b0624a824f5fc583f7de647b240504` | `03c76bf6661f670a705245479f406a1d3ba7b279` | `4d0b2462961d1fa5c64be4f73b533f7e165ad12f` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:de19365884b460f6ff14015b3424194ed4d681315b8e6afc38f9f165da9851be` |
| `P5-duplicate-at-C` | `bc6aa9f19ca8f454518b57c31d776631febc8cc1` | `7dfc74cea7ca951a4a21f28ef492e36f3fff17e6` | `21f67ef2f92ee4ee90ffd14a7e531e5f33f281cc` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:cd583ace17ec11aaadec270a736f46dd5adb88cba4d1f65568e73ab8b279ac19` |
| `P6a-old-delete-recreate` | `8039e1a89ee29be7b3a79d4fda7aa15a8653058f` | `900438d3fe4393f0ea2f87aa4d8dfc1e188f5919` | `6781a4eaee80c8ebde47bef04c33dcb47e91bc98` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/1/0 | `PASS` | `sha256:610c9951c8e6e504c79c656c5370636271b3a2eb41e66bf2d136dda09b86cd7e` |
| `P6b-candidate-delete-recreate` | `b5161adf1ba6eeb99b2181aa264598f707d19a95` | `bfb4c66d18c551b23a8580132543db2357ddb4f7` | `ca9f44b0f38c99dc7c70093046ead1b19f464389` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:22e2379272c214f5a3a6e10526102182579bfda4ef02b17876d8ca5770ce431c` |
| `P7-immutable-payload-change` | `43f673bf99a741dc37c6631d39bd5e9c037f7368` | `523cb1cb6e17b0e00b3bc3235618cfc0834d233f` | `03ae818dc35342d03432e7e25ca292808528ff3d` | 1 | `blocking-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:4a8f4704d65e74e01eef46863a6bd82038e9775a22271613dc9a1b77c340df44` |
| `P8-path-timing-move` | `1c34d6196d22c53ce54eac5b2cbed46be8432134` | `f9bdb1fd1af9e2d3b5b405594d2ef37ab55ac025` | `cef78e9bb54e4b4318172d0a2b6881da3a4b8971` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:d7bf72f1163d76651d2774f134958150348f161effd6afeeebb61e7afdcd24ea` |
| `P9-direct-two-parent-valid` | `074b437bb8582cabd4372ea380454368e8d81ab3` | `2380b58d4a6b687769359903f12100d69a543b2d` | `faa886162cc54c7c6544e33793a6e7f4342a90a0` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:aacc334d7ea5a6228d30cf3d8658daa8ccb8f09b33061fb6ca35c2c23e407b2c` |
| `PCX-01-neutral-parent` | `ee5d0eb6e70a978d7da73147f1faef9615f8624e` | `c4b177d1b0039326cd6592c90f7ce62e729ed3a8` | `acc6673079b122e2ae443cc91c4012c83344430d` | 0 | `no-finding` | `valid` | `direct` | 2/0/1/0 | `PASS` | `sha256:f2b79c250894179298d106a0b04c6cd54445fc96038a20d4e52d78c4f993858d` |
| `PCX-02-neutral-plus-invalid-carrier` | `b02a161fd6cd727aa2eb6bdf5ec43f5c5587e04d` | `78c77a131414cb7f196137896f9fd0080bb6552e` | `cf599de5003f9d108a979cb21f6d36c5c3785dee` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/1/0 | `PASS` | `sha256:f900c40a1c2f8304d81cb0a0e2fd56d07276a845526a10d4395d2304ebeddc9e` |
| `PCX-03-foreign-exact-identity` | `35f271b5d18393dac59002bb0c0c794d3589659b` | `36313b4892aaa243fc2d01fd05ebc8e7ac0145e3` | `f7fb0303c3061d22daf61cdeb03cd67496639432` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:ce2132fe47419f371ae8d8f16e19d63c7daaee0a23902f4ff293cdc6e75364f9` |
| `PCX-04-several-absent-one-supplier` | `32c7576c4c4aca96bdad8162078e9b2a28d6ae33` | `c4cf7124f59fc3edbec373d87507aba76143cfd6` | `cb06b9b4e0a3ae842774d0f888ebb5f1bca53881` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:4d8489436db7aacc43255b29d09d8b46faeec465511f492c9393533da459cdc8` |
| `PCX-05-competing-later-supplier` | `d297f8d7d5f3557c94f944194e6da99c1c092c81` | `39f138bf6fdf1db76fe12a652664dbdd3fcb33e6` | `5cc308cff656d4866cfd255d968e65ee17b58271` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:bfc0f4c1e061942c4829af82a2796947313e78cf363a82f944b63601dd1b853e` |
| `PCX-06-nested-supplier-over-direct` | `4fef7d2a64023363e13a455eddeac016838f651a` | `db0f6a1bdc43a8bccc8184e323867f7ed9aa04a0` | `2513214e5beaae7f3a289d4fae4018a00971c21c` | 0 | `no-finding` | `valid` | `supplier` | 2/2/1/4 | `PASS` | `sha256:3bb05e868888d5129785a4b45d32499de4f4f5427edb370173bba0bf7ee61cff` |
| `PCX-07-overqualified-propagation` | `e9920c69e87c8fadecea9dd6bfce80039a60619b` | `4eb27ecce806ae96e902a1c1cb1098fb7e8d7ba7` | `ea08bb6dd2a18266bfd6f436011c1cc610c4c8dd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:dc8ad8a4aa926ca8929046333f8a7e77a66c12ed328f66dce06e6a1af82dcdd0` |
| `PCX-09-recreated-claimed-bytes` | `41008171d1f9c6afd397a17c3e5567e040d881e2` | `9e38900a6d2f2e3b48457b5fe92fb55cf68ef1ed` | `626d32b7150a4185dddc568c91f3f096abd5f4e5` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/0 | `PASS` | `sha256:cec5d2ce622c7c2ccc5111d92e46d878f4210b19093298247435914c16ca12c7` |
| `PCX-10-transient-multiplicity` | `04b5c0356d29ee676d98d58fc639efaaa47278ea` | `cb082de1d3492e0b6e85918c5b1a4d2d600a110c` | `6dc48150188c026a1300d5fa19b065b1ad6a01aa` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:ad0aa13146c726490785b7c41eaaa86aa9a5d3cfa78f0f024323598179f15358` |
| `PCX-11-different-payload-same-path` | `9f7f5b9e5ce030055a6151bed80dfb6db1a94206` | `d45b35ca53a81320262faaeb7136fd081e8c1fef` | `78876b74b5d5c2cbdd3085a992a484c82280c769` | 1 | `blocking-finding` | `invalid` | `mixed` | 2/1/1/1 | `PASS` | `sha256:207de3faa60b3e0f7b21b56d9c9114d11f280373b6c88dc216e51c013cb24fba` |
| `PCX-12-timing-rename-supplier` | `c81cd1ddc4c58f7e6d5b9bd7f0a626f972651c79` | `e89ed03c9f3c8d338d6b4f03dfee7d6994ce400e` | `97ae732aab6ceb15bba65fdc775f3b4d5115a3a2` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:4ad89fc43fa34ad0c6e22c960b89cb19dedacc6be5bf278e177581141160be57` |
| `PCX-13-conflicting-human-response` | `58e15401aaba3e6f056f7dbaf6789c10d35ae553` | `1e790e17e8d0ba21ab1a7213d6e0e0fa2d12f047` | `14707f668aecd10bb531aa6fa0ec57700d26844b` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/3/1/1 | `PASS` | `sha256:a51244b95f3273145a4b485fce488f72182b1a4cbe843e85306eeb06c7a8c03b` |
| `PCX-14-valid-human-supplier` | `920e716ffd62703b03e21acd40423d34d60f165d` | `15ab9f04625ca7c4d6a8847bebaaa2b3169b5b69` | `36eaf058713764ea31d22a9cc74f800aaefbed1d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:67906cb8c3be17910b6587efe18c4916e2e2bd588939368dcbb7878ec31eca94` |
| `PCX-15-generated-retry-supplier` | `f5df7b0d8cf5622f4f786cbe936003b31c493199` | `d66c33a79421c1c87e7477e748fbb3513f8d0de5` | `5f8251bbbc8ce9fc2742bc88cbd70bf88615b05a` | 0 | `no-finding` | `valid` | `supplier` | 1/1/7/1 | `PASS` | `sha256:c1eceeaf84d6854e3811008e7816e9fece47c44597d61eea788277ae6f926d61` |
| `PCX-16-task-pickup-supplier` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:b16db54920f33753fbe926a7d30b5d6a0a51124ea81adfba278e88375ea57730` |
| `PCX-17-complete-cherry-pick` | `33db81167dcecdaa77e3c6e97ea6305b99d13346` | `8385f0c8c1094932a794ebb94b32b4d872806cd2` | `855eaa3b813900caaa0e523baa198491cb4bc47b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:2fb63df54a9ebe741df60f4b34b548a71935d8dce8a40443e503b051d5a4d6b1` |
| `PCX-17-deletion-only-cherry-pick` | `56008eecc6492c2c091a516834d675e283cc40bd` | `35b9163866f1c9cf6ab2435eeba3abfc0b9fd1fa` | `5da95440d2c9065d8b6f4506d2108a3f97bed539` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/1/0 | `PASS` | `sha256:d157e50d57ea719af313b235fd572c0c5ced5cec6519a5e89143955588522139` |
| `PCX-19-missing-claim-blob-recovery` | `759e2f27b42fa1f3bf68d8b436eed022ee8f1f5c` | `90aed2b3f8214a269d6421e6f4fe63ad3a61b091` | `dd34454f3204840ae81e2f273772c00488e681ea` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:d96c89904e5cc456360a60a76bc5b9c6a8b8b23ddb219e59460a0654e723fac9` |
| `PCX-20a-budget-below-limit` | `c957293f54b1b960b7b7f351087c77ac874eb253` | `ad76497bc5fa23076fff741b5d419a2ccd714637` | `ce775146b901f12bc2c05d22f06343da4d2c66d0` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:d7b0765fe2793c735d4b1c482da9846c58761122d38f9dc544651ce6a6601170` |
| `PCX-20b-budget-overflow` | `a018c90c3dbe1374339730ede5c7b76e21fee985` | `fb2043655802898f2561cc21431580a2609aef9c` | `06abdb0e773f19b6acc2ecf85d17e6c1770e7295` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:1c362cc7ec3cefe57beddc211c9145b698453b5da3f7336fad5e5f67d4913435` |
| `R10-direct-review-target-backtick-dotless-rejected` | `fe50d93da4de5ba4e924562e499d68c3dfe93118` | `1f06d5a4de78cd24f1f97cd617c10ab79bbf5487` | `ba4edb8f323adba9645e47c2536f2b621bed7855` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/2/0 | `PASS` | `sha256:7e8cbe21ea182063f34f103f88b74977e7d91374b12189df23f6512a7852527a` |
| `R10-supplier-review-revision-generic-placeholder-rejected` | `b13043f4864a963aee7af4e3e3a913313f9f7b19` | `9d96a7eecc2b34704ef588142e4b48111849f3a9` | `02371c1e8f0eebe4e567694cfe6677c8b872a7a8` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 1/1/2/0 | `PASS` | `sha256:078ddae5326fa42b38bf51f605c982dd2c2696ad6505f03fe9fc78c345934616` |
| `R13-direct-review-binding-identical` | `d6d18f0c56d196748c9a94adad1191e68722eb4a` | `7e0284f9a2354f44218502da59ca365cff918285` | `88dc201a2aae2ad0b8984b58fff19f45c78d7859` | 0 | `no-finding` | `valid` | `direct` | 2/0/4/0 | `PASS` | `sha256:204f2ac8f9e730d42ec758b628c42c014cee244e418aed34c7bb8b0c4c4b0205` |
| `R13-direct-review-binding-revision` | `f7d60f4ef43874a6e2045634265a8bb7968e07f4` | `e51c37206f2fa3f2d3a5ee9ff92aeaedc0aa431b` | `a4d2d52e8f40a5ba80cf350bd00db494c92c2eae` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:8322389488a52643a2d07d8ef89c18d44255b0e99c17b362d66571968e574036` |
| `R13-direct-review-binding-target` | `8454b9025487d126acbb3eb278584199e4d93bc2` | `75d9c282afe629e2fee58b878ffe93481926e719` | `74f92dd03eaf05333a9e7168644bbae38b7bb50f` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/3/0 | `PASS` | `sha256:6a420742caed8f263cb923fc074ab383ef7d7f784897641acd76dd0d2b8d2045` |
| `R13-direct-review-binding-terminal` | `32a00d09012a40145f9abdaedea2734348c68e5f` | `d784ca71704ac0bd18e1a70b45c18d1994353eb9` | `6677edfd8778a755904939d01b070af66f32bcaa` | 1 | `blocking-finding` | `invalid` | `direct` | 2/0/4/0 | `PASS` | `sha256:a5c249dba3c37b93e6b5084c56571c61d4d49818547a74af78d1ada97c34b30b` |
| `R13-persisted-claim-loss` | `5604e77ef241630dd284448a224de046d2caf460` | `49974b53d2f24076e2ad9eb183ee4e1511ad69e5` | `8702850ba2e7f56c29b16557c496adcaa627829b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:d395ccd259b9d1f741598154e7603d2b25d76231756ebfef4bccde877dc004e5` |
| `R13-persisted-pending-fill` | `6b710008b02a5c4b970a282ad2624b0384727292` | `5218487e636b8519c69f49d146acd9b7f8b25948` | `31a21eb1595bd8ebe46e55bb235d8d677edd6d58` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:fe95c704e6daabb42b5f5d75358d430787dd849e47380b9c2c0a9f09c0777726` |
| `R13-persisted-response-change` | `68dfa83702f8aa1a82181785ff40b9e0eb0f2958` | `af35b452b83aa6f8fee2d3dcf01a951a83cc0f19` | `464115d4c500dda036c5592c6c8f21fe9a959e15` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:1067b487ca8b2ca11fd981596fc0811dbcddbd447d6deebc9de085eaa29babdf` |
| `R13-persisted-response-removal` | `49d500f64d51f720b0decb65db3ad5163d4f72e4` | `69bbf3a1bec29fcf92121c581925bb092d1535ab` | `24126e616db515f5ee1d08d4f2da297b50e02f3a` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:701b0e35307efa105c0e04aef4fec0ed8ecb826e186e3e77b847c9a18a204576` |
| `R13-persisted-review-outcome-change` | `103fdd9bd623d90d09b2193e9272b3980c80906a` | `2c3f7acfeeb385de256074091a38c9953ce7f1f9` | `c8a8b37e924d1e18c54dd5bea09d07191b6b0be6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:ee03ed826cf4c384957867406856e14347cd4b921af20e639891a19b5aaa43ae` |
| `R13-persisted-review-revision-change` | `952a03b6b34abb531365195232acd149ec51e221` | `cc3bf0c5664ca51a1c1df82759aaa607efd30550` | `344c8d4e0333b14fb5b21550528242614812a55b` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:2f5e8d5ddb0c7d80bfdd2e0d5808997a1aebf5fa0f0a3a5aef2194bfd1414cb1` |
| `R13-persisted-review-target-change` | `de7f303a3f48d8d27eb65e7388d0f8dd934b4e96` | `2c37567f76cece330ee8c4997c96aa2bcd1764e0` | `4f6be0576ef37c17b25b0268542bf4003a7b56bb` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/7/0 | `PASS` | `sha256:f80d4668049ba98f223f145397d08ef7dfa8584cdf9bab8f7ec2a8fadc6fad1e` |
| `R13-persisted-same-state` | `0d4f188e038977d78c48829a48b12354ffc8aa32` | `a3edb26d4a2069954d0459dd9ea503cc27833f61` | `edee50f1fe44db9136335db0de7e27ad442f4eca` | 0 | `no-finding` | `none` | `none` | 0/0/3/0 | `PASS` | `sha256:00c46e1b84832307241be668fb2e3b42b6c0fedb558562c6d8ab18698993f7da` |
| `R13-persisted-terminal-fill` | `ba73b784939318c875041e869d49a08cfd88f440` | `b5ea69a78713ea41e8229125a90fa2718088c6f9` | `8250a2475da8b2c1a0dfffd5ecbe3e73fdd9b838` | 0 | `no-finding` | `none` | `none` | 0/0/6/0 | `PASS` | `sha256:134e92b46adeb0c290751e784a52ed48c2e9f048d1f0497daa65290f490716ef` |
| `R13-supplier-review-binding-identical` | `14976a93658e5bcfe9339368e77f82e77f31830d` | `ffc5d33bc00724fa377f13ce6ed824f6dc9fc02b` | `962821fb4d4faabe72c3b8e86823a5367aa3294f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:1f19ed0026093447c79cf5788226b48a63c30426655fed937ad94103dcfccf53` |
| `R13-supplier-review-binding-revision` | `52fe1848f1536143161e717bf436ee8c8b07df59` | `e7a884697094e9be1c876b78fc33d9e259d92149` | `8fd2e814f38bf145bd7c84d9e22a355056d40649` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:b124eae8f5cd7c9c0bb26de0b5a21227948c4050112379376d8c841904feea32` |
| `R13-supplier-review-binding-target` | `874d2e356033d133cd409bc9deb8e93198d0ec78` | `adf1ce7876b84e595992f5865f871b59ea892234` | `8c3e7d42c53baf018d30c895ecd64b799edb5d45` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:ff9c4b2322c1bab0948c4134fc132214e57a762b593a8ac187425c907238488c` |
| `R13-supplier-review-binding-terminal` | `e93ff6925d5008e9c95866628b410dda5b293e91` | `60538a926a9acd01f898ba0371ad5249c912f7fc` | `1031e6315881cdc99376df52bcddc86a4427e920` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/4/1 | `PASS` | `sha256:42477ad9721b7c140e14529d2102952aae21a9c52f0e9ffa01fe7548c28f290f` |
| `R14-direct-old-unanswered-carrier-same` | `c1a83b69fb7f04ea375aca7027b157dd9cc266ef` | `37d577cc2c265e8e7082bfd86dd156172db98c5c` | `ae63528ae1af829ced9c2f1b763cc6aeb8c054ec` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:36c329047d5901fdde1375dfc98b28e31191eb5c5ff379cc0aba7c362b7254f0` |
| `R14-direct-old-unanswered-carrier-target` | `0f221025b8224d465679596d3dfd44b6023371ca` | `d39ee31be16db2789928827c2e132a31e22b828f` | `9c07f77ec2836ec0f4222313e315b3ddc31c4ccd` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:6aa44676c54014da3c6b4664331480bfe8160b5cd9ec6020928e9d07642531dd` |
| `R14-persisted-delete-recreate` | `32c778b5ec16afe676bcd2ce898c89388b28ea0e` | `68f01125491f31f259d6cc636bc2f818c9529571` | `0d272d85cea3703f4fdc3aedfa7e821374de51ab` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:79ba4a8574f3989f49ba5b15e5f400028e9f8110d00beb0518d1b0629c9453a0` |
| `R14-persisted-hidden-bytes-low-similarity` | `e56fb481facaa08ac78bd0bcf41f2efdf4cf90db` | `d115e7063e3ffad24a495c9ffae5d70ffaf81928` | `a47b7307d654cb07612ccd7b04f1c32ab874c475` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/3/0 | `PASS` | `sha256:00506fea173bf7056e51ec757b35204acd8f428d793632ffdc6e7b2152b5517d` |
| `R14-persisted-intermediate-claim-regression` | `f98b12c5dbde687aeea147aa84dcf928b4bb53ea` | `a87ecb2becd5e7dab28fbdeb8b0a6f76a6a1cc2f` | `7b384e9882bd9f54be16ef63d18dd3bd1ebe736f` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:3f3c6fdcb39f2b7f4083ec55d4c7ef96fed0b6ceff48aa405b34eadc5b3b4854` |
| `R14-persisted-intermediate-review-regression` | `5fe7bc2ba01136ca7e91068de3c21394628d8616` | `ceeb45bc58cb8e6726517130e20fff034db993f3` | `b7e814f11797fcf8cc10f0a41b0dd8f0849718cc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/4/0 | `PASS` | `sha256:4b2001975ae23fd3dbe4e88f609d2d73004d92cae9db2aaa4e29e697d7624c87` |
| `R14-persisted-merge-carrier-conflict` | `00a09440e320c344f9840d7939f97b5a72654aa1` | `521e76aa7253b7dc1214c2bbdca5c788a601e21d` | `e2f3eacb8b4a86f383f8a76be26dac7e4966edad` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/8/0 | `PASS` | `sha256:dd2a7f0be9369f202083c97cecea2f28965ee2e04dd74c534e5784f46b1dadd2` |
| `R14-persisted-merge-carrier-pending` | `01b493c655badddcf6641e8a7d21d3594a0cb5c3` | `74442946b6639f57e7167838a13cc286f39d3519` | `ca8939b406b7b2323fd08b044625639f5e80cb6b` | 0 | `no-finding` | `none` | `none` | 0/0/8/0 | `PASS` | `sha256:e31bbc98a6adebe6044112b93c01fe3598f79cb77c97337e081abb2df7173019` |
| `R14-persisted-valid-first-response-low-similarity` | `b14ffe7afbd09ecdcf3fcdecbf99fcd42e5f9e59` | `dafb69000967fde6234bce7999767113def81c5c` | `690a6c7b5a5425bcd8a3abfa90b75c77ecbde966` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:ce62ae4b2c0e46ee78be6d07d9cd556ca666645f54c4a57377102d58d0c40367` |
| `R14-persisted-valid-review-retraction` | `58a66e99ff34cdfa5e2bd150d68d5d6121b0cd71` | `03f6cd5ee859d98e6110b2554606ba655ea9b66c` | `75f7c3689154b3ecf8e5c67d467e338ab24a47cb` | 0 | `no-finding` | `none` | `none` | 0/0/5/0 | `PASS` | `sha256:e8929cca91ef3905818a242b8c9c2ec0f79a8c94675821af0d520bf1b90a6f7f` |
| `R14-supplier-old-answered-carrier-pending` | `7f104616c4fd6c3d1f15d7467a7e0da9e164f6e7` | `6f1dba05d9dca3e3776da3c7005a83807190ae74` | `0662f0827db1ad2e39f59626dd8d87f316b73421` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:c40b1693c891544ccb6fbae4beaa7fb5aaac32a167df87789df25b388f8d6a29` |
| `R14-supplier-old-answered-carrier-revision` | `9121f39bba512fa9fd762c3d07c93d1c11d5bc42` | `6d9c8b1bfed15a512d68db494efb71a2d0577f33` | `0b0243e67b4d4635716eb2113f81419da982ba3c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:0ca86ce66be1e1da447e31156f05372863283f7685fd7fc9fecea5c7c21d8671` |
| `R14-supplier-old-answered-carrier-same` | `d87b23dffb37c46a64f0f37fd10db886fc100532` | `a6ff10d32896ec2d87dad1696b24e07cc73ead65` | `9f1c795a2f4fd1450d4d524f3f7adbdf0c496c52` | 0 | `no-finding` | `valid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:de0906efdb0dc559dd367879884af9f846d8c7e7b186c16743e2440aec0a5e60` |
| `R14-supplier-old-answered-carrier-target` | `3436d4ba5dc72f9837516e4155c0c9da9f44dd90` | `8a2de576d9304a51988bfbd943749129f828f882` | `b952d0de4952cb720e3056abe78c7ad8ee52d50f` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/3/1 | `PASS` | `sha256:e2782639ea2c963d686ca19bbe5882fe20d101d274495a92a298f74153d51853` |
| `R14-supplier-old-unanswered-carrier-same` | `186d0ffca8ab62c6de1677780cb4153eced4fe53` | `b6e124010b1f74882864bdc3dc1fbd289fd5305c` | `e9e33f66742ae613b738497753ffb4957610b85e` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:bd7356eb346515b2871a1c65ad569540b0a34cf9ecb5577bcf040950ef3fd551` |
| `R14-supplier-old-unanswered-carrier-target` | `9109e916c44dbeaa2bfe0e3b5497e9d98ef3e9a3` | `a09f2f2ed771008847609d177c72e0b1f62d8084` | `0c38b44e67a3ad27238aed8c8a667837aa7fc444` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:852c67d9ff97ff1985c763efa6b6eec121cc855d165f644ce2d798a90b1a032e` |
| `R15-old-continuous-preserved` | `9972c0979b118b85b5c9d80a811679b41840910b` | `6e29170cbd7791baf6f74923a50387a9359979e1` | `316e8cd76611658ad9587c73e54cbfb6f3c9f379` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:b595d89eba9dabaf5c52e927bc6d2798d674bca4608bfc33eca92850af8d6a0a` |
| `R15-old-hidden-bytes-restore` | `600ae7430233c349c25bbe4ab0f9f8fb55e7c92e` | `023e0594e4a6d2f3403635decbac7a9d90ec06f0` | `20096f8d2a62bfe7e6990d90b91135ef249879c6` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:2abff8c5d0292806d105e73a6c66f1e0b687335ba3633bbabf7fcc46d85e00bd` |
| `R15-old-human-binding-restore` | `ed9337d8d288a493c724a71081e4db71972e2e08` | `1d8e4411979ce8ea8dc5697180f8d17be74f1be6` | `fce1db3bfd0846d5af6dcc96b362a52baec376bc` | 1 | `blocking-finding` | `invalid` | `none` | 0/0/5/0 | `PASS` | `sha256:b3e8893d9a986da5cbd5578eb801b2c7de29414c1fdac003ce62f430d14d6cb9` |
| `R15-old-invalid-delete-recreate` | `f26bbc4c9cdbbf3ad4b2cd18c03b6ae60ef51fc4` | `4fa6ffd247960df785d1e957e4cd902382e8f437` | `b3e62e6398e4ee29f708d4eca4bd98a4b699b015` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:682c36b0558b2f792bf912897bbd0bd113f76f1d4213eb9606a2f2e7aeedba77` |
| `R15-old-valid-delete-recreate` | `d949c6358b9809dbc4c19c55ccc30fab511c7413` | `5f6066d0642c29fbb3414c54445b8ac08d5c99ff` | `de690fe09e6d88d499db4b3ebccdb7dbfb8b5617` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/3/0 | `PASS` | `sha256:1c1fe1a072569050760ac7a9f465f7d87c1afaab494448dee7376b91cd9ab000` |
| `R16-earlier-landed-evidence-reversal` | `e731036f833027f6e32ae9d17deec1f1b3114412` | `f8186fb2af1ae0e23196a4ac0095582433643daa` | `aee42abb66d8ba55343efe6f741c32987563844e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:2b5d1b7fb9635451057e86ff429982eac723da430e2a71fdcf9ef1da5135ad62` |
| `R16-pickup-evolution-0-backlog` | `41945ab0488983f425986ec3f815e50e974be318` | `ddee8c3c0a47baed150ff41c81fe3dd3578991e0` | `50ddfeceda267269a756eff178f2e6f2dcde7af7` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:d54833e5c5d8b47ce0d91166568821ad1949eb9120ff843679089c28a7661f5c` |
| `R16-pickup-evolution-2-blocked` | `e7e14e5b5790e4682f7609b3ca494fc9fd1e9218` | `97de8555908750bc8bfe4f195811124e6639b33e` | `48a4d96e210ac69ff036bff2bd154d6e496e6a05` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:ffad74d158f0c0d95768017273dbdb6f8f992c0860a3b5f02e1234a45bff5a78` |
| `R16-pickup-evolution-3-in-review` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `66aae1f38225afbdde6a9af1c261223a7505c461` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:1321f9da9ce3a8ee5b1dc5571925d52d8c855a40591c4fbd9d7af687c417c310` |
| `R16-pickup-evolution-3-in-review-drop-artifact` | `7be6b185c13cdf698e8617ca833d5916efff192d` | `0732fd851a8ac5e656c0ce67c7e1dc8a32b5278c` | `04e4cdf6f4c210ea0a27c59ed86f1d01627024c2` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:a552ca94239c4229c9d4f6a8ca4495883aba72c693ff7aa71be34eda9bd8b22b` |
| `R16-pickup-evolution-4-done` | `28b720891ddfd4c7291ada824d3d2196cf4a560b` | `da9ebd1326c500e7d2c008fdb80f43be5cf13ff9` | `a8a309c333926cb8144f022c4356736917e5907f` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:742212cf98bccafaff4794c5803ae323e02c77f26b3dba5ed7460bfe5ef29941` |
| `R16-support-adoption-drift` | `a831384530c69ef834d1d997c25ffb996cfa4bbc` | `be001bade214359024c192e8b06d79229261a4c7` | `ce12604ff0140d20fdda463a6140634b62f35bed` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:c89b9e4c6725d8509412f4468b7d594d9fb793a68bc4f6e388cc01060421210a` |
| `R16-support-forward` | `8617eee2ba78f3977a9e7e0329159f725633daac` | `4690d1f06ca2513358bd47fc88e8dfdee3a15d71` | `9e15331efb2e68a1762d26fed1df245232a40f2d` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:f2fd315f6a89438b5d2fb7ed26f8117f29da7322dc491a4b98e4022993e23384` |
| `R16-support-invalid-source` | `b5e005e8c934907d6548515f752cba73b79797da` | `8cc15771a0e42ecaa2b04166fdd57589976cb454` | `2c6d7881177ab459839ec9bf195c035cb8faeddf` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/0 | `PASS` | `sha256:0511322034898833d8c5fe42e5b47739d118c2f9cd0be5c497d9aa4e43f0a6fa` |
| `R16-support-nested-drop` | `168496fb2f34612a9276eab0151b2b83bf1edd88` | `13967af6be58e3cbea6ee31c6f54f6c39b246626` | `95622f34bd3618ecc561897fe977861d26c1a4c8` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:819c118eb49ee4d0b57aca6ab5af56acb7257860072e6eb42fa20deaecd54c4a` |
| `R16-support-permutation-diamond` | `f3d302490bc5c12be93f9392e00071fef0822ffa` | `b82141d042aba0552175891be684c7dd7eccc579` | `04baf28178f9b9b80761050e875ca2f993b4792a` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:ffcedb86b1b51534fda89b1e8e2970faba7defb0810a0927ad29b62816dd4005` |
| `R16-support-reverse-drop` | `96de2cbd6d1afee44ffb6a03dcd12ea53ade9d70` | `fdd6aafdea7adfb0255ef9c1cf12168a23685d00` | `c24c0ed6dd25307717255c297879a96ee8c40f7c` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:d9159d0629dce6cb70766364ff1fbf3ab41b2dccead3a4f9cc2b60c893ef6d96` |
| `R16-support-reverse-preserved` | `f3b2fb92a748ae2b38142cc01b1542b5302dcdfb` | `1f62604717746cdf35f2f13b4efe8789e9a73118` | `e38824daf72c0fbb9c049b6662fea36ad262f8cd` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:7987b2f6330dafa5cd7057e1eac4050b08b99ad9cf7097bc96659eb46f9f5c53` |
| `R16-support-source-evolution` | `ffc5faa56114e44e8497228192ca4daacd278179` | `91474815e967e29084c0d18638907fe068dfd87e` | `2614fbbda55f0fd12af32872df6361a290c8b12b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:9e0b5809cfca5ac57d7b76f77414b4e2639aeb9ef8bf6e3f35ea5c2a1ae410be` |
| `R17-carry-absent-arm` | `a3cbba79bd52df83262715df9652f338ed3b7f5f` | `a6a471c1129d9af27fd96ae12ec4bee2d2f326e5` | `a5e82a41d59db68164823c9fb5a58359bcf1ec49` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:edf6a1aeaa9d636fd0c3d947d91a21a526a5f8df62b6d3f488f5f5994e59e78d` |
| `R17-carry-compatible` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `ba001beceb64bc88110a724ad6da2ee3498c8c90` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:6b0cdcedd7323cbe6b0a79e34260e807b3d0e47f63c996809be4ddf0521bfcc7` |
| `R17-carry-compatible-reversed` | `b308ae8f1fb6e8424e8224bb75bdc758fa9d36dc` | `c707f7968f51ae5520c8ac31f1379ee289cb7946` | `b4684c533ad9bfcb5918dfff653a30eda3e53d66` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:e57e76702fd293d0f40ee811027af4073f53990077dbb59f71eeaec1934666ff` |
| `R17-carry-incompatible` | `bb60281870ffd7279e90c3fdb11326b1759a64f3` | `20417860a7a086bb0f2a171db425ac97f43c5269` | `d9fb9b1c536e2ef615e7ed902c697ebe84f27793` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:cbf377b4530b77c2ee02f53f9315472dda0166b90a9eb23d7fdde41e20b13d2d` |
| `R17-carry-outside-duplicate` | `f793332edc8b2cbee979959d560c177365267cb6` | `723fbd86c6180058e653f7b8241401c172a7dd1a` | `0449217881a784a7c4bb1ef1e6b8ed1a5fb781f5` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:f98847fbb08da00afe37e231302a3395b3bbdd92afb62636b8bf97793095a2c3` |
| `R17-carry-outside-single` | `446a8c37bb272b847634d4f51ed29d6bdf9db1a5` | `5f2c5d5e1489b14b10120ff854459b2e71944fd1` | `60e0f415b3d0d3c59e0a7980c4efbc9868e1d576` | 1 | `blocking-finding` | `ambiguous` | `direct` | 1/0/1/0 | `PASS` | `sha256:b39363ef59f268bec37017d3420fb5af468d6beb9b27a1d83d8c229f10b05577` |
| `R17-dynamic-support-traversal-exact` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 0 | `no-finding` | `valid` | `supplier` | 1/1/1/1 | `PASS` | `sha256:7367068286bdab704371996ff343cb5dc8cb1e583dd1152415477adc231ead1b` |
| `R17-dynamic-support-traversal-plus-one-refused` | `ab3f73cb72be2389d566fb06118bc841facffc86` | `be2b18037fbd9785128edb1af215d459b7be8b9c` | `fcf1b089a8cf59a77e3d1740409e12b12815f7fc` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:105adc59f4cf3b2a5e778bc6d7f06e0cf94d708c64538d4cced9908cb787d521` |
| `R17-flat-tree-peak-exact` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:09576d2ad617c1b036c282a6349b5142593539db2ad1a3bb089365a44229e9e7` |
| `R17-flat-tree-peak-plus-one-refused` | `6d04db14269fb22a677d1741dfb0c5910a6bf579` | `d0e77b3c5a49fbee0ee1fb3f24811f7945fb217c` | `346b534af244d3ecd65f6e30977a62c856428895` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:9375a4e7d4aa7657fc19485af80441a7fca5238481df3e7233e9f1a0a951d0e0` |
| `R17-graph-line-peak-bytes-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:2adb819542e201753c4d3d6b1e6ba6c5208a82eb2d6c8a4d86dd8e5c2cbb0984` |
| `R17-graph-line-peak-bytes-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:3d05432849c055d930669287b74d270b97c07cd82c053b4925b7f215be3c57b0` |
| `R17-graph-output-bytes-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:9368895fcaee42f5fc4b21d6a62acd728d3b1bf7b3a05887b0c28e141a75e74c` |
| `R17-graph-output-bytes-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:17d7061ad0bb818feecda941135e691fd3595ec534d35304acbbf26614ccdb78` |
| `R17-graph-parent-tokens-exact` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 0 | `no-finding` | `none` | `none` | 0/0/4/0 | `PASS` | `sha256:7120bcdee3ba6056697db4d27e4c443d7b1fdc1d71ec7d0f72e7f4a7c6ee800a` |
| `R17-graph-parent-tokens-plus-one-refused` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:d1751c4569eb3b849a293819380da1ed579fd49bdf9615752f6fe4ee5ddbccb4` |
| `R17-object-payload-peak-exact` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:96a0510c67026d3c9f629f6252733914fe8a1a3929f92804834cd76daa8748d5` |
| `R17-object-payload-peak-plus-one-refused` | `53f6c80de7203e881aa896be54074d09376c8449` | `2720af33febd032adf7c2c42efb51e374bc6ccef` | `e72179ccae7a6dde471759898b14bfdf936825de` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:d3550a47fe4b6bb949730e0e3458c09b66d7539e9cf7cbd7613f3135814d71f6` |
| `R17-outside-C-neutral-parent-valid-restack` | `d3d362d37559714b75cea48eef7f44a4547f4e2f` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:be692b8fc59196adb36ddfac766b993af4c976fe99036d65f6a9b8a447c7fda9` |
| `R17-persisted-outside-duplicate` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `481c03e8e4afa0b3dfe37df8a244bc53823811f4` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:777adb545e10cb0b42cf07026a85216f0b3c91e8370a4d5541b63a0e024d2ee2` |
| `R17-persisted-outside-duplicate-reversed` | `a634b186452a74ebe41c0fb8cea97e576a5e1c56` | `1a6848089233430bc2a23baea686c5c84369f135` | `d74cfd74fc6648eb13bb52ad192ee13b4146155e` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:9759115c66a9d1a20139597c0ac298fe49cadd49123dd990878e65f208ff3149` |
| `R17-persisted-outside-single` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `32a88f55e904d1892fd473b62f3d30a4bf2faf24` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:dce5a511b7e6a158af32696f9e8b337ae16157903b6fe06c4286e84e4e6150d2` |
| `R17-persisted-outside-single-reversed` | `f87a6d73b61852cb9487b0f1ebf6febd0e72c35c` | `6062aa2350b2611b66c70feda73ec2f005a969ab` | `4a231bb4516e6185d7ade17f5e5cb8aaafcc0613` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:e678219af74c2c7d7eaba8961d951d83673d89b377b1766df7fee683c1ad8fa3` |
| `R17-persisted-unauthorized-absent-arm` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `c1e4c835d0ece38b56490f0beffef88494aef8a2` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:1998b8bf7f9f42914ff2047bbb2f270d56daf9147897221fd06439f506b7523f` |
| `R17-persisted-unauthorized-absent-arm-reversed` | `91dcb08637806181435c1f391f3e2db35fefeef0` | `cfe02192e79b2fb37f7278844446c987345c369e` | `6a55c69bf40bfcd9abe33bababdae51ad111eeca` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:ed4522b63fdff89154a6abef379cc4f0f3121c46dad4c6ac074eb033472821e0` |
| `R17-persisted-valid-absent-arm` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `501cc5ef6cb38be7a83d37b9f47d26cf2acebdec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:812ea58669e65e4cef37d2fa85d4911f2086c5875c37c6fff9995be800f3c8a3` |
| `R17-persisted-valid-absent-arm-reversed` | `be75a50c3ceea41059aa954effb358348455b9d7` | `1f0d7b897a4a09e5c8273ddcd4fb25ef7a69f656` | `12f08cf66b77738190f29720044039af1fcc10ec` | 1 | `blocking-finding` | `ambiguous` | `none` | 0/0/2/0 | `PASS` | `sha256:aa1672c5e5faa49e73eec640c0a2d35fb47c02015bc7d4d0b8125ed2ba969ade` |
| `R17-precharge-P22-budget` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:1c905027b91c4ccaa2064647f280764b358280c348c3e141b21b5a157025954d` |
| `R17-support-serialized-exact` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:fce77f35c1a380fd014be4e1c715a27555f73e88abc6b1cbb7b5f3595a29fb7e` |
| `R17-support-serialized-plus-one-refused` | `28fdb47beb543c35636b1518739e9dc7e76a6d34` | `ebb6305bc27fef1e7c09fde6d8d493adc46f2eeb` | `ec0b23cf1c14ab42fe281007e8db80fed18771d4` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:c19bb3431e871481638fa0dfa5f6f8e0800d53eb45ffaa410bc77394e9d48289` |
| `R17-unreadable-outside-C-ancestor-stays-unopened` | `33f9ad5aab42435cc63bf59f2b38294666dce16f` | `9490a5097490e4a7e38d8b76dded28f7d370d22d` | `508323236873cfbdf04254316378e7748f4a3959` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:8cc2be5a5e20cff70b8c289eb1768ec4a741368752985496c1826b2c6d9b22ca` |
| `R17-unreadable-outside-C-boundary` | `None` | `42b178114baa052d7ee7ffb1c8814a8d916b7911` | `19fbc24144d0298bca24978ad439e9deb1c7fd87` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:75d9ec143ff20a360ecf50bebc8c64eb42617d0413191c9564dea92787c96003` |
| `R17-wide-outside-C-boundary-budget` | `c2080829aec4e8ae17a17e29fd823b80e74d99d0` | `a2659af5918566489ae4ea08c86925a0b276ad90` | `0f42c9312d8a41d51c1e17d3776a6ec5a8e657e2` | 2 | `blocking-finding` | `ambiguous` | `none` | 0/0/0/0 | `PASS` | `sha256:82d53930ac2f952b77b729fc44a677441022bfde553e9934518d47c08d39877e` |
| `R3-01-two-invalid-causal-sources` | `73373ac5106e43d8643b5b616268d77a5ca1d264` | `8f89d0fc4c063c0bbabb284434f74bcf244fb5d3` | `8ed846d60715d845a5e19ab6b299ce853a592614` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:1316e3c100fa34edeb65d768ff50f98e5d60f88b81555730fb84c77256139768` |
| `R3-02-invalid-valid-causal-competition` | `16722b83a642e40f2157c752a07adffddfaa709d` | `35e767d91f32b96f8f8308b431b5c6a0b35be23f` | `ff42531aadc6ffa000560bc56d995993ffa8e62c` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/2/1/1 | `PASS` | `sha256:f13187b7605287abcf9d8ec081c26f4a078a8f3df39142c91467feec1a8f4ded` |
| `R3-03-valid-supplier-plus-invalid-parent-at-N-blocks` | `1e44d8c3cba4bdd091bd1ae218a504f5b7d938fd` | `ba83bd926d133cee0384ae4b8fd577de5d14e835` | `433bb31a23f524c2a61cd0084e0a1ecda0af8c3c` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:1d7907c17a585f3bd4e977306f9c1b8cc174a782fd05baf3b0852f35a64277af` |
| `R4-01-same-root-valid-diamond` | `4e831314d34c2897a072cca5b58303d8fd0e7ddd` | `2ae7f29324bd8d6b29c1f7640602fe7ec9193b1e` | `a7bbf4b40d0a3322205e3d8407eee73b9b11ccc9` | 0 | `no-finding` | `valid` | `supplier` | 1/3/1/3 | `PASS` | `sha256:0deec28d24ff2f69ef4c0c3e678c6e9115651490c2db4b37e45254fe46ac6261` |
| `R4-02-distinct-valid-root-diamond` | `10965dc1169826888c7d66e2389f9f90787c0064` | `286e35141edc20fad35f8b0d4aeb4930c403d038` | `37a75ca4c96e8966c19fa18afe6b6f9b1e4c10d7` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/2 | `PASS` | `sha256:94f890dc40b6a54efb8ab355c1b17c1b52907fe7c0700e19807297dfc44e2cb7` |
| `R4-03-equal-root-plus-invalid-diamond` | `90e37b9adc7b3b428f2963282519639354bd2b56` | `de44aaea6c73d11ca46c2255f39f9b9a3d10d36e` | `3c9778ae10bc7a945bb59ad802db12bd6803ea64` | 1 | `blocking-finding` | `ambiguous` | `supplier` | 2/3/1/1 | `PASS` | `sha256:80cdaa8d8c56c9b1fd1d7baf41e76aa7d4a043f39f14e9421b9a4dc16d892e32` |
| `R5-01-invalid-redelete-after-supplier-reintroduction` | `1e5dad973b3278ca8c12f3dd74f72250eaaf9f09` | `c63664276a141f3f60f61c9d404de201e6f8cf16` | `d40a531fd9a0dacb986f9259ac6f94ec0d248faa` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:417f1a491b45c0b50f2d82ff29c77892cdbcd547e8db00118eb4eb48a6a0b8f4` |
| `R5-02-valid-redelete-after-supplier-reintroduction` | `79b338b3ef54382a0ec95e87a7ba962b1ec7c20a` | `9c8b1418effb6889d14466e278a7987b7e7cfbc3` | `fb0bff9778f436aed2a46f887eafb84e1c74ea5f` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/1/1/1 | `PASS` | `sha256:169fefb00d304457d5db705665aff12e1ec5e70651890257526dca26eaf91786` |
| `R6-01-valid-plus-invalid-all-absent` | `566072d117ff7a1e4309949f6a885bd8e26d65d2` | `5dc5378fdc316aa30dce282d0388a438d755b067` | `abe68c6bcfb89b4194e7d9f3ace08a58e985a450` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:f5e3761f985971e8358b075e3ea34ae96ccbd16ea50a00854463dc06eacf461f` |
| `R6-02-valid-plus-ambiguous-all-absent` | `f61617485ff0160e37de559fe752c56ff3bcb5f7` | `10a37a2bc559519d6d84f70850b0a78445c3d5ec` | `4ab46009954bb98c5f22629274722667dc21ca37` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:35dced8accb278be8b946b108bbbd648d2a7674f1369fa839774e61643dd0a4d` |
| `R6-03-two-invalid-all-absent` | `f5141f92b29541282cf1ec520470e8c604aeaa6b` | `eb354df4fb54776834a9dff53f51f496a2bb338f` | `8f769727f1c641bd2587115f2fbcda5fdda816d1` | 1 | `blocking-finding` | `ambiguous` | `ambiguous` | 2/0/1/0 | `PASS` | `sha256:399af367ff9ef1d771615b63c3425968ea32056e0d9ef42eeccef444194336c9` |
| `R6-04-same-valid-root-all-absent-wrappers` | `c4ad2cb41bff8803f0f3d5b81ea0cfd785c9aa59` | `c3b9fb54026383a350146fb2f25243c9e8c7cb01` | `7bf74330f432155c3c39eedbfc81fa72bface489` | 0 | `no-finding` | `valid` | `supplier` | 1/2/1/2 | `PASS` | `sha256:44a5f3f8dd1def1df6822d81daeb4b00f46b3143455f0a7d4d1477f4d01db3d4` |
| `R8-direct-human-response-conflict` | `92c80d9c65c7be349d0a6c663a6a2ea9c3c2397c` | `1dc4f0dc77aae1eefaef0bb443ec187ff1efb23d` | `cb29049ff107a9a11a4ec7babbdee21819518dd6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/2/0 | `PASS` | `sha256:cff40bb0006f3b68b64c2732aba2e02487e8b4df3da97807613a9dc2b8120e27` |
| `R8-direct-human-response-identical` | `2b79814b0bce6f1556c0b2724ade9d7bbb4bf939` | `b3879039d6d7168e89b3046e6e60e056460907c1` | `2c2289035cfc91c73564f6a97b326ebca02be132` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:e57bbfffa0608a8740be9841236c0ced216605bf0bd5c30a98d1b48fc790f6a1` |
| `R8-review-binding-divergent` | `9b4889771f49a83cd02600a2de58fc5e6e8b8259` | `e3c594800cfe94f4f23c58060ae4ab31f50c078c` | `dc70864ec5e13a399d4966356b9803075681a0e6` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:bf0d7b8a17c5be6a4d69bd97918a00c1a1162201523033ced68a64962578f61e` |
| `R8-review-binding-identical` | `45b7550dbdc799efed73af109da57c6906d428a0` | `a3f97a3b22945e663eb10180bde5de3b7bf790fa` | `b2dbe65f89982fb586b0fb5349454d80c7c53310` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:b8174abb93308ee02ca3e150cb7a5e6f9cec755cc59cd50e57112eff9d00c7e1` |
| `R8-review-binding-terminal-conflict` | `cd64224f775f16bc2099816c594012a9592f8536` | `356f3f37cdffaf8f6c568a158a32c478f55a0e13` | `2c972bd770f520e2a62aaf928c8731a4a5b9b7ee` | 1 | `blocking-finding` | `invalid` | `direct` | 1/0/3/0 | `PASS` | `sha256:43b2e21cfd0f41281f04f510c7487ed04d0c1d8e4bc8f843581a7ed32ef0b9d2` |
| `R8-supplier-human-response-conflict` | `255e448f3c735fefdcee3c07071c3d6bb6abb312` | `27927fe11bdeee043660e700c81e8cb3853c56bf` | `1fb9fc40da2d44e839830611cc20d0aee23c560e` | 1 | `blocking-finding` | `invalid` | `supplier` | 1/1/2/0 | `PASS` | `sha256:56f814dac7bb9e82f526a265175cfa2ea2bd65fcab68b5e97a50592c3324d22f` |
| `R8-supplier-human-response-identical` | `800658fac71a8c7fbc2d257bde57964cc96dcef9` | `f33b095abbf3c3e3225e0fbfc663b0a7f52d312b` | `e94946d2990fe3c67bc61676f66f90fab1b7a26a` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:eddd0172b555f8a997f24834e7baafe8df70f7a7c94e1b7faeca3ed5100a9ef9` |
| `R9-direct-review-revision-pending-fill` | `00ce8c4f203a14c87a9955fece2645744ab2222a` | `6da769be2398ce26c45d3dba7845e0d6bcdc07fc` | `f5e8ec93ded434c47e27f345c1e38da95297f7be` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:cff69eac1885165dc62a2e0ab302f5b4841dca07baf340bc0167c34ea8ffa784` |
| `R9-direct-review-target-pending-fill` | `7a613196cb22eb565e0f85194f7e2b8251a1484e` | `4263506464cbffb20b5f550fa142ebd391669ca1` | `8f2d8945b9ee6ffc11a714efefad9f8c1d708410` | 0 | `no-finding` | `valid` | `direct` | 1/0/2/0 | `PASS` | `sha256:866a20d1e694e09217cd1589f375b616318f61f0e06ca24a1594ab19ec8107b7` |
| `R9-supplier-review-revision-pending-fill` | `eef4459d2337688dab6f6681415a6f5c57cca6b8` | `9bec712c0e2453a881aa8fd36ff89d8887e07942` | `26d16dfc1e390a11c674ccbcf8281d212a19544b` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:6e8123ceda934521bd91ecce344d9ffd6f2c9e872cdf1dd6abb40136df0ece49` |
| `R9-supplier-review-target-pending-fill` | `8cc94bd588fa82e6bf7fa0258a7f4a3b96453d75` | `648b5b5515d697600fab0a9aa087a1f63bddad3d` | `64affcee2fe535a4f21aa80e72df2131349dda62` | 0 | `no-finding` | `valid` | `supplier` | 1/1/2/1 | `PASS` | `sha256:c7c5e4a11c4441f0b914cf10bb85853b1364815af44b2a0d5034531e76ba8f63` |
| `W0-fast-forward-return` | `b614e3dd70da804a078bde5088d38ac9de511846` | `b614e3dd70da804a078bde5088d38ac9de511846` | `2fce4585d497e94f48f6807dd3cd9fd7b432b264` | 0 | `no-finding` | `none` | `none` | 0/0/0/0 | `PASS` | `sha256:7693de173d8361aa1d99e91ba61e95db0ecfd320e1c9d25c4eaeebef262c9c06` |
| `W1-pre-PR-push-exact-endpoints` | `2fb10d8c39b965cafdeb5e496e351ab258f75960` | `365339838cdfc9d6579ac21478fec9b776742c27` | `1cc139111382dea68cae0208e17354f6f75c5bad` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:6885198d18b90cd9ddd0e437701c7a30ff9952037e9222e6c6b1d9084d0a0383` |
| `W2-base-advance-retarget-invariant` | `1e1e59bc5493dd584372acb3da94233d867bbed0` | `a6363187edd2b2ae4cac6d24e0bc6d4d9adfb836` | `1c48ddcef1c77fdc65609d2a077ef3cb40396393` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:3ace98a69beb762066127f31a7298dec582f2cccd0971beaa40c8f4c214e5cbc` |
| `W3-multiple-PR-API-zero-calls` | `7f7a2d473d3bb95a7879b5ff2c26195a4b730e1e` | `b32b24f6a4b08d17c073bfdc2355521efbcbcf58` | `56238e170cdc0358979e2cbefc7af6cbf89b279b` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:d525b9c832d3f2c1dd2d6cb3023bd144694580f93998fe08228897aed6ecd938` |
| `W4-stale-rerun-exact-inputs` | `b5c4bd355d0c9fb9279be13d67268628652addc1` | `842d19ca481aa76dfcdcf096af4c550e826d9569` | `6046485394ff351e5cbecdd5c5503c44a821af8c` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:106f26dcb25776af49f5a7f4e0ef410917f800ff3eed2a8ddbc68954e7f7ea8f` |
| `W5-missing-O-coverage-unavailable` | `None` | `ffffffffffffffffffffffffffffffffffffffff` | `4923d6cd62a6ccd426bd569cc06323a11f775bc4` | 2 | `unreadable` | `unreadable` | `none` | 0/0/0/0 | `PASS` | `sha256:866fb67a4bcff6c12eb1e573b0bdac471d734f5a142d3b2f1d42e2775e5abaf7` |
| `W6-created-deleted-zero-endpoints` | `fb590466fe387afa4f25743982c78e281f34f36e` | `2df4b3d62821abe8ea3f482b931ed91d256d24a9` | `1f3aa42d8428e4dd3b8b98220355e0bf883c318d` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:65f835989867fad2e50aff1574fb7ded9758a482aac87c6e84fa4a09804df8fc` |
| `W7-PR-synchronize-top-level-endpoints` | `99342d9672d3f50559eccba1fc16eb8710b7b476` | `55bd0ff6ffe71dcae7a1afbfa440b021bf972dec` | `5a612247b54e551764fbf258e44893a0f5c40dde` | 0 | `no-finding` | `valid` | `direct` | 1/0/1/0 | `PASS` | `sha256:814efdc073e8650ef9b4b0ee4222f3c09b8632ea2d09dfc98da448166b036f41` |

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
| `posthoc-budget-accounting` | `df53962cd25ebbb38830454e977caf65252ce009` | `8533fdc2d343b168d822c683379bfabbb49c0d28` | `466dae5f060fd0aa74cf71db38fa694686afd7ae` | `blocking-finding` | `blocking-finding` | `OBSERVED_RED` | `sha256:7c686cded6769487eab91eb2bea89ffd454343d02e2362019b97de54a495dd13` |
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
| `stream-malformed-truncated-final-line` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `0000000000000000000000000000000000000000` | `unreadable` | `partial-graph` | `OBSERVED_RED` | `sha256:3af7784f6bb2d2e42293bb8fa0f2acb38ae8b023d1fff8f3b9adf5bc00911bf2` |
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
The closed runtime matrix additionally admits/refuses exact/+1 values for total graph bytes, peak graph-line bytes, a 1,000,000-byte object, 1,004 flattened paths, 12 dynamic support paths, and 2,920 serialized certificate bytes.

PCX-19 is replay-bound by `sha256:d96c89904e5cc456360a60a76bc5b9c6a8b8b23ddb219e59460a0654e723fac9`. One ObjectDatabase reader observes a missing blob without caching the miss, the object is restored, the same reader/process succeeds, and a third read hits its positive cache.

## Reproducible audit

Use two fresh, empty scratch roots:

```sh
PYTHONHASHSEED=1 LC_ALL=C LANG=C TZ=UTC PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-v5-seed1 > /tmp/production-contract-r17-v5-seed1.jsonl
PYTHONHASHSEED=777 LC_ALL=fr_FR.UTF-8 LANG=fr_FR.UTF-8 TZ=America/Los_Angeles PYTHONPYCACHEPREFIX=/tmp/production-contract-poc-pycache python3 docs/designs/restack-queue-provenance/pocs/production-contract/prototype.py --self-test --fixtures-dir /tmp/production-contract-r17-v5-seed777 > /tmp/production-contract-r17-v5-seed777.jsonl
python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-v5-seed1.jsonl --compare /tmp/production-contract-r17-v5-seed777.jsonl
python3 docs/designs/restack-queue-provenance/pocs/production-contract/audit_readme.py --stream /tmp/production-contract-r17-v5-seed1.jsonl --damage-test
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
unknown raw fields/cost rows, locale error drift, post-hoc or unmetered runtime work,
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
